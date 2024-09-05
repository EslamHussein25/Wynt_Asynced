import os
from sqlgres import Jobs_DB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#add her the async session to make sute the session which we will opend is async not sync session 
async def get_job_data(session: AsyncSession, jobid: int):
    try:
        logger.info(f"Fetching job data for job ID: {jobid}")
        query = select(Jobs_DB).filter(Jobs_DB.id == jobid)
        result = await session.execute(query)
        job = result.scalars().first()
        
        if job:
            logger.info(f"Job data retrieved successfully for job ID: {jobid}")
        else:
            logger.warning(f"No job found with job ID: {jobid}")

        return job
    except Exception as e:
        logger.error(f"Error fetching job data for job ID {jobid}: {e}")
        return None
