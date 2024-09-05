import aioboto3
from botocore.exceptions import ClientError
import logging
import json
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_s3_object(s3_client, bucket, key):
    if not key.endswith("resume.pdf"):
        logger.info(f"Skipping file {key} as it is not 'resume.pdf'")
        return None, None

    try:
        metadata_response = await s3_client.head_object(Bucket=bucket, Key=key)
        metadata = metadata_response.get('Metadata', {})
        logger.info(f"Metadata for {key}: {metadata}")
        
        response = await s3_client.get_object(Bucket=bucket, Key=key)
        file_content = await response['Body'].read()
        return file_content, metadata
    except ClientError as e:
        logger.error(f"Error getting S3 object: {str(e)}")
        raise

async def send_and_save_to_s3(cv_data, scorecandidate_json, extracted_text, resumeid, region='us-east-1'):
    bucket_name = 'wynt'
    root_path = f'resumes/{resumeid}/'

    cv_data_json = await asyncio.to_thread(json.dumps, cv_data)
    score_data_c_json = await asyncio.to_thread(json.dumps, scorecandidate_json)
    cv_data_file_name = 'cv_data.json'
    score_c_data_file_name = 'scorecandidate.json'
    extracted_text_file_name = 'extracted_text.txt'

    s3_url = f'http://{bucket_name}.s3-{region}.amazonaws.com/{root_path}'

    session = aioboto3.Session()
    
    try:
        async with session.client('s3', region_name=region) as s3_client:
            # Async S3 upload for all objects
            await s3_client.put_object(
                Bucket=bucket_name,
                Key=f'{root_path}{cv_data_file_name}',
                Body=cv_data_json,
                ContentType='application/json'
            )

            await s3_client.put_object(
                Bucket=bucket_name,
                Key=f'{root_path}{score_c_data_file_name}',
                Body=score_data_c_json,
                ContentType='application/json'
            )

            await s3_client.put_object(
                Bucket=bucket_name,
                Key=f'{root_path}{extracted_text_file_name}',
                Body=extracted_text,
                ContentType='text/plain'
            )

            logger.info(f'Files successfully uploaded to {s3_url} in {bucket_name}')
    except ClientError as e:
        logger.error(f'Failed to upload files to S3: {e}')
        raise
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        raise

