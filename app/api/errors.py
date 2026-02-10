from fastapi import HTTPException


class NotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)


class AuthenticationException(HTTPException):
    def __init__(self, detail: str = "Authentication failed."):
        super().__init__(status_code=401, detail=detail)


class FetchException(HTTPException):
    def __init__(self, detail: str = "Failed to fetch data"):
        super().__init__(status_code=502, detail=detail)
