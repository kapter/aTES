from databases import Database
from sqlalchemy import create_engine, MetaData, engine
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import ormar
from signals import Producer


DATABASE_URL = "sqlite:///db.sqlite"

database  = Database(DATABASE_URL)
metadata = MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Role(ormar.Model):
    class Meta(BaseMeta):
        tablename = "roles"
        # constraints = [ormar.IndexColumns(["id"])]
    id: int = ormar.Integer(primary_key=True)
    created_at: datetime = ormar.DateTime(default=datetime.utcnow)
    title: str = ormar.String(max_length=100)

class Account(ormar.Model):
    class Meta(BaseMeta):
        tablename = "accounts"
        # constraints = [ormar.IndexColumns(["id","public_id"])]
    id: int = ormar.Integer(primary_key=True)
    created_at: datetime = ormar.DateTime(default=datetime.utcnow)
    public_id: str = ormar.String(max_length=100,unique=True)
    email: str = ormar.String(max_length=100,unique=True)
    name: Optional[str]  = ormar.String(max_length=100,nullable=True)
    role: Role = ormar.ForeignKey(Role, name="role_id")
    hashed_password: Optional[str] = ormar.String(max_length=100,nullable=True)
    role_type: Optional[str]

class AccountIn(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]

class RoleOut(BaseModel):
    title: str
class AccountOut(BaseModel):
    name: Optional[str]
    email: str
    public_id: str
    role: RoleOut
class AccountWithToken(BaseModel):
    name: Optional[str]
    email: str
    public_id: str
    role: str
    token: str
    url:Optional[str]

class Login(BaseModel):
    email:str
    password:str
    url:Optional[str]

class ChangeRole(BaseModel):
    public_id: str
    role_title: str
    
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

Account.Meta.signals.post_save.connect(Producer.post_save)
Account.Meta.signals.post_update.connect(Producer.post_update)