import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_db():
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("⚠️  No se encontró DATABASE_URL en el entorno. Saltando inicialización automática de DB.")
        return

    print("🔄 Intentando inicializar la base de datos...")
    try:
        # Conectarse a Postgres
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # 1. Crear extensión UUID si no existe
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        # 2. Eliminar tabla usuarios obsoleta
        cursor.execute("DROP TABLE IF EXISTS usuarios;")

        # 3. Crear tabla contribuyentes (ahora con password_hash)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contribuyentes (
                ruc VARCHAR(13) PRIMARY KEY,
                password_hash VARCHAR NOT NULL,
                razon_social VARCHAR,
                estado_ruc VARCHAR,
                tipo_contribuyente VARCHAR,
                regimen_impositivo VARCHAR,
                actividad_economica TEXT,
                ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 4. Insertar la empresa de prueba con su contraseña
        cursor.execute("""
            INSERT INTO contribuyentes (ruc, password_hash, razon_social, estado_ruc, tipo_contribuyente, regimen_impositivo, actividad_economica)
            VALUES ('1790011674001', '$2b$12$4BY9p.L1y6koWe1VDyrdxu20arZNIwNGR70W9lWQ1fqNC.Mmz88Ay', 'CORPORACION FAVORITA C.A.', 'ACTIVO', 'Sociedad', 'Régimen General', 'Venta al por mayor y menor de productos de supermercado.')
            ON CONFLICT (ruc) DO NOTHING;
        """)

        print("✅ Tablas y datos de prueba creados/verificados correctamente.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")

if __name__ == "__main__":
    init_db()
