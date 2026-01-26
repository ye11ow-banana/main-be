from uuid import UUID

import filetype

from auth.exceptions import InvalidFileExtensionException
from clients.s3 import S3Client
from config import settings
from unitofwork import IUnitOfWork


class AvatarUploader:
    def __init__(self, uow: IUnitOfWork, s3_client: S3Client):
        self._uow = uow
        self._s3_client = s3_client

    async def upload(self, user_id: UUID, file: bytes) -> str:
        key = f"{user_id}.{self._get_file_extension(file)}"

        if await self._avatar_exists(user_id):
            self._delete(bucket=settings.s3.avatar_bucket, key=key)

        url = self._s3_client.upload_avatar(
            file=file, bucket=settings.s3.avatar_bucket, key=key
        )
        async with self._uow:
            await self._uow.users.update({"id": user_id}, avatar_url=url)
            await self._uow.commit()

        return url

    async def delete(self, user_id: UUID) -> None:
        async with self._uow:
            user = await self._uow.users.get(id=user_id)
            await self._uow.users.update({"id": user_id}, avatar_url=None)
            await self._uow.commit()
        if user.avatar_url is None:
            return
        key = user.avatar_url.split("/")[-1]
        self._delete(bucket=settings.s3.avatar_bucket, key=key)

    async def _avatar_exists(self, user_id: UUID) -> bool:
        async with self._uow:
            user = await self._uow.users.get(id=user_id)
            return user.avatar_url is not None

    def _delete(self, bucket: str, key: str) -> None:
        self._s3_client.delete(bucket=bucket, key=key)

    @staticmethod
    def _get_file_extension(file: bytes) -> str:
        kind = filetype.guess(file)
        if kind:
            return kind.extension
        raise InvalidFileExtensionException("Invalid file type")
