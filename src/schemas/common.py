from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")

# ── ENUMS ──

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    GENERATING_PDF = "generating_pdf"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"

class JobType(str, Enum):
    TRANSCRIPTION = "transcription"
    SUMMARIZATION = "summarization"
    PDF_GENERATION = "pdf_generation"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


# ── Paginations ──

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Page size")
    sort_by: str | None = Field(default=None, description="Sort by field")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        allowed_sizes = [10, 20, 50, 100]
        if v not in allowed_sizes:
            return min(allowed_sizes, key=lambda x: abs(x - v))
        return v

class PaginatedResponse(BaseModel), Generic[T]:
    items: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(default=0, ge=0, description="Total number of items")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Page size")
    total_pages: int = Field(default=0, ge=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Has next page")
    has_previous: bool = Field(default=False, description="Has previous page")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1,
        )
    

# ── Common Responses ──
class MessageResponse(BaseModel):
    message: str = Field(..., description="Message")

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Error details")

class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Error details")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Message")
    data: T = Field(..., description="Data")

# ── File upload ──
class FileUploadInfo(BaseModel):
    filename: str = Field(..., description="Filename")
    content_type: str = Field(..., description="Content type")
    size: int = Field(..., description="File size")
    storage_path: str = Field(..., description="Storage path")
    storage_bucket: str = Field(..., description="Storage bucket")