import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Las variables de entorno ya son inyectadas por docker-compose

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Las variables SUPABASE_URL o SUPABASE_KEY no están definidas en el .env")
    sys.exit(1)

print(f"🔍 Probando conexión a Supabase...\nURL: {SUPABASE_URL}")

try:
    # 1. Intentar inicializar el cliente
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente de Supabase inicializado correctamente (el formato de las llaves es válido).")
    
    # 2. Intentar hacer una pequeña consulta para verificar permisos y conexión real
    # Buscamos un límite de 1 para que sea rápida.
    response = supabase.table('contribuyentes').select('*').limit(1).execute()
    print("✅ Conexión exitosa. Se logró consultar la tabla 'contribuyentes'.")
    print(f"   Datos recibidos: {response.data}")

except Exception as e:
    print(f"\n❌ Error al conectar o consultar Supabase:\n{str(e)}")
