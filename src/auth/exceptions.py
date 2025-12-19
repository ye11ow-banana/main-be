class AuthenticationException(ValueError):
    pass


class RegistrationException(ValueError):
    pass


class WrongEmailVerificationCodeException(ValueError):
    def __init__(self, code: int):
        super().__init__(f"Wrong verification code. Code: {code}. Please try again.")
