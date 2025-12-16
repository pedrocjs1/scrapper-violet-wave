import requests
import json
import logging
from app.core.config import settings # <--- IMPORTANTE: Usamos tu config central

logger = logging.getLogger(__name__)

class SlackService:
    def __init__(self):
        # En lugar de buscar en el sistema, la sacamos de tu configuración ya cargada
        self.webhook_url = settings.SLACK_WEBHOOK_URL

    def send_alert(self, lead_phone, message_content):
        # Verificación de seguridad
        if not self.webhook_url:
            logger.warning("⚠️ CRÍTICO: No hay URL de Slack configurada en settings.")
            return

        # Preparamos el mensaje bonito
        payload = {
            "text": f"🔥 *LEAD CALIENTE DETECTADO* 🔥\n\n📱 *Teléfono:* {lead_phone}\n💬 *Dijo:* _{message_content}_\n🚀 *Acción:* Link enviado. ¡Revisar Calendly!"
        }

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                logger.error(f"❌ Error Slack: {response.status_code} - {response.text}")
            else:
                logger.info("✅ Notificación enviada a Slack con éxito.")
                
        except Exception as e:
            logger.error(f"❌ Fallo al conectar con Slack: {e}")