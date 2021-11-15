from security import create_access_token, verify_password,hash_password,decode_access_token,JWTBearer
from fastapi import APIRouter,Depends,status,HTTPException
from db import Account,AccountIn, AccountOut,Role,AccountWithToken,Login,ChangeRole
from ulid import ULID
from typing import Optional


router = APIRouter()

async def get_role():
    adminrole = await Role.objects.get_or_none(title='admin')
    if adminrole is None:
        await Role.objects.create(title='employee')
        adminrole = await Role.objects.create(title='admin')
        return adminrole
    else:
        return await Role.objects.get_or_none(title='employee')

async def get_current_account(
    token: str = Depends(JWTBearer())
) -> Account:
    cred_exception= HTTPException(status_code = status.HTTP_403_FORBIDDEN,detail="Credentials are not vaalid")
    payload = decode_access_token(token)
    if payload is None:
        raise cred_exception
    public_id: str = payload.get("sub")
    if public_id is None:
        raise cred_exception
    account = await Account.objects.get_or_none(public_id=public_id)
    if account is None:
        raise cred_exception
    await account.role.load()
    return account

@router.get("/{public_id}", response_model=Optional[AccountOut])
async def get_account(public_id: str):
    account =  await Account.objects.prefetch_related("role").get_or_none(public_id=public_id)
    return account

@router.get("/self/", response_model=Optional[AccountOut])
async def get_account(current_account: Account = Depends(get_current_account)):
    return current_account


@router.post("/", response_model=AccountOut)
async def create_account(
    account_in: AccountIn):
    values = dict(account_in)
    print(values)
    values['hashed_password'] = hash_password(values['password'])
    values.pop('password',None)
    values['public_id']=str(ULID())
    account = Account(**values)
    role = await get_role()  
    account.role = role
    return await account.save()

@router.put("/", response_model=AccountOut)
async def update_account(
    public_id: str,
    account_in: AccountIn,
    current_account: Account = Depends(get_current_account)
    ):
    account= await Account.objects.get_or_none(public_id=public_id)
    
    if ((current_account.role.title=="admin")|(current_account==account)):
        values = dict(account_in)
        print(values)
        if ('password' in values.keys()) & (values['password'] is not None):
            print('pass')
            print(values['password'])
            values['hashed_password'] = hash_password(values['password'])
        values.pop('password',None)
        await account.update(**values)
        await account.role.load()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="No rights for update this")
    return account

@router.put("/change_role/", response_model=AccountOut)
async def change_role(
    change_role: ChangeRole,
    current_account: Account = Depends(get_current_account)
    ):
    account= await Account.objects.prefetch_related("role").get_or_none(public_id=change_role.public_id)
    role = await Role.objects.get_or_none(title=change_role.role_title)
    if (current_account.role.title=="admin")&(role is not None)&(account is not None):
        await account.update(role=role)
    return account


@router.post("/login/",response_model=  AccountWithToken)
async def login(login: Login)->AccountWithToken:
    account = await Account.objects.prefetch_related("role").get_or_none(email=login.email)
    if account is None or not verify_password(login.password, account.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    accountwtoken = AccountWithToken(
        public_id=account.public_id,
        name=account.name,
        email=account.email,
        role=account.role.title,
        token=create_access_token({"sub": account.public_id,"role":account.role.title}),
        url=login.url
    )
    return accountwtoken