from twilio.rest import Client
from app.core.config import settings

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def send_message(self, to: str, body: str):
        """Sends an SMS/WhatsApp message."""
        # For this MVP, we will assume WhatsApp if the number starts with whatsapp:, otherwise SMS.
        # But for 'daily outreach' usually it's SMS unless specified.
        # If testing with WhatsApp Sandbox, 'to' and 'from' need 'whatsapp:' prefix.
        
        from_number = settings.TWILIO_PHONE_NUMBER
        if to.startswith("whatsapp:") and not from_number.startswith("whatsapp:"):
             from_number = f"whatsapp:{from_number}"
        
        message = self.client.messages.create(
            body=body,
            from_=from_number,
            to=to
        )
        return message.sid
