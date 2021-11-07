from security import create_access_token, verify_password,hash_password,decode_access_token,JWTBearer
from fastapi import APIRouter,Depends,status,HTTPException
from db import Account,Ticket,TicketIn,TicketOut
from ulid import ULID
from typing import Optional,List
from random import randint
from pykafka import KafkaClient
import time
from aiokafka import AIOKafkaConsumer
import asyncio
import json

router = APIRouter()

async def get_current_account(
    token: str = Depends(JWTBearer())
) -> Account:
    cred_exception= HTTPException(status_code = status.HTTP_403_FORBIDDEN,detail="Credentials are not vaalid")
    payload = decode_access_token(token)
    if payload is None:
        raise cred_exception
    public_id: str = payload.get("sub")
    role: str = payload.get("role")
    if public_id is None:
        raise cred_exception
    account = await Account.objects.get_or_none(public_id=public_id)
    if account is None:
        # raise cred_exception
        # create account
        account = await Account.objects.create(public_id=public_id,role=role)
    return account

async def get_random_employee():
    employees = await Account.objects.filter(role='employee').all()
    emp_number = randint(0,len(employees)-1)
    return employees[emp_number]

@router.post("/", response_model=TicketOut)
async def create_ticket(
    ticket_in: TicketIn,
    current_account: Account = Depends(get_current_account)
    ):
    values=dict(ticket_in)
    values['public_id']=str(ULID())
    ticket = await Ticket.objects.create(**values)
    await ticket.update(assign= await get_random_employee())
    return ticket

@router.get("/kafka/")
async def kafka_test():
    consumer = AIOKafkaConsumer("Account_created","Account_updated", bootstrap_servers='localhost:29092',
        group_id="ticket_service")
    await consumer.start()
    print("consumer started")
    try:
        async for msg in consumer:
            # print("consumed: ", msg.topic, msg.partition, msg.offset,
            #     msg.key, msg.value, msg.timestamp)
            msg_obj = json.loads(msg.value.decode("utf-8"))
            print(msg_obj)
            print(msg_obj.keys())
            account = await Account.objects.get_or_none(public_id=msg_obj['public_id'])
            if account is None:
                await Account.objects.create(**msg_obj)
            else:
                await account.upsert(**msg_obj)
            
            
    finally:
        await consumer.stop()
    print("final")
    return

@router.get("/complete/{public_id}",response_model=TicketOut)
async def make_complete(public_id:str,current_account: Account = Depends(get_current_account)):
    ticket = await Ticket.objects.select_related("assign").get_or_none(public_id=public_id,assign=current_account,completed=False)
    if ticket is not None:
        await ticket.update(completed=True)
    return ticket

@router.get("/my/",response_model=List[TicketOut])
async def my_tickets(current_account: Account = Depends(get_current_account)):
    tickets = await Ticket.objects.select_related("assign").filter(assign=current_account,completed=False).all()
    return tickets

@router.get("/uncompleted/",response_model=List[TicketOut])
async def view_uncompleted(current_account: Account = Depends(get_current_account)):
    if current_account.role == "admin":
        return await Ticket.objects.select_related("assign").filter(completed=False).all()
    else:
        return []

@router.get("/shuffle/",response_model=List[TicketOut])
async def shuffle(current_account: Account = Depends(get_current_account)):
    if current_account.role == "admin": # todo managers
        tickets =  await Ticket.objects.select_related("assign").filter(completed=False).all()
        for ticket in tickets:
            await ticket.update(assign = await get_random_employee())
        return tickets
    else:
        return []
