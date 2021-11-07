import databases
from fastapi import FastAPI
import uvicorn
from db import database
from fastapi.middleware.cors import CORSMiddleware
import endpoints

app = FastAPI(title="Auth Popug Inc.")

origins = [
    "http://localhost:3000"
    
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix='/auth',tags=["auth"]) 

app.on_event("startup")
async def startup():
    await database.connect()

## for sqlite db is not nessesary
# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()


if __name__ == "__main__":
    uvicorn.run('main:app',port=8000,host='0.0.0.0',reload=True)