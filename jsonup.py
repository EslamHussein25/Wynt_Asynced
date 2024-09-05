import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def json_load(cv_data):
    try:
        return await json.loads(cv_data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        logger.error(f"Error decoding JSON: {e}")
        return None