class TeamError(Exception):
    status_code = 400
    error_code = "TEAM_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class TeamAlreadyExistsError(TeamError):
    status_code = 400
    error_code = "TEAM_ALREADY_EXISTS"
    message = "A team relationship already exists between these users."


class TeamNotFoundError(TeamError):
    status_code = 400
    error_code = "TEAM_NOT_FOUND"
    message = "The requested team was not found."


class TeamPermissionError(TeamError):
    status_code = 400
    error_code = "TEAM_PERMISSION_DENIED"
    message = "You do not have permission to perform this action."
