from pydantic import BaseModel


class LoginRequest(BaseModel):
    # Plain str, not EmailStr: email-validator rejects RFC 2606 reserved TLDs like
    # .test, which the seeded demo accounts deliberately use for fixture data.
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    display_name: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: str
