from fastapi import APIRouter, Form
from app.services.openai_service import OpenAIService
from app.services.twilio_service import TwilioService
from app.services.gsheet_service import GSheetService
from app.services.slack_service import SlackService
from app.utils.memory import Memory
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

openai_service = OpenAIService()
twilio_service = TwilioService()
gsheet_service = GSheetService()
slack_service = SlackService()
memory = Memory()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    user_id = From 
    user_message = Body
    
    logger.info(f"📩 Mensaje: {user_message} | De: {user_id}")
    
    # Recuperamos historial ANTES de agregar el nuevo mensaje para contar
    current_history = memory.get_history(user_id)
    turns_count = len(current_history)
    
    # Guardamos el mensaje actual
    memory.add_message(user_id, "user", user_message)
    
    # 1. Clasificar
    intent = openai_service.classify_intent(user_message)
    logger.info(f"🧠 Intent Original: {intent} | Turnos: {turns_count}")

    # --- REGLA DE SEGURIDAD ---
    # Si el usuario dice "Si me interesa" en el primer mensaje, NO cerrar venta aún.
    # Forzamos que pase a INTERESTED para que el bot haga preguntas.
    if intent == 'READY_TO_BOOK' and turns_count < 2:
        logger.info("🛡️ Intervención de seguridad: Es muy pronto para cerrar. Cambiando a INTERESTED.")
        intent = 'INTERESTED'

    # --- FLUJO ---
    if intent == 'READY_TO_BOOK':
        logger.info("🚀 >>> CIERRE DE VENTA DETECTADO <<<")
        
        clean_phone = user_id.replace("whatsapp:", "")
        
        # A. Excel
        gsheet_service.update_status_by_phone(clean_phone, "Lead Caliente")
        
        # B. Slack (Intentamos enviar y logueamos resultado)
        try:
            slack_service.send_alert(clean_phone, user_message)
            logger.info("🔔 Alerta enviada a Slack")
        except Exception as e:
            logger.error(f"❌ Error enviando a Slack: {e}")

        # C. Link
        reply = "¡Genial! 🚀 Vamos a solucionarlo.\n\nAgenda tu demo de 10 min aquí:\n👉 https://calendly.com/ramiro-baudo-violetwaveai/30min"
        twilio_service.send_message(user_id, reply)
        memory.add_message(user_id, "assistant", reply)
        
        return {"status": "handoff_completed"}

    elif intent == 'NOT_INTERESTED':
        clean_phone = user_id.replace("whatsapp:", "")
        gsheet_service.update_status_by_phone(clean_phone, "No interesado")
        return {"status": "stopped"}

    else:
        # Conversación (INTERESTED)
        # Aquí el bot leerá el prompt nuevo y hará preguntas de cualificación
        history = memory.get_history(user_id)
        reply = openai_service.generate_response(history)
        
        memory.add_message(user_id, "assistant", reply)
        twilio_service.send_message(user_id, reply)
        
        return {"status": "replied"}