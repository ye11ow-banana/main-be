from datetime import datetime
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail

from auth.models import UserInfoDTO
from config import settings
from notification.services.base import INotificationService

conf = ConnectionConfig(
    MAIL_USERNAME=settings.email.smtp_username,
    MAIL_PASSWORD=settings.email.smtp_password,
    MAIL_FROM=settings.email.smtp_from,
    MAIL_PORT=settings.email.smtp_port,
    MAIL_SERVER=settings.email.smtp_server,
    MAIL_STARTTLS=settings.email.smtp_starttls,
    MAIL_SSL_TLS=settings.email.smtp_ssl_tls,
    USE_CREDENTIALS=False,
    TEMPLATE_FOLDER=Path("/app/templates"),
)

fm = FastMail(conf)


class EmailNotificationService(INotificationService):
    async def send_verification_code(self, user: UserInfoDTO) -> None:
        code = await self.create_verification_code(user.id)
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[NameEmail(name=user.username, email=user.email)],
            template_body={
                "username": user.username,
                "email": user.email,
                "verification_code": code,
                "year": datetime.now().year,
            },
            subtype=MessageType.html,
        )
        await fm.send_message(message, template_name="email-verification.html")
