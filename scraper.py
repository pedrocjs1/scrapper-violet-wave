from apify_client import ApifyClient
from app.services.gsheet_service import GSheetService
from app.core.config import settings
import logging

# Configuración
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def run_scraper(city="Mendoza", limit=20):
    """
    Busca dentistas en la ciudad especificada y los guarda en Sheets.
    """
    if not settings.APIFY_TOKEN:
        print("[ERROR] Falta APIFY_TOKEN en el .env")
        return

    print(f"[INFO] Iniciando busqueda de Dentistas en {city}...")
    
    # 1. Conectar con Apify
    client = ApifyClient(settings.APIFY_TOKEN)

    # 2. Configurar el Actor de Google Maps
    # ID CORRECTO: compass/crawler-google-places
    run_input = {
        "searchStringsArray": [f"Dentistas en {city}", f"Clínica Dental en {city}"],
        "maxCrawledPlacesPerSearch": limit,
        "language": "es",
        "onlyDirectPlaces": True, 
    }

    # 3. Ejecutar el scraper
    try:
        # CORRECCIÓN AQUÍ: Usamos el ID oficial de Compass
        print("[INFO] Enviando tarea a Apify (esto puede tardar unos segundos)...")
        run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    except Exception as e:
        print(f"[ERROR] Fallo al conectar con Apify: {e}")
        return

    print("[INFO] Descargando resultados...")
    
    # 4. Procesar resultados
    leads_to_save = []
    
    try:
        # Iteramos sobre los items que encontró
        dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()
        
        for item in dataset_items:
            # Apify a veces devuelve el teléfono en 'phone' o 'phoneUnformatted'
            phone = item.get("phoneUnformatted") or item.get("phone")
            name = item.get("title")
            url = item.get("googleMapsUrl")
            website = item.get("website")
            
            # FILTRO DE CALIDAD: Solo guardamos si tiene teléfono
            if phone:
                lead_data = {
                    "Nombre": name,
                    "Phone": phone,
                    "Notas": f"Web: {website} | Maps: {url}"
                }
                leads_to_save.append(lead_data)
                
        print(f"[OK] Encontrados {len(leads_to_save)} leads con telefono.")

        # 5. Guardar en Google Sheets
        if leads_to_save:
            gsheet = GSheetService()
            gsheet.add_leads(leads_to_save)
        else:
            print("[AVISO] No se encontraron leads validos esta vez.")
            
    except Exception as e:
        print(f"[ERROR] Procesando datos: {e}")

if __name__ == "__main__":
    # Puedes cambiar la ciudad y la cantidad aquí
    CIUDAD = "Mendoza, Argentina"
    CANTIDAD = 5 
    
    run_scraper(CIUDAD, CANTIDAD)