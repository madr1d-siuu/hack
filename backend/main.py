# backend/main.py
import os
import sys
from fastapi.middleware.cors import CORSMiddleware

# Добавляем пути для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = current_dir
root_dir = os.path.dirname(backend_dir)

sys.path.insert(0, root_dir)
sys.path.insert(0, backend_dir)

print("=== Python Path ===")
for path in sys.path:
    print(f"  {path}")

# Импортируем только базовые модули
try:
    from app.core.logging import setup_logging
    from app.core.middleware import CorrelationMiddleware
    from app.api.endpoints import router as api_router
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

# Остальной код main.py
from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

try:
    from app.db.database import Base, engine
    # Создаем таблицы если их нет
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables checked/created")
except Exception as e:
    print(f"⚠️  Database tables error: {e}")

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    
    # Импортируем воркер внутри функции чтобы избежать circular import
    import asyncio
    from app.workers.transaction_worker import start_worker
    asyncio.create_task(start_worker())
    
    yield
    
    # Shutdown
    logger.info("Stopping application...")
    from app.workers.transaction_worker import stop_worker
    await stop_worker()


app = FastAPI(
    title="Anti-Fraud Transaction API",
    description="API для обнаружения мошеннических транзакций",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Временно для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)

# Роутеры
app.include_router(api_router, prefix="/api")

# Базовые endpoints
@app.get("/")
async def root():
    return {"message": "Anti-Fraud Transaction API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Админка через API + Swagger/Redoc
@app.get("/admin")
async def admin_info():
    return {
        "message": "Admin panel available via:",
        "endpoints": {
            "api_documentation": "/api/docs",
            "transactions_api": "/api/admin/transactions",
            "rules_api": "/api/admin/rules", 
            "analytics_api": "/api/admin/analytics",
            "export_csv": "/api/export/transactions"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )