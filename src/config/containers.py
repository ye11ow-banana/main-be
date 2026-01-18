from dependency_injector import containers, providers
from openai import OpenAI
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.services import AppService
from auth.services.authentication import JWTAuthenticationService
from auth.services.registration import RegistrationService
from calorie.openai_client.client import CalorieOpenAIClient
from calorie.services.day import DayService
from calorie.services.product import ProductService
from calorie.services.trend import TrendService
from config import settings
from notification.services.email import EmailNotificationService
from unitofwork import UnitOfWork


def create_db_engine(
    user: str, password: str, host: str, port: str, db_name: str
) -> AsyncEngine:
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    return create_async_engine(database_url, poolclass=NullPool)


class Container(containers.DeclarativeContainer):
    db_engine = providers.Singleton(
        create_db_engine,
        user=settings.db.user,
        password=settings.db.password,
        host=settings.db.host,
        port=settings.db.port,
        db_name=settings.db.db_name,
    )
    async_session_maker = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    openai_client = providers.Singleton(OpenAI, api_key=settings.openai.api_key)
    uow = providers.Factory(UnitOfWork, async_session_maker=async_session_maker)
    calorie_openai_client = providers.Factory(CalorieOpenAIClient, client=openai_client)
    jwt_authentication_service = providers.Factory(JWTAuthenticationService, uow=uow)
    registration_service = providers.Factory(RegistrationService, uow=uow)
    notification_service = providers.Factory(EmailNotificationService, uow=uow)
    app_service = providers.Factory(AppService, uow=uow)
    trend_service = providers.Factory(TrendService, uow=uow)
    day_service = providers.Factory(
        DayService, uow=uow, calorie_openai_client=calorie_openai_client
    )
    product_service = providers.Factory(ProductService, uow=uow)
