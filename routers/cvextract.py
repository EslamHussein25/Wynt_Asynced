from fastapi import APIRouter
import asyncio
from sqs_operations import process_sqs_messages

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    asyncio.create_task(process_sqs_messages())

@router.get("/")
async def root():
    return {"message": "SQS processing service is running"}