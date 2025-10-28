import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Используем переменную окружения для Docker или локальную для разработки
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgreP12@postgres:5432/DB_HACK"
)

# Создаем движок базы данных
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    echo=False  # Логирование SQL-запросов (True для отладки)
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()