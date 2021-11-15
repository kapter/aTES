from passlib.context import CryptContext
from jose import jwt
from datetime import datetime,timedelta
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import Request,HTTPException,status
from fastapi.security import HTTPBearer
from jose.exceptions import ExpiredSignatureError

ACCESS_TOKEN_EXPIRE_MINUTES = 5
SECRET_KEY = ""
ALGORITHM = 'HS256'

pwd_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password,hash)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp":datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    print(to_encode)
    return jwt.encode(to_encode,SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        encoded_jwt = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
    except jwt.JWSError:
        return None
    except jwt.JWTClaimsError as error:
        print (str(error))
        pass
        return None
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature has expired")
    return encoded_jwt

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer,self).__call__(request)
        exp = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid auth token")
        if credentials:
            token =decode_access_token(credentials.credentials)
            if token is None:
                raise exp
            return credentials.credentials
        else: 
            raise exp