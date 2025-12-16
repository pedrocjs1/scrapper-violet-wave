from openai import OpenAI
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def classify_intent(self, user_message: str) -> str:
        # Normalizamos el mensaje a minúsculas para análisis más fácil
        msg_lower = user_message.lower()
        
        prompt = f"""
        Analiza el mensaje del prospecto: '{user_message}'.
        
        Clasifica en una de estas categorías:
        
        1. READY_TO_BOOK: 
           - Si el usuario dice frases afirmativas cortas como: "Si me parece", "Dale", "Bueno", "Ok", "Si", "Me parece bien", "Genial".
           - Si pide el link o pregunta cómo seguimos.
           - Si acepta la propuesta de llamada.
        
        2. NOT_INTERESTED: 
           - Rechazo claro ("No me interesa", "No gracias").
        
        3. INTERESTED: 
           - Si hace preguntas sobre el servicio.
           - Si cuenta sus problemas ("Tengo inasistencias", "Uso excel").
           - Si dice "Me interesa" PERO es el inicio de la conversación (aún no se le ha propuesto llamada).
        
        4. QUESTION: Preguntas técnicas específicas.
        
        Responde SOLO con la etiqueta.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "Eres un clasificador de intenciones agresivo para cierre de ventas. Ante la duda de una afirmación, clasifica como READY_TO_BOOK."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip().replace("'", "").replace('"', "").replace(".", "")

    def generate_response(self, conversation_history: list) -> str:
        system_prompt = f"""
        Eres {settings.AGENT_NAME}, SDR de {settings.COMPANY_NAME}.
        
        TU OBJETIVO: Cualificar y agendar demo.
        
        ESTRATEGIA:
        1. Si es el primer mensaje, haz una pregunta de cualificación.
        2. NO envíes links todavía.
        3. Si el usuario cuenta un problema, propón la llamada: "¿Te parece bien si te muestro cómo funciona en una llamada de 10 min?"
        
        Mantén respuestas cortas.
        """

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()