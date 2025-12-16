from apify_client import ApifyClient
from app.core.config import settings
from app.services.gsheet_service import GSheetService
import logging

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_TOKEN)
        # Nota: Ya no instanciamos GSheetService aquí por defecto.
        # Lo haremos dinámicamente en el método scrape_and_save

    def scrape_and_save(self, city: str, country: str, niche: str, spreadsheet_id: str, limit: int):
        """
        Busca leads por Nicho + Ubicación y guarda en el Sheet ID especificado.
        """
        # Construimos la búsqueda dinámica: "Dentistas en Mendoza, Argentina"
        search_query = f"{niche} en {city}, {country}"
        print(f"[INFO] Iniciando busqueda: '{search_query}' -> Sheet Destino: {spreadsheet_id}")

        # 1. Configurar Apify
        run_input = {
            "searchStringsArray": [search_query], 
            "maxCrawledPlacesPerSearch": limit,
            "language": "es",
            "onlyDirectPlaces": False, # False permite encontrar más negocios relacionados al nicho
        }

        try:
            # Ejecutar el actor
            run = self.client.actor("compass/crawler-google-places").call(run_input=run_input)
        except Exception as e:
            print(f"[ERROR] Fallo Apify: {e}")
            return {"status": "error", "message": str(e)}

        # 2. Procesar resultados
        leads_found = []
        try:
            dataset_items = self.client.dataset(run["defaultDatasetId"]).iterate_items()
            
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

        print(f"[INFO] Encontrados {len(leads_found)} leads brutos. Filtrando duplicados...")

        # 3. Guardar en el Excel ESPECÍFICO
        try:
            # Instanciamos el servicio CON el ID que mandó el usuario desde el Dashboard
            gsheet_specific = GSheetService(spreadsheet_id=spreadsheet_id)
            added_count = gsheet_specific.add_leads(leads_found)
            
            return {
                "status": "success", 
                "found": len(leads_found), 
                "added_new": added_count,
                "city": city,
                "country": country,
                "niche": niche
            }
        except Exception as e:
            return {"status": "error", "message": f"Error conectando al Excel (ID incorrecto o sin permisos): {str(e)}"}