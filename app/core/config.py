import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    GOOGLE_CREDENTIALS_FILE: str
    GOOGLE_SHEET_NAME: str
    
    # --- NUEVA VARIABLE (ESTO ES LO QUE FALTABA) ---
    SLACK_WEBHOOK_URL: str 
    APIFY_TOKEN: str

    # Variables de Identidad (que agregamos antes)
    AGENT_NAME: str = "Pedro"
    COMPANY_NAME: str = "Violet Wave"
    NICHE: str = "Odontólogos y Clínicas Dentales"

    class Config:
        env_file = ".env"
        # Esto permite que si hay variables extra en el .env que no usamos, no de error.
        # Pero en este caso, SÍ queremos usar la de Slack, así que agregarla arriba es la solución correcta.
        extra = "ignore" 

settings = Settings()