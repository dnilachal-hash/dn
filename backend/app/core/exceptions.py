from fastapi import HTTPException, status


class PayrollLockedError(HTTPException):
    def __init__(self, detail: str = "Payroll month is locked and cannot be modified"):
        super().__init__(status_code=status.HTTP_423_LOCKED, detail=detail)


class ComplianceBlockError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class NotFoundError(HTTPException):
    def __init__(self, entity: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


class DuplicateError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
