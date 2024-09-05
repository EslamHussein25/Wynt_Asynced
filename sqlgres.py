from sqlalchemy import  Column, Integer, Text, DateTime, ForeignKey ,Enum , TIMESTAMP, ARRAY ,Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

import cuid

import logging

from utils import profiletype , setup_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine, SessionLocal, Base = setup_database()

class talents_DB(Base):
    __tablename__ = 'profiles'
    id = Column(Text, primary_key=True ,default=lambda: cuid.cuid())  
    tenantId = Column(Text, nullable=True)  
    resumeId = Column(Text, nullable=False)  
    name = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    socialLinks = Column(JSONB, nullable=True)
    yearsOfExperience = Column(Integer, nullable=True)
    type = Column(Enum(profiletype, name='ProfileType'), nullable=False)
    titleCategoryId = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    educations = relationship("talent_education_DB", back_populates="profile")
    job_details = relationship("talent_job_details_DB", back_populates="profile")
    skills = relationship("talent_skills_DB", back_populates="profile")
    projects = relationship("talent_projects_DB", back_populates="profile")
    achievements = relationship("talent_achievements_DB", back_populates="profile")
    certifications = relationship("talent_certifications_DB", back_populates="profile")
    evaluations = relationship("talent_evaluation_DB", back_populates="profile")
     

class talent_education_DB(Base):
    __tablename__ = 'profile_education'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False) 
    description = Column(Text, nullable=True)  # all
    school = Column(Text, nullable=True)
    speciality = Column(Text, nullable=True)
    department = Column(Text, nullable=True)
    degree = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="educations")

class talent_job_details_DB(Base):
    __tablename__ = 'profile_work_experience'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    company = Column(Text, nullable=True)
    position = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="job_details")

class talent_skills_DB(Base):
    __tablename__ = 'profile_skills'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    category = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="skills")

class talent_projects_DB(Base):
    __tablename__ = 'profile_projects'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="projects")

class talent_achievements_DB(Base):
    __tablename__ = 'profile_achievements'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    description = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="achievements")

class talent_certifications_DB(Base):
    __tablename__ = 'profile_certifications'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationship
    profile = relationship("talents_DB", back_populates="certifications")

class talent_evaluation_DB(Base):
    __tablename__ = 'profile_evaluation'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    profileId = Column(Text, ForeignKey('profiles.id'), nullable=False)  
    score = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    recommendationsScore = Column(JSONB, nullable=True)
    conclusion = Column(Text, nullable=True)
    strengthPoints = Column(JSONB, nullable=True)
    recommendationsCV = Column(JSONB, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    
    profile = relationship("talents_DB", back_populates="evaluations")


class title_categories_DB(Base):
    __tablename__ = 'title_categories'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    name = Column(Text, nullable=False)


class talent_pools_DB(Base):
    __tablename__ = 'talent_pools'
    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    tenantId = Column(Text, nullable=False)
    createdAt = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    updatedAt = Column(TIMESTAMP(timezone=False), onupdate=func.now(), nullable=False)
    processingProfileCount = Column(Integer, nullable=False, default=0)
    totalProfileCount = Column(Integer, nullable=False, default=0)

class candidates_DB(Base):
    __tablename__ = 'candidates'

    id = Column(Text, primary_key=True, default=lambda: cuid.cuid())
    jobId = Column(Text, nullable=True)
    profileId = Column(Text, nullable=True)
    resumeId = Column(Text, nullable=True)
    createdAt = Column(TIMESTAMP,default=func.now(), nullable=True)
    updatedAt = Column(TIMESTAMP,default=func.now(), onupdate=func.now(), nullable=True)

class Jobs_DB(Base):
    __tablename__ = 'jobs'

    id = Column(Text, primary_key=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    createdAt = Column(TIMESTAMP, nullable=True)
    updatedAt = Column(TIMESTAMP, nullable=True)
    location = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    employmentType = Column(Text, nullable=True)
    minSalary = Column(Integer, nullable=True)
    maxSalary = Column(Integer, nullable=True)
    salaryCurrency = Column(Text, nullable=True)
    publishStatus = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    tools = Column(ARRAY(Text), nullable=True)
    skills = Column(ARRAY(Text), nullable=True)
    candidatesRecommendation = Column(Boolean, nullable=True) 
    processingCandidatesCount = Column(Integer, nullable=True)
    totalCandidatesCount = Column(Integer, nullable=True)
    tenantId = Column(Text, nullable=True)
    industryId = Column(Text, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Base.metadata.create_all(engine)