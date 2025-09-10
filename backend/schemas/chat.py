"""
Chat and Message Schemas for MCP Backend
Pydantic models for chat sessions, messages, and conversation management.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Individual message in a chat session.
    Supports both user and AI messages with optional data attachments.
    """
    
    _id: Optional[str] = Field(None, description="Unique message identifier")
    role: str = Field(..., description="Message role: 'user', 'assistant', 'system'")
    text: str = Field(..., description="Message content/text")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional structured data attachment")
    status: str = Field(default="processed", description="Message processing status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = Field(None, description="Timestamp when message was confirmed")
    
    # Enhanced fields for MCP integration
    mcp_tool_used: Optional[str] = Field(None, description="MCP tool that processed this message")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    confidence_score: Optional[float] = Field(None, description="AI confidence score for the response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "role": "user",
                "text": "Analyze market opportunities for my tech startup",
                "data": {"company": "TechCorp", "sector": "technology"},
                "status": "processed",
                "mcp_tool_used": "market_analyzer",
                "confidence_score": 0.95
            }
        }


class ChatSession(BaseModel):
    """
    Chat session containing multiple messages and session metadata.
    Tracks conversation context and analysis progress.
    """
    
    _id: Optional[str] = Field(None, description="Unique session identifier") 
    user_id: str = Field(..., description="User identifier")
    messages: List[Message] = Field(default=[], description="List of messages in chronological order")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Enhanced session tracking
    session_type: str = Field(default="general", description="Type of chat session")
    analysis_session_id: Optional[str] = Field(None, description="Associated analysis session ID")
    company_context: Optional[str] = Field(None, description="Company being analyzed")
    sector_context: Optional[str] = Field(None, description="Business sector context")
    status: str = Field(default="active", description="Session status: active, completed, archived")
    
    # MCP integration fields
    mcp_tools_used: List[str] = Field(default=[], description="List of MCP tools used in session")
    total_processing_time: Optional[float] = Field(None, description="Total processing time for session")
    charts_generated: int = Field(default=0, description="Number of charts generated in session")
    reports_generated: int = Field(default=0, description="Number of reports generated in session")
    
    # Analytics and insights
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="Session-level metadata")
    conversation_summary: Optional[str] = Field(None, description="AI-generated conversation summary")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": "user123",
                "session_type": "market_analysis",
                "analysis_session_id": "analysis_456",
                "company_context": "TechCorp",
                "sector_context": "technology",
                "status": "active",
                "mcp_tools_used": ["market_analyzer", "competitor_analysis"],
                "charts_generated": 3,
                "reports_generated": 1
            }
        }


class ChatMessage(BaseModel):
    """
    Simplified message model for API requests/responses.
    Used for creating new messages in chat sessions.
    """
    
    role: str = Field(..., description="Message role: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Message content")
    session_id: Optional[str] = Field(None, description="Target session ID")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="File attachments or data")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "role": "user",
                "content": "What are the main competitors in the fintech space?",
                "session_id": "session_123",
                "attachments": [{"type": "file", "name": "market_data.pdf"}]
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for chat API endpoints.
    Includes the AI response and processing metadata.
    """
    
    message: Message = Field(..., description="The generated response message")
    session_id: str = Field(..., description="Session identifier")
    processing_info: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested follow-up actions")
    charts_available: bool = Field(default=False, description="Whether charts were generated")
    reports_available: bool = Field(default=False, description="Whether reports are available")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "message": {
                    "role": "assistant",
                    "text": "Based on your market analysis, here are the top 5 competitors...",
                    "mcp_tool_used": "competitor_analysis",
                    "confidence_score": 0.92
                },
                "session_id": "session_123",
                "processing_info": {"processing_time": 2.5, "tools_used": ["competitor_analysis"]},
                "suggested_actions": ["Generate competitive analysis report", "Create market positioning chart"],
                "charts_available": True,
                "reports_available": False
            }
        }


class ConversationContext(BaseModel):
    """
    Conversation context for maintaining chat history and state.
    Used by MCP tools to understand conversation flow.
    """
    
    session_id: str = Field(..., description="Session identifier")
    recent_messages: List[Message] = Field(..., description="Recent messages for context")
    company_info: Optional[Dict[str, Any]] = Field(None, description="Extracted company information")
    analysis_state: Optional[Dict[str, Any]] = Field(None, description="Current analysis state")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences and settings")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "recent_messages": [],
                "company_info": {"name": "TechCorp", "sector": "technology"},
                "analysis_state": {"step": "competitor_analysis", "progress": 60},
                "user_preferences": {"chart_style": "modern", "detail_level": "comprehensive"}
            }
        }
