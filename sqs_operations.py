import aioboto3
import aioboto3.session
from botocore.exceptions import ClientError
import logging
import os
import asyncio
import json

from extracttext import extract_text_from_pdf
from s3_operations import get_s3_object
from cvprocess import cvprocess
from cloudwatch_operations import log_to_cloudwatch_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEUE_wynt_resumes = os.getenv('QUEUE_wynt_resumes')

if not QUEUE_wynt_resumes:
    logger.error("Environment variable QUEUE_wynt_resumes is not set.")
    exit(1)

LOG_STREAM_NAME = 'sqs_processing_stream'

async def process_message(sqs, message):
    try:
        messagea = message['Body']
        logger.debug(f"Raw message body: {messagea}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Started processing message ID: {messagea}.")

        body = await asyncio.to_thread(json.loads, message['Body'])
        receipt_handle = message['ReceiptHandle']
        bucket = body['detail']['bucket']['name']
        key = body['detail']['object']['key']

        logger.info(f"Processing file: s3://{bucket}/{key}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Processing file: s3://{bucket}/{key}")

        if key.endswith('resume.pdf'):
            file_content, metadata = await get_s3_object(bucket, key)
            extracted_text = await extract_text_from_pdf(file_content)
            logger.info(f"Extracted text from {key}: {extracted_text[:100]}...")
            await cvprocess(metadata, extracted_text)
        elif key.endswith('cv_data.json'):
            logger.info(f"Processing cv_data.json file: {key}")
        elif key.endswith('score.json'):
            logger.info(f"Processing score.json file: {key}")
        elif key.endswith('extracted_text.txt'):
            logger.info(f"Processing extracted_text.txt file: {key}")

        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Finished processing message ID: {messagea} successfully.")

        # Delete the message from the queue
        await sqs.delete_message(
            QueueUrl=QUEUE_wynt_resumes,
            ReceiptHandle=receipt_handle
        )
        logger.info(f"Deleted message from queue: {receipt_handle}")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for message ID: {messagea}: {str(e)}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"JSON error occurred while processing message ID: {messagea}.")
    except ClientError as e:
        logger.error(f"Error processing message ID: {messagea}: {str(e)}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Client error occurred while processing message ID: {messagea}.")
    except Exception as e:
        logger.error(f"Unexpected error during processing message ID: {messagea}: {str(e)}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Unexpected error occurred while processing message ID: {messagea}.")

async def process_sqs_messages():
    session = aioboto3.Session()  # Create an async session
    async with session.client('sqs') as sqs:
        while True:
            try:
                logger.info("Starting to poll SQS for messages.")
                response = await sqs.receive_message(
                    QueueUrl=QUEUE_wynt_resumes,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=1
                )

                messages = response.get('Messages', [])

                if not messages:
                    logger.info("No messages in queue. Waiting 5 seconds...")
                    await asyncio.sleep(1)
                    continue

                # Process all messages concurrently
                await asyncio.gather(*[process_message(sqs, message) for message in messages])

            except Exception as e:
                logger.error(f"Error in SQS processing loop: {str(e)}")
                await log_to_cloudwatch_logs(LOG_STREAM_NAME, "Error in the SQS processing loop.")
                await asyncio.sleep(1)

