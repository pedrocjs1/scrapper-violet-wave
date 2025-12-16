from fastapi.testclient import TestClient
from main import app
from app.db import models, database

# CONFIGURACIÓN:
# Usamos la base de datos REAL (leads.db) para que el usuario quede guardado.

client = TestClient(app)

def create_admin_user():
    print("------------------------------------------------")
    print("[INFO] INICIANDO CONFIGURACION DE USUARIO ADMIN")
    print("------------------------------------------------")

    email = "admin@violetwave.com"
    password = "admin123" 
    
    print(f"1. Intentando registrar usuario: {email}")
    
    # Intentamos registrar
    try:
        response = client.post("/register", json={"email": email, "password": password})
        
        if response.status_code == 200:
            print("[OK] USUARIO CREADO CON EXITO.")
        elif response.status_code == 400:
            print("[INFO] El usuario ya existe (eso es bueno, seguimos).")
        else:
            print(f"[ERROR] Error creando usuario: {response.text}")
            return
            
    except Exception as e:
        print(f"[ERROR CRITICO] en registro: {e}")
        return

    print("\n2. Probando Login (Obtener Token)...")
    try:
        response = client.post("/token", data={"username": email, "password": password})
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"[OK] Login Exitoso! Token generado.")
            print("------------------------------------------------")
            print("CREDENCIALES PARA ENTRAR AL DASHBOARD:")
            print(f"Email:    {email}")
            print(f"Password: {password}")
            print("------------------------------------------------")
        else:
            print(f"[ERROR] Login fallo: {response.text}")
            
    except Exception as e:
        print(f"[ERROR CRITICO] en login: {e}")

if __name__ == "__main__":
    # Aseguramos que las tablas existan antes de empezar
    models.Base.metadata.create_all(bind=database.engine)
    create_admin_user()