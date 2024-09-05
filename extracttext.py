import fitz
from fastapi import HTTPException
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_text_from_pdf(file_content: bytes):
    try:
        # Run the blocking fitz operation in a separate thread
        text = await asyncio.to_thread(extract_text_sync, file_content)
        logger.info(f"extract_text_from_pdf: {text}")
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF file")

def extract_text_sync(file_content: bytes):
    text = ""
    with fitz.open(stream=file_content, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text
