import logging
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse  
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from pydantic import BaseModel 

# Imports de tus módulos
from app.routes import webhook
from app.scheduler.tasks import daily_outreach_job

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Scheduler
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start scheduler
    scheduler.add_job(daily_outreach_job, 'cron', hour=10, minute=0, id="daily_outreach")
    scheduler.start()
    logger.info("Scheduler started.")
    yield
    # Shutdown: Stop scheduler
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

app = FastAPI(title="Violet Wave Dashboard", lifespan=lifespan)

# --- MONTAR CARPETA STATIC ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(webhook.router)

# --- MODELOS DE DATOS ---
class ScrapeRequest(BaseModel):
    city: str
    country: str
    niche: str          # <--- Nuevo
    spreadsheet_id: str # <--- Nuevo
    limit: int = 10

# --- RUTA PRINCIPAL (DASHBOARD VISUAL) ---
@app.get("/")
def read_dashboard():
    return FileResponse('static/index.html')

# --- ENDPOINT PARA BUSCAR LEADS (API) ---
@app.post("/api/buscar-leads")
async def buscar_leads_google_maps(request: ScrapeRequest):
    """
    DASHBOARD TOOL: Busca leads en Google Maps y llena el Excel indicado.
    """
    from app.services.scraper_service import ScraperService
    
    logger.info(f"🔎 Buscando '{request.niche}' en {request.city}, {request.country}")
    
    scraper = ScraperService()
    # Pasamos TODOS los parámetros nuevos
    result = scraper.scrape_and_save(
        city=request.city, 
        country=request.country, 
        niche=request.niche,
        spreadsheet_id=request.spreadsheet_id,
        limit=request.limit
    )
    
    return result

# --- ENDPOINT DE PRUEBA MANUAL (OUTREACH) ---
@app.post("/test-manual")
async def test_manual_trigger():
    logger.info(">>> 🔴 INICIANDO PRUEBA MANUAL DESDE ENDPOINT <<<")
    try:
        # Ejecutamos la tarea manualmente.
        if asyncio.iscoroutinefunction(daily_outreach_job):
            await daily_outreach_job()
        else:
            daily_outreach_job()
            
        return {"status": "success", "message": "Tarea ejecutada. Revisa la consola/terminal para ver los logs."}
    except Exception as e:
        logger.error(f"Error en prueba manual: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)