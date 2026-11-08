class ApiError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class SearchExpiredError(ApiError):
    status_code = 410
    code = "search_expired"


class ProviderError(ApiError):
    status_code = 502
    code = "provider_error"


class ProviderAuthError(ApiError):
    status_code = 502
    code = "provider_auth_error"
