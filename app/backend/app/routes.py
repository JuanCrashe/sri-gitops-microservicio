import os
import jwt
import bcrypt
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models import ContribuyenteUpdate
from app.database import supabase

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_jwt_secret():
    return os.environ.get('JWT_SECRET', 'super-secret-default-key')

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token is invalid or expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        data = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        current_user = data.get('sub')
        if current_user is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return current_user

def validar_ruc_sintaxis(ruc: str) -> bool:
    return bool(re.match(r'^\d{13}$', ruc))

@router.post('/auth/login')
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    ruc = form_data.username
    password = form_data.password

    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection error")

    response = supabase.table('contribuyentes').select('*').eq('ruc', ruc).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
    user = response.data[0]
    
    if 'password_hash' not in user or not user['password_hash']:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
    token = jwt.encode({
        'sub': user['ruc'],
        'exp': datetime.utcnow() + timedelta(hours=2)
    }, get_jwt_secret(), algorithm="HS256")
    
    # Retornamos el estándar OAuth2 para Swagger (access_token),
    # y también 'token'/'ruc' para mantener compatibilidad total con tu código Frontend en Flask.
    return {
        "access_token": token,
        "token_type": "bearer",
        "token": token,
        "ruc": user['ruc']
    }

@router.get('/contribuyente/{ruc}')
def get_contribuyente(ruc: str, current_user: str = Depends(get_current_user)):
    if not validar_ruc_sintaxis(ruc):
        raise HTTPException(status_code=400, detail="RUC inválido. Debe tener exactamente 13 dígitos numéricos.")
        
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection error")
        
    response = supabase.table('contribuyentes').select('*').eq('ruc', ruc).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Contribuyente no encontrado")
        
    return response.data[0]

@router.put('/contribuyente/{ruc}')
def update_contribuyente(ruc: str, contribuyente: ContribuyenteUpdate, current_user: str = Depends(get_current_user)):
    if not validar_ruc_sintaxis(ruc):
        raise HTTPException(status_code=400, detail="RUC inválido. Debe tener exactamente 13 dígitos numéricos.")
        
    validated_data = contribuyente.model_dump(exclude_unset=True)
    
    if not validated_data:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection error")
        
    validated_data['ultima_actualizacion'] = datetime.utcnow().isoformat()
    
    response = supabase.table('contribuyentes').update(validated_data).eq('ruc', ruc).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Contribuyente no encontrado o error al actualizar")
        
    return response.data[0]
