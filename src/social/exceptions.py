class TeamError(ValueError):
    pass


class TeamAlreadyExistsError(TeamError):
    pass


class TeamNotFoundError(TeamError):
    pass


class TeamPermissionError(TeamError):
    pass
