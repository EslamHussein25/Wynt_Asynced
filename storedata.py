from sqlgres import (
    Base, talents_DB, talent_skills_DB, talent_projects_DB, talent_evaluation_DB, 
    talent_education_DB, talent_certifications_DB, talent_job_details_DB, 
    talent_achievements_DB, title_categories_DB, talent_pools_DB, candidates_DB, Jobs_DB
)

from utils import profiletype
from eventbridge_operations import send_eventbridge_event
from cloudwatch_operations import log_to_cloudwatch_logs

import json
import re
import logging

from sqlalchemy.future import select
from sqlalchemy import delete, func, update, and_
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_STREAM_NAME = 'Store_Data'

async def store_cv_data(session, cv_data, scorecandidate_json,score_candidate,resumeid, tenantId, profile_type, title_categories, jobid=None, candidate_id=None):
    try:
        profile_id = await handle_talent_profile(session, cv_data, resumeid, tenantId, profiletype.Talent, title_categories)
        await process_education(session, cv_data, profile_id)
        await process_job_details(session, cv_data, profile_id)
        await process_skills(session, cv_data, profile_id)
        await process_projects(session, cv_data, profile_id)
        await process_achievements(session, cv_data, profile_id)
        await process_certifications(session, cv_data, profile_id)
        await process_evaluation_p(session,cv_data,profile_id)
        await update_talent_pools(session, tenantId)
        
        if profile_type == profiletype.Candidate:
            profile_id = await create_candidate_record(session, cv_data, resumeid, tenantId, profile_type, title_categories)
            await process_education(session, cv_data, profile_id)
            await process_job_details(session, cv_data, profile_id)
            await process_skills(session, cv_data, profile_id)
            await process_projects(session, cv_data, profile_id)
            await process_achievements(session, cv_data, profile_id)
            await process_certifications(session, cv_data, profile_id)
            await process_evaluation_c(session, cv_data, scorecandidate_json, score_candidate, profile_id)
            await update_job_and_candidate(session, jobid, tenantId, candidate_id, profile_id)
        
        return True
    except Exception as e:
        print(f"Error storing CV data: {e}")
        logger.error(f"Error storing CV data: {e}")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"Error storing CV data: {e}")
        await session.rollback()
        return False

async def handle_talent_profile(session, cv_data, resumeid, tenantId, profile_type, title_categories):
    age = await parse_age(cv_data.get('Age'))
    experience = await parse_experience(cv_data.get('experience'))
    title_category_id = await get_title_category_id(session, title_categories)

    result = await session.execute(
        select(talents_DB).filter(
            and_(
                talents_DB.email == cv_data.get('Email'),
                talents_DB.type == profile_type.Talent,
                talents_DB.tenantId == tenantId
            )
        )
    )
    existing_talent = result.scalars().first()

    if existing_talent:
        await update_existing_talent(existing_talent, cv_data, resumeid, title_category_id, age, experience)
        profile_id = existing_talent.id
    else:
        profile_id = await create_new_talent(session, cv_data, resumeid, tenantId, profile_type, title_category_id, age, experience)

    await session.commit()
    logger.info(f"profile_id {profile_id} successfully.")
    await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"profile_id {profile_id} successfully.")
    return profile_id

async def create_new_talent(session, cv_data, resumeid, tenantId, profile_type, title_category_id, age, experience):
    new_talent = talents_DB(
        tenantId=tenantId,
        resumeId=resumeid,
        titleCategoryId=title_category_id,
        name=cv_data.get('Name'),
        age=age,
        phone=cv_data.get('Phone'),
        email=cv_data.get('Email'),
        address=cv_data.get('address')[0].get('alladdress') if cv_data.get('address') else None,
        country=cv_data.get('address')[0].get('country') if cv_data.get('address') else None,
        city=cv_data.get('address')[0].get('city') if cv_data.get('address') else None,
        title=cv_data.get('title'),
        summary=cv_data.get('summary'),
        type=profile_type.value,
        yearsOfExperience=experience
    )
    session.add(new_talent)
    await session.flush()
    logger.info(f"create_new_talent successfully.")
    await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"create_new_talent successfully.")
    return new_talent.id

async def update_existing_talent(talent, cv_data, resumeid, title_category_id, age, experience):
    talent.resumeId = resumeid
    talent.titleCategoryId = title_category_id
    talent.name = cv_data.get('Name')
    talent.age = age
    talent.phone = cv_data.get('Phone')
    talent.address = cv_data.get('address')[0].get('alladdress') if cv_data.get('address') else None
    talent.country = cv_data.get('address')[0].get('country') if cv_data.get('address') else None
    talent.city = cv_data.get('address')[0].get('city') if cv_data.get('address') else None
    talent.title = cv_data.get('title')
    talent.summary = cv_data.get('summary')
    talent.socialLinks = cv_data.get('socialLinks')
    talent.yearsOfExperience = experience
    logger.info(f"update successfully.")
    await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"update successfully.")

async def create_candidate_record(session, cv_data, resumeid, tenantId, profile_type, title_categories):
    # Always create a new record for candidates
    age = await parse_age(cv_data.get('Age'))
    experience = await parse_experience(cv_data.get('experience'))
    title_category_id = await get_title_category_id(session, title_categories)

    new_candidate = talents_DB(
        tenantId=tenantId,
        resumeId=resumeid,
        titleCategoryId=title_category_id,
        name=cv_data.get('Name'),
        age=age,
        phone=cv_data.get('Phone'),
        email=cv_data.get('Email'),
        address=cv_data.get('address')[0].get('alladdress') if cv_data.get('address') else None,
        country=cv_data.get('address')[0].get('country') if cv_data.get('address') else None,
        city=cv_data.get('address')[0].get('city') if cv_data.get('address') else None,
        title=cv_data.get('title'),
        summary=cv_data.get('summary'),
        type=profile_type.value,
        yearsOfExperience=experience
    )
    session.add(new_candidate)
    await session.flush()
    await session.commit()
    await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"create candidate record profile_id{new_candidate.id}")
    return new_candidate.id


async def process_education(session, cv_data, profile_id):
    await session.execute(delete(talent_education_DB).where(talent_education_DB.profileId == profile_id))
    for edu in cv_data.get('education', []):
        education = talent_education_DB(
            profileId=profile_id,
            description=edu.get('education'),
            school=edu.get('school'),
            speciality=edu.get('speciality'),
            department=edu.get('department'),
            degree=edu.get('degree'),
            duration=edu.get('duration')
        )
        session.add(education)
    await session.commit()

async def process_job_details(session,cv_data,profile_id):
    await session.execute(delete(talent_job_details_DB).where(talent_job_details_DB.profileId == profile_id))
    for job in cv_data.get('jobDetails', []):
        job_detail = talent_job_details_DB(
            profileId=profile_id,
            company=job.get('company'),
            position=job.get('position'),
            duration=job.get('duration'),
            responsibilities=json.dumps(job.get('responsibilities'))
        )
        session.add(job_detail)
    await session.commit()

async def process_skills(session, cv_data, profile_id):
    await session.execute(delete(talent_skills_DB).where(talent_skills_DB.profileId == profile_id))
    for skill_category in cv_data.get('skills', []):
        for skill in skill_category.get('skills', []):
            skill_entry = talent_skills_DB(
                profileId=profile_id,
                category=skill_category.get('category'),
                name=skill
            )
            session.add(skill_entry)
    await session.commit()

async def process_projects(session, cv_data, profile_id):
    await session.execute(delete(talent_projects_DB).where(talent_projects_DB.profileId == profile_id))
    for project in cv_data.get('projects', []):
        project_entry = talent_projects_DB(
            profileId=profile_id,
            name=project.get('project_name'),
            description=project.get('Project_details')
        )
        session.add(project_entry)
    await session.commit()
    for job in cv_data.get('jobDetails', []):
            for project in job.get('projects', []):
                project_entry = talent_projects_DB(
                    profileId=profile_id,
                    name=project.get('project name'),
                    description=project.get('Project details')
                )
                session.add(project_entry)
    await session.commit()

async def process_achievements(session, cv_data, profile_id):
    await session.execute(delete(talent_achievements_DB).where(talent_achievements_DB.profileId == profile_id))
    for achievement in cv_data.get('achievements', []):
        achievement_entry = talent_achievements_DB(
            profileId=profile_id,
            description=achievement
        )
        session.add(achievement_entry)
    await session.commit()

async def process_certifications(session, cv_data, profile_id):
    await session.execute(delete(talent_certifications_DB).where(talent_certifications_DB.profileId == profile_id))
    for certification in cv_data.get('certifications', []):
        certification_entry = talent_certifications_DB(
            profileId=profile_id,
            title=certification.get('title'),
            description=certification.get('description')
        )
        session.add(certification_entry)
    await session.commit()

async def process_evaluation_p(session,cv_data,profile_id):
    await session.execute(delete(talent_evaluation_DB).where(talent_evaluation_DB.profileId == profile_id))
    evaluation = talent_evaluation_DB(
        profileId=profile_id,
        strengthPoints=json.dumps(cv_data.get('strengthPoints')),
        recommendationsCV=json.dumps(cv_data.get('recommendationsCv'))
    )
    session.add(evaluation)
    await session.commit()

async def process_evaluation_c(session, cv_data, scorecandidate_json, score_candidate, profile_id):
    await session.execute(delete(talent_evaluation_DB).where(talent_evaluation_DB.profileId == profile_id))
    evaluation = talent_evaluation_DB(
        profileId=profile_id,
        score=score_candidate,
        reason=scorecandidate_json.get('reason'),
        recommendationsScore=json.dumps(scorecandidate_json.get('recommendationsScore')),
        conclusion=scorecandidate_json.get('conclusion'),
        strengthPoints=json.dumps(cv_data.get('strengthPoints')),
        recommendationsCV=json.dumps(cv_data.get('recommendationsCv'))
    )
    session.add(evaluation)
    await session.commit()

async def update_talent_pools(session, tenantId):
    result = await session.execute(select(talent_pools_DB).filter_by(tenantId=tenantId).with_for_update())
    profile_stat = result.scalars().first()
    if profile_stat:
        if profile_stat.processingProfileCount > 0:
            profile_stat.processingProfileCount -= 1
        profile_stat.totalProfileCount += 1
        await session.commit()

async def update_job_and_candidate(session, jobid, tenantId, candidate_id, profile_id):
    # Update job
    job_result = await session.execute(select(Jobs_DB).filter_by(id=jobid, tenantId=tenantId).with_for_update())
    job = job_result.scalars().first()
    if job:
        if job.processingCandidatesCount > 0:
            job.processingCandidatesCount -= 1
        job.totalCandidatesCount += 1
        await session.commit()
    
    # Update candidate profile
    result = await session.execute(select(candidates_DB).filter_by(id=candidate_id))
    candidate = result.scalars().first()

    if candidate:
        stmt = (
            update(candidates_DB).
            where(candidates_DB.id == candidate_id).
            values(profileId=profile_id)
        )
        await session.execute(stmt)
        await session.commit()
        print(f"Candidate with ID {candidate_id} updated successfully.")
        logger.info(f"Candidate with ID {candidate_id} updated successfully.")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"Candidate with ID {candidate_id} updated successfully.")

    else:
        print(f"No candidate found with ID {candidate_id}.")
        logger.warning(f"No candidate found with ID {candidate_id}.")
        await log_to_cloudwatch_logs(LOG_STREAM_NAME,f"No candidate found with ID {candidate_id}.")


    await send_eventbridge_event(profile_id, candidate_id)

async def parse_age(age_str):
    return int(age_str) if await asyncio.to_thread(isinstance, age_str, int) and age_str.isdigit() else age_str if await asyncio.to_thread(isinstance, age_str, int) else None

async def parse_experience(experience_str):
    if await asyncio.to_thread(isinstance, experience_str, str):
        match = re.search(r'\d+', experience_str)
        return int(match.group()) if match else None
    elif await asyncio.to_thread(isinstance, experience_str, str):
        return experience_str
    return None

async def get_title_category_id(session, title_categories):
    title_categories = title_categories.strip().strip('"').strip("'")
    result = await session.execute(
        select(title_categories_DB).filter(func.lower(title_categories_DB.name) == func.lower(title_categories))
    )
    title_category = result.scalars().first()
    return title_category.id if title_category else None