from apify_client import ApifyClient
# from app.core.config import settings  <-- Ya no necesitamos esto aquí
from app.services.gsheet_service import GSheetService
import logging

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        # ¡IMPORTANTE! Quitamos el cliente por defecto.
        # Si no hay token del usuario, no se usa nada.
        pass 

    def scrape_and_save(self, city: str, country: str, niche: str, spreadsheet_id: str, limit: int, apify_token: str = None):
        """
        Busca leads usando OBLIGATORIAMENTE el token del usuario.
        """
        # 1. Validación Estricta del Token
        if not apify_token or len(apify_token) < 10:
            logger.warning("Intento de scraping sin token de Apify válido.")
            return {
                "status": "error", 
                "message": "⚠️ Error: Debes ingresar TU Token de Apify para poder buscar leads. No se ha realizado ninguna búsqueda."
            }

        logger.info(f"[INFO] Usando Token del Usuario: {apify_token[:5]}...")
        client = ApifyClient(apify_token)

        search_location = f"{niche} en {city}, {country}"
        print(f"[INFO] Buscando: '{search_location}' (Limit: {limit})")

        # 2. Configurar Apify
        run_input = {
            "searchStringsArray": [search_location], 
            "maxCrawledPlacesPerSearch": limit,
            "language": "es",
            "onlyDirectPlaces": False, 
        }

        try:
            # Ejecutar el actor
            run = client.actor("compass/crawler-google-places").call(run_input=run_input)
        except Exception as e:
            print(f"[ERROR] Fallo Apify: {e}")
            # Mensaje más amigable si el token es inválido
            if "authentication failed" in str(e).lower() or "token" in str(e).lower():
                 return {"status": "error", "message": "El Token de Apify ingresado no es válido o ha expirado."}
            return {"status": "error", "message": str(e)}

        # 3. Procesar resultados
        leads_found = []
        try:
            dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()
            for item in dataset_items:
                phone = item.get("phoneUnformatted") or item.get("phone")
                name = item.get("title")
                url = item.get("googleMapsUrl")
                website = item.get("website")
                
                if phone:
                    lead_data = {
                        "Nombre": name,
                        "Phone": phone,
                        "Notas": f"Nicho: {niche} | Web: {website} | Maps: {url}"
                    }
                    leads_found.append(lead_data)
        except Exception as e:
             return {"status": "error", "message": f"Error procesando dataset: {str(e)}"}

        print(f"[INFO] Encontrados {len(leads_found)} leads brutos.")

        # 4. Guardar en Excel y obtener reporte
        try:
            gsheet_specific = GSheetService(spreadsheet_id=spreadsheet_id)
            # save_report ahora es un diccionario: {"added": X, "duplicates": Y}
            save_report = gsheet_specific.add_leads(leads_found)
            
            return {
                "status": "success", 
                "found": len(leads_found), 
                # Usamos los datos del nuevo reporte
                "added_new": save_report['added'],
                "duplicates": save_report['duplicates'],
                "city": city,
                "niche": niche
            }
        except Exception as e:
            return {"status": "error", "message": f"Error Excel: {str(e)}"}