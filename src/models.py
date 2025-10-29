"""
src/models.py
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False, unique=True)
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)

    building = relationship("Building", back_populates="organizations", lazy="selectin")
    activities = relationship("OrganizationActivity", back_populates="organization", lazy="selectin")
    phone_numbers = relationship("PhoneNumber", back_populates="organization", lazy="selectin",
                                 cascade="all, delete-orphan")


class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)

    organization = relationship("Organization", back_populates="phone_numbers", lazy="selectin")


class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    address = Column(String, unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    organizations = relationship("Organization", back_populates="building", lazy="selectin")


class Activity(Base):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('activities.id'), nullable=True)
    level = Column(Integer, nullable=True)

    sub_activities = relationship("Activity", remote_side=[id])
    organizations = relationship("OrganizationActivity", back_populates="activity", lazy="selectin")


class OrganizationActivity(Base):
    __tablename__ = 'organization_activities'

    organization_id = Column(Integer, ForeignKey('organizations.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), primary_key=True)

    organization = relationship("Organization", back_populates="activities", lazy="selectin")
    activity = relationship("Activity", back_populates="organizations", lazy="selectin")
