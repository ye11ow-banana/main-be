from dependency_injector.wiring import inject
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from auth.exceptions import (
    AuthenticationException,
    InvalidFileExtensionException,
    RegistrationException,
    WrongEmailVerificationCodeException,
)
from auth.models import (
    RefreshTokenDTO,
    TokenDTO,
    UserInCreateDTO,
    UserInfoDTO,
    UserInLoginDTO,
    UserVerificationCodeDTO,
)
from config.dependencies import (
    ActiveUserDep,
    AuthenticatedUserDep,
    AvatarUploaderDep,
    EmailNotificationDep,
    JWTAuthenticationDep,
    RegistrationDep,
    UserServiceDep,
)
from models import ResponseDTO, SuccessDTO

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sign-in")
@inject
async def sign_in(
    user: UserInLoginDTO,
    jwt_auth_service: JWTAuthenticationDep,
) -> ResponseDTO[TokenDTO]:
    try:
        token = await jwt_auth_service.authenticate_user(user)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ResponseDTO[TokenDTO](data=token)


@router.post("/refresh-token")
@inject
async def refresh_token(
    token: RefreshTokenDTO, jwt_auth_service: JWTAuthenticationDep
) -> ResponseDTO[TokenDTO]:
    try:
        token = await jwt_auth_service.refresh_access_token(token.refresh_token)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ResponseDTO[TokenDTO](data=token)


@router.get("/me")
async def get_current_user(
    user: AuthenticatedUserDep,
) -> ResponseDTO[UserInfoDTO]:
    return ResponseDTO[UserInfoDTO](data=user)


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
@inject
async def sign_up(
    user: UserInCreateDTO,
    registration_service: RegistrationDep,
) -> ResponseDTO[UserInfoDTO]:
    try:
        new_user = await registration_service.register_user(user)
    except RegistrationException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[UserInfoDTO](data=new_user)


@router.post("/email/verification-code", status_code=status.HTTP_200_OK)
@inject
async def send_email_verification_code(
    user: AuthenticatedUserDep,
    notification_service: EmailNotificationDep,
) -> ResponseDTO[SuccessDTO]:
    if user.is_verified:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="User is already verified"
        )
    try:
        await notification_service.send_verification_code(user)
    except RegistrationException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[SuccessDTO](data=SuccessDTO())


@router.post("/email/verify")
@inject
async def verify_email(
    code: UserVerificationCodeDTO,
    user: AuthenticatedUserDep,
    registration_service: RegistrationDep,
) -> ResponseDTO[SuccessDTO]:
    if user.is_verified:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="User is already verified"
        )
    try:
        await registration_service.apply_code(code.code, user.id)
    except WrongEmailVerificationCodeException as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResponseDTO[SuccessDTO](data=SuccessDTO())


@router.get("/users")
@inject
async def get_users(
    _: ActiveUserDep, user_service: UserServiceDep
) -> ResponseDTO[UserInfoDTO]:
    users = await user_service.get_users()
    return ResponseDTO[UserInfoDTO](data=users)


@router.post("/avatar")
@inject
async def upload_avatar(
    user: ActiveUserDep,
    uploader: AvatarUploaderDep,
    avatar: UploadFile = File(...),
) -> ResponseDTO[SuccessDTO]:
    if avatar.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported avatar type",
        )

    content = await avatar.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        await uploader.upload(user.id, content)
    except InvalidFileExtensionException:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported avatar type",
        )

    return ResponseDTO[SuccessDTO](data=SuccessDTO())


@router.delete("/avatar")
@inject
async def delete_avatar(
    user: ActiveUserDep, uploader: AvatarUploaderDep
) -> ResponseDTO[SuccessDTO]:
    await uploader.delete(user.id)
    return ResponseDTO[SuccessDTO](data=SuccessDTO())
