from typing import Sequence


class PydanticConvertor:
    """
    Class for converting Pydantic errors to a list of dicts with fields "field" and "message".
    E.g.:
        from  {..., "loc": ("username",), "msg": "Assertion failed,
              Username must be alphanumeric", ...}
        to {"field": "username", "message": "Username must be alphanumeric"}
    """

    def __init__(
        self,
        error_message_substrings_to_convert: tuple[str, ...] | None = None,
    ) -> None:
        if error_message_substrings_to_convert is None:
            self._error_message_substrings_to_convert: tuple[str, ...] = (
                "error, ",
                "failed, ",
            )
        else:
            self._error_message_substrings_to_convert = (
                error_message_substrings_to_convert
            )

    def convert_errors(self, errors: Sequence) -> list[dict[str, str]]:
        new_errors: list[dict[str, str]] = []
        for error in errors:
            try:
                error_message = error["msg"]
            except KeyError:
                error_message = "Unknown error"
            try:
                field = str(error["loc"][-1]) if error["loc"] else "all"
            except KeyError:
                field = "all"
            error_message = self._convert_error_message(error_message)
            new_errors.append(
                dict(
                    field=field,
                    message=error_message,
                )
            )
        return new_errors

    def _convert_error_message(self, error_message: str) -> str:
        for error in self._error_message_substrings_to_convert:
            error_message = error_message.split(error)[-1]
        return error_message


class Pagination:
    def __init__(self, page: int = 1, limit: int = 10) -> None:
        self.limit = limit
        self._page = page

    def get_page_count(self, total_count: int) -> int:
        return (total_count + self.limit - 1) // self.limit

    def get_offset(self) -> int:
        return (self._page - 1) * self.limit
