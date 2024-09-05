import aioboto3
import logging
import asyncio
import json
from jobifyai import process_gpt_4o_turbo
from storedata import store_cv_data
from jsonup import json_load
from getdata import get_job_data
from utils import get_database_session, profiletype
from s3_operations import send_and_save_to_s3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





async def cvprocess(metadata, extracted_text):
    tenantId = metadata.get('tenant_id')
    jobid = metadata.get('job_id')
    resumeid = metadata.get('resume_id')
    candidate_id = metadata.get('candidate_id')
    
    # check if Talent or Candidate 
    profile_type = profiletype.Candidate if jobid is not None else profiletype.Talent
    # get the other data from process cv by extracting this data 
    cv_data, title_categories, score_candidate, score_candidate_j = await process_cv(extracted_text, jobid)
    #parse all the data to json 
    cv_data = await json_load(cv_data)
    scorecandidate_json = await json_load(score_candidate_j)
    #send the result to s3 on aws to save there 
    asyncio.create_task(send_and_save_to_s3(cv_data, scorecandidate_json, extracted_text, resumeid, region='us-east-1'))
    #then send the same result to the database and save it there 
    session = await get_database_session()
    try:
        success = await store_cv_data(session, cv_data, scorecandidate_json, score_candidate, resumeid, tenantId, profile_type, title_categories, jobid, candidate_id)
        if not success:
            print("Failed to store CV data")
            logger.error("Failed to store CV data")
    finally:
        await session.close()

# extract the data from cv this is the main function to work with cv 
async def process_cv(extracted_text, jobid):
    description, requirements, experience, education, tools, skills = None, None, None, None, None, None
    session = await get_database_session()

    try:
        if jobid is not None:
            job = await get_job_data(session, jobid)
            if job:
                title = job.title
                description = job.description
                requirements = job.requirements
                experience = job.experience
                education = job.education
                tools = job.tools
                skills = job.skills

    finally:
        await session.close()

    job_title = title if jobid is not None else ""
    cv_data, title_categories = await parse_cv(extracted_text)
    score_candidate, score_candidate_j = await score_cv_candidate(extracted_text, job_title, description, requirements, experience, education, tools, skills)

    return cv_data, title_categories, score_candidate, score_candidate_j

async def parse_cv(text: str):
    
    agent_script = f"""
Organize CV data into these categories, staying within 4090 tokens:
{{
"Name":"",
"Age":"",
"Phone":" , ,...",
"Email":"Write the email in lowercase letters only.",
"address":[{{
"alladdress": "get full address like:("Sadat, Square, Qalyubia Governorate")",
"country" : "Back country ISO 3166 like : EG,KSA,USA,etc....",
"city" : ""
}}],
socialLinks:[{{
"platform":"Write the platform name in lowercase except first letter only. if back presonal website back only Website",
"link":"link",
}}]
"title":"on cv",
"summary": "Max 100 words",
"experience": "Find out how many years of experience he has.",
"education": [{{
"education" : "all education"
"school" : "University, school, institute or academy",
"speciality" : "description",
"department" : "department on school",
"degree" : "",
"duration": ""
}}],
"jobDetails": [{{
"company": "",
"position": "",
"duration": "",
"responsibilities": ["",""],
"projects": [{{
"project name":"name",
"Project details":"details",
"project name":"name",
"Project details":"details",
"":"",
"":""
}}]
}}],
"skills": [{{
"category": "category name", "skills": ["...", "..."],
"":"" , "":["",""]
Get all the skills written even if they are not related
}}],
"projects": [{{
"project_name":"name",
"Project_details":"details",
"project_name":"name",
"Project_details":"details",
write all projects
}}]
"achievements": ["",""],
"certifications": ["title":"","description":""],
"strengthPoints": ["4 key strengths he/she have it Related to "title on cv"",""],
"recommendationsCv": ["4 actionable CV improvements Related to "title on cv"",""]
}}
Instructions:
1. Tailor to job title: "title":"on cv".
2. Be concise, focus on quality over quantity.
3. If input exceeds limit, focus on most recent and relevant info.
3. any field is empty back it EMPTY
"""
    data = await process_gpt_4o_turbo(text, f"{agent_script} (respond in JSON)")
    title_categories = await get_title_categories(data)
    return data, title_categories

async def score_cv_candidate(cv_text, job_title: str = "", description: str = "", requirements: str = "", experience: str = "", education: str = "", tools: str = "", skills: str = ""):
   
    agent_score_c = f"""
Human Resources Specialist Evaluation Framework for the {job_title} Role

As a Human Resources Specialist, you are tasked with critically evaluating candidates' CVs for the position of "{job_title}". This evaluation must meticulously assess the alignment of the candidate's qualifications, experience, and skills with the following parameters:

- **Job Title:** {job_title}
- **Job Description:** {description}
- **Job Requirements:** {requirements}
- **Job Skills:** {skills}
- **Job Tools:** {tools}

Evaluation Criteria:

1. **Direct Experience and Proficiency:**
   - Assess whether the candidate’s experience and proficiencies align with the specific skills and requirements outlined in the job description.
   - Only experiences directly related to these skills and requirements are acceptable.
   - Automatically assign low scores (below 50) to candidates whose experience does not align with the specified job requirements.

2. **Educational and Professional Background:**
   - Evaluate the relevance of the candidate’s educational qualifications and professional background concerning the job title and its requirements.
   - Only degrees and professional experiences explicitly related to the job role should be considered valid.
   - Deduct significant points or fail candidates who do not have the exact educational and professional background required.

3. **Transferable Skills and Knowledge Gaps:**
   - Identify and critically assess any significant knowledge gaps relative to the job requirements, skills, and tools.
   - Consider the candidate's potential to address these gaps effectively if they show clear evidence of similar past achievements.

4. **Scoring System:**
   - Implement a rigorous scoring system where scores are based primarily on the candidate’s alignment with the job title, description, requirements, skills, and tools. The system should be transparent and quantifiable, focusing on direct evidence of skills and experience as outlined.
   - Reserve scores above 50 exclusively for candidates who demonstrate strong proficiency and direct experience in the core areas outlined.

**Score:**
- Provide a score from 0 to 100 based on all Evaluation Criteria.

**Reason for the Score:**
- Provide a detailed rationale for the assigned score, focusing on how the candidate’s qualifications relate to the job title, description, requirements, skills, and tools. Clearly state any discrepancies and areas of misalignment where relevant.

**Recommendations:**
- Offer specific and actionable recommendations to the candidate to enhance their alignment with the job title, description, requirements, skills, and tools. Concentrate on development in areas directly related to their stated role.

**Conclusion:**
- Your analysis should clearly distinguish between candidates with general qualifications and those who possess the specific skills and experiences required by the job. Ensure that the scoring reflects a stringent and precise evaluation aligned with the job's explicit needs.

Please return the evaluation data in the following JSON format:
{{
    "score": "",
    "reason": "",
    "recommendations": ["", "", ""],
    "conclusion": ""
}}
"""

    score_c = await process_gpt_4o_turbo(cv_text, agent_score_c)
    try:
        score_data_c = await json_load(score_c)
        numeric_score_c = int(score_data_c["score"])
    except (KeyError, ValueError):
        numeric_score_c = 0
        logger.warning(f"Exception in numeric_score: {numeric_score_c}")

    return numeric_score_c, score_c

async def get_title_categories(data):

    parsed_data = await json_load(data)
    title = parsed_data.get("title", "EMPTY")
    logger.info(f"talent_title: {title}")
    agent_categories = """
"Software Engineer"
"BIM Coordinator"
"BIM Facilitator"
"BIM Manager"
"UX/UI Designer"
"BIM Designer"
"BIM Engineer"
"Project Manager"
"BIM Modeller"
"Data Analyst"
"Web Developer"
"DevOps Engineer"
Based on this categorys, choose one that is related to the job title sent to you.
if title Software Engineer Title Categories is Software Engineer like that on all
respond in string format like that:"BIM Engineer"
"""
    category = await process_gpt_4o_turbo(title,agent_categories)
    logger.info(f"talent_title category: {category}")
    return category

async def score_cv_profile(cv_text):
    agent_score_p = f"""
HR Specialist Evaluation Framework
As a HR Specialist, your task is to critically evaluate the CV by assessing how well the candidate's qualifications, experience, and skills align with their own stated job title, rather than the provided job description.
Evaluation Criteria:
1. **Direct Experience and Competence:**
   - Assess whether the candidate’s experience and competencies align with the skills and requirements typically associated with their stated job title.
   - Assign a low score (below 50) if the candidate’s experience does not match the typical skills and requirements for the job title listed on their CV.
2. **Educational and Professional Background:**
   - Evaluate the relevance of the candidate’s educational qualifications and professional background in relation to their job title.
   - Deduct points or fail candidates who do not possess the specific educational and professional background usually required for the job title listed.
3. **Transferable Skills and Knowledge Gaps:**
   - Identify and assess any significant knowledge gaps in relation to the common requirements for the job title.
   - Consider candidates for filling these gaps if they can demonstrate past achievements in similar areas.
4. **Scoring System:**
   - Implement a rigorous scoring system based on the candidate’s alignment with the typical requirements of their job title. The system should be transparent and measurable, focusing on direct evidence of skills and experience as relevant to the job title.
   - Reserve scores above 50 for candidates who show strong competency and direct experience relevant to the job title.
**Score:**
- Provide a score from 0 to 100 based on all Evaluation Criteria.
**Rationale for Score (reason):**
- Provide a detailed justification for the assigned score, focusing solely on how the candidate’s qualifications relate to their job title and its typical requirements. Address any discrepancies and areas of misalignment where necessary.
**Recommendations:*
- Offer specific, actionable recommendations to the candidate to enhance their alignment with the job title, concentrating on development in areas relevant to their stated role.
**Conclusion:**
- Your analysis should sharply distinguish between candidates with general qualifications and those who possess the specific skills and experiences required by the job. Ensure that the scoring reflects a stringent and precise evaluation aligned with the job's explicit needs.
Please return the evaluation data in the following JSON format:
{{
    "score": "",
    "reason": "",
    "recommendationsScore": ["", "", ""],
    "conclusion": ""
}}
"""
    
    score_p = await process_gpt_4o_turbo(cv_text, agent_score_p)
    try:
        score_data_p = await json_load(score_p)
        numeric_score_p = int(score_data_p["score"])
    except (KeyError, ValueError):
        numeric_score_p = 0
        logger.warning(f"Exception in numeric_score: {numeric_score_p}")

    return numeric_score_p, score_p






async def main():
    # This is where you'd start your main asyncio event loop, calling cvprocess and other functions
    pass

if __name__ == "__main__":
    asyncio.run(main())
