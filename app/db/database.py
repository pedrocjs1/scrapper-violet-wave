import os  # <--- IMPORTANTE: Necesitamos importar 'os'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# LÓGICA INTELIGENTE:
# 1. Pregunta si existe la carpeta del volumen de Railway (/app/data)
# 2. Si existe, usa esa ruta para que los datos sean eternos.
# 3. Si no existe (estás en tu PC), usa el archivo local ./leads.db
if os.path.exists("/app/data"):
    SQLALCHEMY_DATABASE_URL = "sqlite:////app/data/leads.db"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./leads.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()