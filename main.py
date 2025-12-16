import logging
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse  
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from pydantic import BaseModel 
from fastapi import Depends
from typing import Optional # Importante para el campo opcional

# Imports de tus módulos
from app.routes import webhook
from app.scheduler.tasks import daily_outreach_job
from app.db import database, models
from app.routers import auth
from app.core import security

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Scheduler
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(daily_outreach_job, 'cron', hour=10, minute=0, id="daily_outreach")
    scheduler.start()
    logger.info("Scheduler started.")
    models.Base.metadata.create_all(bind=database.engine)
    yield
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

app = FastAPI(title="Violet Wave Dashboard", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(webhook.router)
app.include_router(auth.router)

# --- MODELO ACTUALIZADO ---
class ScrapeRequest(BaseModel):
    apify_token: Optional[str] = None # <--- NUEVO CAMPO OPCIONAL
    city: str
    country: str
    niche: str          
    spreadsheet_id: str 
    limit: int = 10

@app.get("/")
def read_login():
    return FileResponse('static/login.html')

@app.get("/dashboard")
def read_dashboard():
    return FileResponse('static/dashboard.html')

# --- ENDPOINT PROTEGIDO ---
@app.post("/api/buscar-leads")
async def buscar_leads_google_maps(
    request: ScrapeRequest, 
    current_user: models.User = Depends(security.get_current_user)
):
    from app.services.scraper_service import ScraperService
    
    logger.info(f"🔎 Buscando '{request.niche}' (User: {current_user.email})")
    
    scraper = ScraperService()
    
    # Pasamos el token del usuario (si lo puso) al servicio
    result = scraper.scrape_and_save(
        city=request.city, 
        country=request.country, 
        niche=request.niche,
        spreadsheet_id=request.spreadsheet_id,
        limit=request.limit,
        apify_token=request.apify_token # <--- Enviamos el token
    )
    
    return result

@app.post("/test-manual")
async def test_manual_trigger(current_user: models.User = Depends(security.get_current_user)):
    logger.info(f">>> 🔴 INICIANDO PRUEBA MANUAL (User: {current_user.email}) <<<")
    try:
        if asyncio.iscoroutinefunction(daily_outreach_job):
            await daily_outreach_job()
        else:
            daily_outreach_job()
        return {"status": "success", "message": "Tarea ejecutada."}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)