
from aiokafka import AIOKafkaProducer
import asyncio
import json




class Producer:
    def __init__(self):
        self.event_type = "ALBUM_INSTANCE"

    async def post_save(sender, instance, **kwargs):
        producer = AIOKafkaProducer(bootstrap_servers='localhost:29092')
        await producer.start()
        try:
            account = {
                'public_id':instance.public_id,
                'email':instance.email,
                'name':instance.name,
                'role':instance.role.title,
            }
            await producer.send_and_wait("Account_created", json.dumps(account).encode("utf-8"))
        finally:
            await producer.stop()

    async def post_update(sender, instance, **kwargs):
        producer = AIOKafkaProducer(bootstrap_servers='localhost:29092')
        await producer.start()
        try:
            account = {
                'public_id':instance.public_id,
                'email':instance.email,
                'name':instance.name,
                'role':instance.role.title,
            }
            await producer.send_and_wait("Account_updated", json.dumps(account).encode("utf-8"))
        finally:
            await producer.stop()