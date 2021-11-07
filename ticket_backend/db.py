from databases import Database
from sqlalchemy import create_engine, MetaData, engine
from datetime import datetime
from typing import Optional

from sqlalchemy.sql.schema import ForeignKey
from pydantic import BaseModel
import ormar



DATABASE_URL = "sqlite:///db.sqlite"

database  = Database(DATABASE_URL)
metadata = MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

class Account(ormar.Model):
    class Meta(BaseMeta):
        tablename = "accounts"
        # constraints = [ormar.IndexColumns(["id","public_id"])]
    id: int = ormar.Integer(primary_key=True)
    created_at: datetime = ormar.DateTime(default=datetime.utcnow)
    public_id: str = ormar.String(max_length=100,unique=True)
    name: Optional[str] = ormar.String(max_length=100,nullable=True)
    email: Optional[str] = ormar.String(max_length=100,nullable=True)
    role: str = ormar.String(max_length=20)

class AccountOut(BaseModel):
    public_id: str
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]


class Ticket(ormar.Model):
    class Meta(BaseMeta):
        tablename = "tickets"
    id: int = ormar.Integer(primary_key=True)
    created_at: datetime = ormar.DateTime(default=datetime.utcnow)
    public_id: str = ormar.String(max_length=100,unique=True)
    description: str = ormar.String(max_length=255)
    assign: Account = ormar.ForeignKey(Account,name="account_id")
    completed: bool = ormar.Boolean(default=False)
class TicketIn(BaseModel):
    description: str

class TicketOut(BaseModel):
    public_id: str
    description: str 
    completed: bool
    assign: Optional[AccountOut] 
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)


