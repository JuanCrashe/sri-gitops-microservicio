from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    ruc: str = Field(..., min_length=13, max_length=13)
    password: str = Field(..., min_length=1)

class ContribuyenteUpdate(BaseModel):
    razon_social: Optional[str] = None
    estado_ruc: Optional[str] = None
    tipo_contribuyente: Optional[str] = None
    regimen_impositivo: Optional[str] = None
    actividad_economica: Optional[str] = None
    
    class Config:
        extra = "forbid"
