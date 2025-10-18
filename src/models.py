"""
src/models.py
"""
from phonenumbers import NumberParseException
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
import phonenumbers


Base = declarative_base()


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=False)

    building = relationship("Building", back_populates="organizations", lazy="selectin")
    activities = relationship("OrganizationActivity", back_populates="organization", lazy="selectin")
    phone_numbers = relationship("PhoneNumber", back_populates="organization", lazy="selectin",
                                 cascade="all, delete-orphan")


class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)

    organization = relationship("Organization", back_populates="phone_numbers", lazy="selectin")

    @validates('number')
    def validate_number(self, number):
        try:
            parsed_number = phonenumbers.parse(number, "RU")
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            return False


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
    level = Column(Integer, nullable=False)

    sub_activities = relationship("Activity", remote_side=[id])
    organizations = relationship("OrganizationActivity", back_populates="activity", lazy="selectin")

    @validates('level')
    def validate_level(self, level):
        if level > 3:
            raise ValueError("Максимальный уровень вложенности деятельности - 3")
        return level


class OrganizationActivity(Base):
    __tablename__ = 'organization_activities'

    organization_id = Column(Integer, ForeignKey('organizations.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), primary_key=True)

    organization = relationship("Organization", back_populates="activities", lazy="selectin")
    activity = relationship("Activity", back_populates="organizations", lazy="selectin")


class PhoneNumberModel(BaseModel):
    number: str

    @field_validator('number')
    def validate_number(cls, value):
        try:
            parsed_number = phonenumbers.parse(value, "RU")
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Неверный формат номера телефона")
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValueError("Неверный формат номера телефона")


class OrganizationCreate(BaseModel):
    name: str
    building_id: int
    phone_numbers: list[PhoneNumberModel]
    activity_ids: list[int]


class OrganizationUpdate(BaseModel):
    name: str | None = None
    building_id: int | None = None
    phone_numbers: list[PhoneNumberModel] | None = None
    activity_ids: list[int] | None = None


class BuildingCreate(BaseModel):
    address: str
    latitude: float
    longitude: float


class ActivityCreate(BaseModel):
    name: str
    parent_id: int | None = None

    @field_validator('parent_id')
    def validate_parent_id(cls, value):
        if value == 0:
            raise ValueError("Parent ID cannot be 0")
        return value


class ActivityUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None

    @field_validator('parent_id')
    def validate_parent_id(cls, value):
        if value == 0:
            raise ValueError("Parent ID cannot be 0")
        return value