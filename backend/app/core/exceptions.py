from http import HTTPStatus


class AppError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "not_found", HTTPStatus.NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, "conflict", HTTPStatus.CONFLICT)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, "unauthorized", HTTPStatus.UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "forbidden", HTTPStatus.FORBIDDEN)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, "validation_error", HTTPStatus.UNPROCESSABLE_ENTITY)
