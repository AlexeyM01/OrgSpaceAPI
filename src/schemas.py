from pydantic import BaseModel, field_validator
import phonenumbers
from typing import List, Optional


class PhoneNumberModel(BaseModel):
    number: str

    @classmethod
    @field_validator('number')
    def validate_number(cls, value: str) -> str:
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
    phone_numbers: List[PhoneNumberModel]
    activity_ids: List[int]


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    phone_numbers: Optional[List[PhoneNumberModel]] = None
    activity_ids: Optional[List[int]] = None


class BuildingCreate(BaseModel):
    address: str
    latitude: float
    longitude: float


class ActivityCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

    @classmethod
    @field_validator('parent_id')
    def validate_parent_id(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("ID родительской активности должно быть положительным")
        return value


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None

    @classmethod
    @field_validator('parent_id')
    def validate_parent_id(cls, value: Optional[int]) -> Optional[int]:
        if value <= 0:
            raise ValueError("ID родительской активности должно быть положительным")
        return value if value is not None else None
