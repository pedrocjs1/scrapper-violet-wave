import logging
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# --- IMPORTAMOS TUS SERVICIOS Y CONFIGURACIÓN ---
from app.services.gsheet_service import GSheetService 
from app.services.twilio_service import TwilioService
from app.core.config import settings # <--- Importante: Aquí traemos tus datos (Pedro, Violet Wave, etc.)

load_dotenv() 

logger = logging.getLogger(__name__)

# Configura OpenAI usando la key de settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# --- PROMPT DEL SISTEMA (CONFIGURADO PARA ODONTÓLOGOS) ---
# Usamos f-string para inyectar tu nombre y empresa directamente.
# Nota: Las llaves del JSON {{ }} están dobles para escapar el f-string de Python.

SYSTEM_PROMPT = f"""
Eres un experto en desarrollo de negocios (SDR) para la agencia '{settings.COMPANY_NAME}'.
Tu nombre es {settings.AGENT_NAME}.
Tu objetivo es analizar leads del nicho: {settings.NICHE}.

Tu tarea:
1. Analizar la información del lead.
2. Decidir si vale la pena contactarlo (Score 1-10).
3. Si es calificado (is_qualified=true), redactar un mensaje de apertura para WhatsApp.

REGLAS PARA EL MENSAJE:
- Debe ser corto, casual pero profesional (formato WhatsApp).
- NO uses corchetes como [Tu Nombre]. Usa tu nombre real: {settings.AGENT_NAME}.
- Menciona un problema específico de los odontólogos (ej: sillas vacías, inasistencias, confirmación manual).
- Termina con una pregunta abierta corta para iniciar conversación.
- Ejemplo de tono: "Hola [Nombre Lead], soy {settings.AGENT_NAME} de {settings.COMPANY_NAME}. Vi que gestionan muchas citas, ¿cómo manejan las inasistencias actualmente?"

Responde SOLAMENTE con este JSON:
{{
    "score": (número 1-10),
    "reason": (texto breve),
    "is_qualified": (true/false),
    "suggested_message": (El mensaje listo para enviar, sin placeholders, usando tu nombre real)
}}
"""

def qualify_lead(lead_data):
    """ Función auxiliar para consultar a GPT y calificar el lead """
    try:
        # Pasamos los datos del lead al prompt de usuario
        user_content = f"Analiza este lead: {str(lead_data)}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Puedes cambiar a gpt-4 si quieres más precisión
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        
        # Limpieza de markdown por si GPT responde con ```json ... ```
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error calificando lead: {e}")
        return None

async def daily_outreach_job():
    logger.info("Starting daily outreach job...")
    
    try:
        # 1. Instanciamos TUS servicios
        gsheet_service = GSheetService()
        twilio_service = TwilioService()
        
        # 2. Cargamos leads nuevos
        df_leads = gsheet_service.load_new_leads()
        
        if df_leads.empty:
            logger.info("No hay leads nuevos ('New') para procesar.")
            return

        logger.info(f"Encontrados {len(df_leads)} leads nuevos.")

        # 3. Procesamos cada lead
        for index, row in df_leads.iterrows():
            lead_dict = row.to_dict()
            
            # Obtenemos nombre y teléfono
            name = lead_dict.get('Nombre') or lead_dict.get('name') or 'Doctor'
            raw_phone = str(lead_dict.get('Phone', '')) 

            try:
                # 4. Calificar con IA (Usando el nuevo Prompt)
                analysis = qualify_lead(lead_dict)
                
                if analysis and analysis.get('is_qualified'):
                    message_body = analysis.get('suggested_message')
                    
                    if raw_phone:
                        # --- FORMATO WHATSAPP ---
                        if not raw_phone.startswith("whatsapp:"):
                            to_number = f"whatsapp:{raw_phone}"
                        else:
                            to_number = raw_phone

                        logger.info(f"Lead {name} CALIFICADO (Score: {analysis.get('score')}). Enviando: '{message_body}'")

                        # 5. Enviar usando TU servicio
                        sid = twilio_service.send_message(to=to_number, body=message_body)
                        
                        if sid:
                            logger.info(f"Mensaje enviado con éxito! SID: {sid}")
                            gsheet_service.update_lead_status(index, "Contacted")
                        else:
                            logger.error("Twilio no devolvió un SID, algo falló.")
                    else:
                        logger.warning(f"El lead {name} es calificado pero no tiene número de teléfono.")

                else:
                    # No calificado
                    reason = analysis.get('reason') if analysis else "Error en análisis"
                    logger.info(f"Lead {name} NO calificado. Razón: {reason}")
                    gsheet_service.update_lead_status(index, "Disqualified")

            except Exception as inner_e:
                logger.error(f"Error procesando lead {name}: {inner_e}")

    except Exception as e:
        logger.error(f"Error general en el job: {e}")