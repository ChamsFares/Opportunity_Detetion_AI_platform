"""
Input Schemas for MCP Backend
General input validation and processing schemas.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class InputType(str, Enum):
    """Types of input data."""
    TEXT = "text"
    FILE = "file"
    URL = "url"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"


class ProcessingMode(str, Enum):
    """Processing modes for input data."""
    SYNC = "synchronous"
    ASYNC = "asynchronous"
    BATCH = "batch"
    STREAM = "stream"
    REAL_TIME = "real_time"


class DataFormat(str, Enum):
    """Supported data formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "markdown"


class ValidationRule(BaseModel):
    """Validation rule for input data."""
    
    field_name: str = Field(..., description="Name of field to validate")
    rule_type: str = Field(
        ...,
        description="Type of validation rule",
        pattern="^(required|type|range|pattern|custom|length|format)$"
    )
    rule_value: Union[str, int, float, Dict[str, Any]] = Field(
        ...,
        description="Value or configuration for the rule"
    )
    error_message: Optional[str] = Field(
        None,
        description="Custom error message for validation failure"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "field_name": "email",
                "rule_type": "pattern",
                "rule_value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                "error_message": "Please provide a valid email address"
            }
        }


class FileMetadata(BaseModel):
    """Metadata for file inputs."""
    
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    file_hash: Optional[str] = Field(None, description="Hash of file content")
    upload_timestamp: datetime = Field(..., description="When file was uploaded")
    encoding: Optional[str] = Field(None, description="File encoding")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "filename": "data.csv",
                "file_size": 1024000,
                "mime_type": "text/csv",
                "file_hash": "sha256:abc123...",
                "upload_timestamp": "2024-01-15T10:30:00Z",
                "encoding": "utf-8"
            }
        }


class ProcessingOptions(BaseModel):
    """Processing options for input data."""
    
    extract_text: bool = Field(False, description="Whether to extract text content")
    extract_metadata: bool = Field(True, description="Whether to extract metadata")
    perform_ocr: bool = Field(False, description="Whether to perform OCR on images")
    language_detection: bool = Field(False, description="Whether to detect language")
    content_analysis: bool = Field(False, description="Whether to perform content analysis")
    data_validation: bool = Field(True, description="Whether to validate data")
    format_conversion: Optional[str] = Field(None, description="Target format for conversion")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "extract_text": True,
                "extract_metadata": True,
                "perform_ocr": False,
                "language_detection": True,
                "content_analysis": True,
                "data_validation": True,
                "format_conversion": "json"
            }
        }


class InputData(BaseModel):
    """Base input data model."""
    
    input_id: Optional[str] = Field(None, description="Unique identifier for input")
    input_type: InputType = Field(..., description="Type of input data")
    content: Union[str, Dict[str, Any], List[Any]] = Field(
        ...,
        description="Input content"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    source: Optional[str] = Field(None, description="Source of the input data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Input timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TextInput(InputData):
    """Text input specification."""
    
    input_type: InputType = Field(InputType.TEXT, description="Input type fixed as text")
    content: str = Field(..., description="Text content", max_length=1000000)
    language: Optional[str] = Field(None, description="Language of the text")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "input_type": "text",
                "content": "This is sample text content for analysis",
                "language": "en",
                "encoding": "utf-8",
                "source": "user_input"
            }
        }


class FileInput(InputData):
    """File input specification."""
    
    input_type: InputType = Field(InputType.FILE, description="Input type fixed as file")
    content: str = Field(..., description="File content or file path")
    file_metadata: FileMetadata = Field(..., description="File metadata")
    processing_options: Optional[ProcessingOptions] = Field(
        None,
        description="Options for processing the file"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "input_type": "file",
                "content": "/path/to/file.pdf",
                "file_metadata": {
                    "filename": "document.pdf",
                    "file_size": 2048000,
                    "mime_type": "application/pdf",
                    "upload_timestamp": "2024-01-15T10:30:00Z"
                },
                "processing_options": {
                    "extract_text": True,
                    "perform_ocr": True
                }
            }
        }


class URLInput(InputData):
    """URL input specification."""
    
    input_type: InputType = Field(InputType.URL, description="Input type fixed as URL")
    content: str = Field(..., description="URL to process", pattern=r"^https?://.*")
    fetch_options: Optional[Dict[str, Any]] = Field(
        None,
        description="Options for fetching URL content"
    )
    
    @validator('content')
    def validate_url(cls, v):
        """Validate URL format."""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "input_type": "url",
                "content": "https://example.com/article",
                "fetch_options": {
                    "timeout": 30,
                    "follow_redirects": True,
                    "extract_links": True
                }
            }
        }


class StructuredInput(InputData):
    """Structured data input specification."""
    
    input_type: InputType = Field(InputType.STRUCTURED, description="Input type fixed as structured")
    content: Dict[str, Any] = Field(..., description="Structured data content")
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="Schema definition for validation"
    )
    data_format: DataFormat = Field(..., description="Format of structured data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "input_type": "structured",
                "content": {
                    "name": "John Doe",
                    "age": 30,
                    "skills": ["Python", "AI", "Data Science"]
                },
                "data_format": "json",
                "schema_definition": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                        "skills": {"type": "array"}
                    }
                }
            }
        }


class InputProcessingRequest(BaseModel):
    """
    Request model for input processing.
    """
    
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    inputs: List[Union[TextInput, FileInput, URLInput, StructuredInput]] = Field(
        ...,
        description="Input data to process"
    )
    processing_mode: ProcessingMode = Field(
        ProcessingMode.SYNC,
        description="Processing mode"
    )
    validation_rules: Optional[List[ValidationRule]] = Field(
        None,
        description="Custom validation rules"
    )
    output_format: Optional[DataFormat] = Field(None, description="Desired output format")
    
    # Advanced processing options
    priority: Optional[int] = Field(1, description="Processing priority (1-10)")
    timeout: Optional[int] = Field(300, description="Processing timeout in seconds")
    retry_attempts: Optional[int] = Field(3, description="Number of retry attempts")
    
    # MCP integration
    mcp_tools: Optional[List[str]] = Field(None, description="MCP tools to use")
    analysis_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context for analysis"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "request_id": "req_12345",
                "inputs": [
                    {
                        "input_type": "text",
                        "content": "Analyze this business trend data",
                        "source": "user_query"
                    }
                ],
                "processing_mode": "synchronous",
                "output_format": "json",
                "priority": 5,
                "mcp_tools": ["text_analyzer", "trend_detector"]
            }
        }


class ValidationResult(BaseModel):
    """Result of input validation."""
    
    is_valid: bool = Field(..., description="Whether input is valid")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    processed_fields: Optional[List[str]] = Field(
        None,
        description="Successfully processed fields"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Large file size may affect processing speed"],
                "processed_fields": ["content", "metadata", "source"]
            }
        }


class ProcessingResult(BaseModel):
    """Result of input processing."""
    
    input_id: str = Field(..., description="Input identifier")
    processed_content: Union[str, Dict[str, Any], List[Any]] = Field(
        ...,
        description="Processed content"
    )
    extracted_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted metadata"
    )
    content_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Content analysis results"
    )
    processing_time: float = Field(..., description="Processing time in seconds")
    quality_score: Optional[float] = Field(None, description="Content quality score")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "input_id": "input_123",
                "processed_content": {
                    "text": "Processed text content",
                    "entities": ["AI", "machine learning"],
                    "sentiment": "positive"
                },
                "processing_time": 1.5,
                "quality_score": 0.87
            }
        }


class InputProcessingResponse(BaseModel):
    """
    Response model for input processing.
    """
    
    request_id: str = Field(..., description="Request identifier")
    processing_timestamp: datetime = Field(..., description="When processing completed")
    
    # Processing results
    validation_results: List[ValidationResult] = Field(
        ...,
        description="Validation results for each input"
    )
    processing_results: List[ProcessingResult] = Field(
        ...,
        description="Processing results for each input"
    )
    
    # Summary information
    total_inputs: int = Field(..., description="Total number of inputs processed")
    successful_inputs: int = Field(..., description="Number of successfully processed inputs")
    failed_inputs: int = Field(..., description="Number of failed inputs")
    
    # Technical details
    total_processing_time: float = Field(..., description="Total processing time")
    processing_mode_used: ProcessingMode = Field(..., description="Processing mode used")
    mcp_tools_used: List[str] = Field(default=[], description="MCP tools used")
    
    # Error handling
    errors: List[str] = Field(default=[], description="Processing errors")
    warnings: List[str] = Field(default=[], description="Processing warnings")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "request_id": "req_12345",
                "processing_timestamp": "2024-01-15T10:30:00Z",
                "total_inputs": 3,
                "successful_inputs": 3,
                "failed_inputs": 0,
                "total_processing_time": 4.2,
                "processing_mode_used": "synchronous",
                "mcp_tools_used": ["text_analyzer", "content_extractor"]
            }
        }
