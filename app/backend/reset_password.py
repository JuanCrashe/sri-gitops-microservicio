import sys
import bcrypt
from app.database import supabase

def reset_password(ruc: str, new_password: str):
    if not supabase:
        print("❌ Error: No se pudo conectar a Supabase. Verifica tus variables de entorno.")
        return False
        
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
    
    try:
        response = supabase.table('contribuyentes').update({
            'password_hash': hashed
        }).eq('ruc', ruc).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            print(f"✅ Contraseña reseteada exitosamente para el RUC: {ruc}")
            print(f"   Razón Social: {user.get('razon_social', 'N/A')}")
            print(f"   Nueva contraseña asignada: {new_password}")
            return True
        else:
            print(f"⚠️ No se encontró ningún contribuyente con el RUC: {ruc}")
            return False
    except Exception as e:
        print(f"❌ Error al actualizar contraseña: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_password.py <RUC> <NUEVA_CONTRASEÑA>")
        print("Ejemplo: python reset_password.py 1790011674001 1234")
        sys.exit(1)
        
    ruc_arg = sys.argv[1].strip()
    pwd_arg = sys.argv[2].strip()
    reset_password(ruc_arg, pwd_arg)
