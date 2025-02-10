import logging
from fastapi import FastAPI
from app.db.session import init_db
from app.api.routes import admin, crawler, health, product, proxy


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("crawler.log")],
)

logger = logging.getLogger(__name__)


app = FastAPI(title="E-commerce Crawler API")

# Include routers
app.include_router(crawler.router)
app.include_router(product.router)
app.include_router(proxy.router)
app.include_router(health.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}


# Runs logging output to the console
logging.basicConfig(level=logging.DEBUG)
