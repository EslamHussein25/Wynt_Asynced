import aioboto3
import logging
import time
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use aioboto3 to create an asynchronous CloudWatch Logs client
LOG_GROUP_NAME = 'Wynt-process-AI'

async def ensure_log_stream(LOG_STREAM_NAME):
    # create new var for logs names cloudwatch_logs
    async with aioboto3.client('logs') as cloudwatch_logs:
        try:
            # Create log group if it doesn't exist
            response = await cloudwatch_logs.describe_log_groups(logGroupNamePrefix=LOG_GROUP_NAME)
            #if this group doesn't exist create new one 
            if not any(group['logGroupName'] == LOG_GROUP_NAME for group in response['logGroups']):
                await cloudwatch_logs.create_log_group(logGroupName=LOG_GROUP_NAME)

            # Create log stream if it doesn't exist
            response = await cloudwatch_logs.describe_log_streams(logGroupName=LOG_GROUP_NAME, logStreamNamePrefix=LOG_STREAM_NAME)
            if not any(stream['logStreamName'] == LOG_STREAM_NAME for stream in response['logStreams']):
                await cloudwatch_logs.create_log_stream(logGroupName=LOG_GROUP_NAME, logStreamName=LOG_STREAM_NAME)

        except Exception as e:
            logger.error(f"Failed to ensure log stream: {str(e)}")


async def log_to_cloudwatch_logs(LOG_STREAM_NAME, message):
    async with aioboto3.client('logs') as cloudwatch_logs:
        try:
            await ensure_log_stream(LOG_STREAM_NAME)

            response = await cloudwatch_logs.describe_log_streams(logGroupName=LOG_GROUP_NAME, logStreamNamePrefix=LOG_STREAM_NAME)
            log_stream = next((stream for stream in response['logStreams'] if stream['logStreamName'] == LOG_STREAM_NAME), None)
            sequence_token = log_stream.get('uploadSequenceToken', None)

            log_event = {
                'logGroupName': LOG_GROUP_NAME,
                'logStreamName': LOG_STREAM_NAME,
                'logEvents': [
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': message
                    }
                ]
            }

            if sequence_token:
                log_event['sequenceToken'] = sequence_token

            await cloudwatch_logs.put_log_events(**log_event)
            logger.info(f"Logged to CloudWatch Logs: {message}")

        except Exception as e:
            logger.error(f"Failed to log to CloudWatch Logs: {str(e)}")




# Example usage
async def main():
    await log_to_cloudwatch_logs('example-log-stream', 'This is a test message.')

# Run the example
asyncio.run(main())