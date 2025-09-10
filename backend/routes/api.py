import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.chart_analysis_agent import chart_analysis_agent
from agents.dynamic_chart_agent import process_dynamic_request
from agents.info_extractor import extract_info_from_prompt
from agents.market_analyzer import market_analyzer
from agents.multiAgent import Multi_agent_function
from agents.top_competitors import detect_top_competitors
from db.mongo import db
from schemas.domain_trends import DomainTrendsRequest
from schemas.dynamic_chart import DynamicChartRequest, DynamicChartResponse
from schemas.market_analyzer_input import MarketAnalyzerInput
from services.business_trends_service import get_domain_trends_results
from utils import memory_manager
from utils.crawled_info_saver import (
    crawl_and_filter_company_info,
    save_crawled_info_to_db,
)
from utils.files_data_extraction_reader import extract_files_content

router = APIRouter()

# Global progress tracking for ongoing analyses
analysis_progress = {}  # {session_id: progress_data}


@router.get("/", operation_id="welcome-test")
async def testGERR():
    return {"message": "Welcome to OpporTuna 🐟"}


@router.get("/analysis/progress/{session_id}", operation_id="get-analysis-progress")
async def get_analysis_progress(session_id: str):
    """
    Get the current progress of an ongoing analysis by session ID.

    Args:
        session_id: The session identifier for the analysis

    Returns:
        JSON response with current progress information
    """
    try:
        # Check if session exists
        if session_id not in analysis_progress:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for session ID: {session_id}",
            )

        progress_data = analysis_progress[session_id]

        # Calculate time elapsed
        start_time = progress_data.get("start_time", time.time())
        elapsed_time = time.time() - start_time

        # Calculate ETA
        current_progress = progress_data.get("progress", 0)
        if current_progress > 0:
            total_estimated_time = elapsed_time / (current_progress / 100.0)
            remaining_time = max(0, total_estimated_time - elapsed_time)

            # Format ETA
            if remaining_time < 60:
                eta_formatted = f"{int(remaining_time)}s"
            elif remaining_time < 3600:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                eta_formatted = f"{minutes}m {seconds}s"
            else:
                hours = int(remaining_time // 3600)
                minutes = int((remaining_time % 3600) // 60)
                eta_formatted = f"{hours}h {minutes}m"
        else:
            remaining_time = None
            eta_formatted = "Calculating..."

        return {
            "session_id": session_id,
            "status": progress_data.get("status", "running"),
            "progress": current_progress,
            "step": progress_data.get("step", "unknown"),
            "message": progress_data.get("message", "Processing..."),
            "phase": progress_data.get("phase", "initialization"),
            "elapsed_time": f"{elapsed_time:.1f}s",
            "eta_seconds": int(remaining_time) if remaining_time else None,
            "eta_formatted": eta_formatted,
            "error": progress_data.get("error", False),
            "warning": progress_data.get("warning", False),
            "last_updated": progress_data.get(
                "last_updated", datetime.utcnow().isoformat()
            ),
            "company": progress_data.get("company", ""),
            "sector": progress_data.get("sector", ""),
            "service": progress_data.get("service", ""),
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error getting analysis progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving analysis progress.",
        )


@router.delete(
    "/analysis/progress/{session_id}", operation_id="clear-analysis-progress"
)
async def clear_analysis_progress(session_id: str):
    """
    Clear the progress data for a completed or cancelled analysis.

    Args:
        session_id: The session identifier for the analysis

    Returns:
        JSON response confirming deletion
    """
    try:
        if session_id in analysis_progress:
            del analysis_progress[session_id]
            return {
                "message": f"Progress data cleared for session {session_id}",
                "session_id": session_id,
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for session ID: {session_id}",
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error clearing analysis progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while clearing analysis progress.",
        )


# Combined endpoint for extraction and confirmation
@router.post("/extract-info", operation_id="extract-or-confirm-info")
async def extract_or_confirm_info(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    session_id: Optional[str] = Header(None),
    is_confirmation: bool = Form(False),
):
    combined_doc_text = extract_files_content(files)
    result = extract_info_from_prompt(prompt, combined_doc_text, session_id)
    response_code = result.get("response_code")
    data = result.get("data", {}) if not is_confirmation else result["data"]

    required_fields = [
        "company_name",
        "business_domain",
        "region_or_market",
        "target_audience",
        "unique_value_proposition",
        "distribution_channels",
        "revenue_model",
        "key_partners",
    ]

    # Determine which fields are missing or invalid
    def is_invalid(value):
        return value is None or (
            isinstance(value, str)
            and (not value.strip() or value.strip().upper() == "N/A")
        )

    missing_fields = [field for field in required_fields if is_invalid(data.get(field))]

    newly_provided = []
    if is_confirmation:
        previous_info = getattr(memory_manager, "last_extracted_info", None)
        if previous_info:
            for field in required_fields:
                prev_val = previous_info.get(field)
                new_val = data.get(field)
                if is_invalid(prev_val) and not is_invalid(new_val):
                    newly_provided.append(field)
        memory_manager.last_extracted_info = data.copy()

    if response_code == 403:
        raise HTTPException(status_code=403, detail=result["message"])

    if response_code == 400:
        return {
            "status": "confirmation_required",
            "message": (
                "Some important details are missing or unclear."
                if not is_confirmation
                else "Some important details are still missing."
            ),
            "extracted_info": data,
            "missing_info": missing_fields,
            **({"newly_provided": newly_provided} if is_confirmation else {}),
        }

    if response_code == 200:
        # Save extracted or confirmed info
        try:
            collection = db.confirmed_infos if is_confirmation else db.extracted_infos
            await collection.insert_one({"session_id": session_id, **data})
        except Exception as e:
            print(f"MongoDB save error: {e}")

        # Handle optional website crawling
        crawled_info_to_save = None
        if data.get("urls"):
            try:
                crawled_info_to_save = await crawl_and_filter_company_info(data)
                await save_crawled_info_to_db(data, crawled_info_to_save)
            except Exception as e:
                print(f"MongoDB save error (crawled_infos): {e}")

        # Final response construction
        if not missing_fields:
            message = (
                "Information successfully confirmed and validated."
                if is_confirmation
                else "All required information has been successfully extracted and saved."
            )
            response = {
                "status": "confirmed" if is_confirmation else "processed",
                "message": message,
                "confirmed_info" if is_confirmation else "extracted_info": data,
                **({"newly_provided": newly_provided} if is_confirmation else {}),
                **(
                    {"website_crawled_info": crawled_info_to_save}
                    if crawled_info_to_save
                    else {}
                ),
            }
            return response

        # Still missing fields
        return {
            "status": "confirmation_required",
            "message": "Some infos are missed or unclear and must be provided.",
            "extracted_info": data,
            "missing_info": missing_fields,
            **({"newly_provided": newly_provided} if is_confirmation else {}),
        }

    raise HTTPException(
        status_code=500, detail="Unexpected response format from agent."
    )


@router.post("/confirm-prompt", operation_id="confirm-prompt")
async def confirm_model_results(
    prompt_id: str = Form(...),
    is_confirmed: str = Form(...),
    result_data: Optional[str] = Form(None),  # New parameter for the result data
    user_feedback: Optional[str] = Form(None),
    session_id: Optional[str] = Header(None),
):
    # Convert is_confirmed string to boolean
    is_confirmed_bool = is_confirmed.lower() == "true"

    # Prepare the document to be stored
    confirmation_doc = {
        "prompt_id": prompt_id,
        "is_confirmed": is_confirmed_bool,
        "result_data": result_data,  # Store the confirmed result data
        "user_feedback": user_feedback,
        "session_id": session_id,
        "confirmation_status": "confirmed" if is_confirmed_bool else "rejected",
        "timestamp": datetime.utcnow(),
    }

    try:
        # Store the confirmation in MongoDB
        await db.confirmations.insert_one(confirmation_doc)

        if is_confirmed_bool:
            return {
                "status": "success",
                "message": "Results confirmed and saved successfully",
                "prompt_id": prompt_id,
                "confirmation_status": "confirmed",
                "feedback": user_feedback,
                "result_data": result_data,
            }
        else:
            return {
                "status": "rejected",
                "message": "Results rejected and feedback saved",
                "prompt_id": prompt_id,
                "confirmation_status": "rejected",
                "feedback": user_feedback,
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save confirmation: {str(e)}"
        )


@router.post("/domain-trends", operation_id="get-domain-trends")
async def get_domain_trends(request: DomainTrendsRequest = Body(...)):
    """
    Given a domain, generate keywords and URLs using LLM, crawl the URLs,
    summarize the content, and return a final JSON result not exceeding 800,000 tokens.
    """
    trends_result = get_domain_trends_results(request.domain)
    return {"domain": request.domain, **trends_result}


@router.post("/market-analyzer", operation_id="market-analyzer")
async def market_analyzer_route(
    extracted_info: Dict[str, Any],  # Accept any JSON object (dict)
    session_id: Optional[str] = Header(None),
):
    try:
        # Optional: Basic validation to ensure extracted_info is a dictionary
        if not isinstance(extracted_info, dict):
            raise HTTPException(
                status_code=422, detail="Request body must be a JSON object."
            )

        # Optional: Log the received data for debugging
        # logging.info(f"Received extracted_info: {extracted_info}")

        # Call the market_analyzer function with the input dictionary
        # Ensure your market_analyzer function can handle the potentially
        # varying structure of extracted_info
        result = await market_analyzer(
            extracted_info=extracted_info, session_id=session_id
        )

        # Check for error response codes from market_analyzer
        # Ensure market_analyzer returns a dict with a potential "response_code" key
        if isinstance(result, dict) and result.get("response_code") in [400, 403, 500]:
            raise HTTPException(
                status_code=result["response_code"],
                detail=result.get("message", "Error in market analysis"),
            )

        # Return successful result
        # Adjust the return structure if your market_analyzer returns data differently
        return {
            "status": "success",
            "message": "Market analysis completed",
            "result_data": result,
        }

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions (e.g., validation errors, errors from market_analyzer)
        raise http_exc
    except Exception as e:
        # Handle any unexpected errors within the route logic
        logging.error(
            f"Unexpected error in market_analyzer_route: {e}", exc_info=True
        )  # Log the error
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while processing the request.",
            # Avoid exposing internal error details like str(e) directly to the client in production
        )


# Endpoint for detecting top 10 competitors using flexible company info JSON
@router.post("/top-competitors", operation_id="top-competitors")
async def top_competitors_route(
    company_info: Dict[str, Any] = Body(...),
    session_id: Optional[str] = Header(None),
):
    """
    Accepts a JSON object with arbitrary keys describing a company and returns the top 10 competitors and their official websites.
    """
    try:
        if not isinstance(company_info, dict):
            raise HTTPException(
                status_code=422, detail="Request body must be a JSON object."
            )
        result = await detect_top_competitors(company_info, session_id=session_id)
        if not result.get("data"):
            raise HTTPException(status_code=500, detail="Could not detect competitors.")
        return {"status": "success", "data": result["data"]}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error in top_competitors_route: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal error in competitor detection."
        )


@router.post("/analyze-data", operation_id="analyze-data")
async def analyze_data_for_charts(
    data: Dict[str, Any] = Body(...),
    session_id: Optional[str] = Header(None),
    user_id: Optional[str] = Query(
        None, description="User identifier for memory storage"
    ),
):
    """
    Analyze unstructured/semi-structured JSON data and generate chart configurations using Gemini Pro 2.5.
    Returns a non-streaming JSON response for immediate results and stores results in memory for future use.

    Args:
        data: JSON object containing the data to analyze
        session_id: Optional session identifier
        user_id: Optional user identifier for memory storage (for chart regeneration)

    Returns:
        JSON response with chart configurations that can be used to render charts
    """
    try:
        # Input validation
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=422, detail="Request body must be a JSON object."
            )

        if not data:
            raise HTTPException(status_code=400, detail="Data cannot be empty.")

        # Check if chart analysis agent service is available
        if not chart_analysis_agent.is_service_available():
            raise HTTPException(
                status_code=503,
                detail="Chart analysis service is not available. Please check API key configuration.",
            )

        # Use the chart analysis agent to analyze data with user_id for memory
        result = await chart_analysis_agent.analyze_data_for_charts(
            data, session_id, user_id=user_id
        )

        # Handle error responses from the agent
        if not result.get("success", False):
            error_code = result.get("error_code", "UNKNOWN_ERROR")
            error_message = result.get("error", "Unknown error occurred")

            # Map agent error codes to HTTP status codes
            status_code_mapping = {
                "INVALID_INPUT": 422,
                "EMPTY_DATA": 400,
                "SERVICE_UNAVAILABLE": 503,
                "NO_RESPONSE": 502,
                "NO_CANDIDATES": 502,
                "NO_CONTENT": 502,
                "NO_PARTS": 502,
                "EMPTY_TEXT": 502,
                "TEXT_EXTRACTION_ERROR": 502,
                "SAFETY_BLOCKED": 400,
                "MAX_TOKENS_EXCEEDED": 413,
                "RECITATION_BLOCKED": 400,
                "UNKNOWN_FINISH_REASON": 502,
                "TEXT_ACCESS_ERROR": 502,
                "EMPTY_RESPONSE": 502,
                "INVALID_JSON": 502,
                "INVALID_FORMAT": 502,
                "GEMINI_API_ERROR": 503,
                "INTERNAL_ERROR": 500,
            }

            status_code = status_code_mapping.get(error_code, 500)

            # Include additional debug info for certain errors
            detail = error_message
            if error_code in ["INVALID_JSON", "GEMINI_API_ERROR", "INTERNAL_ERROR"]:
                if "details" in result:
                    detail += f" Details: {result['details']}"

            raise HTTPException(status_code=status_code, detail=detail)

        # === MEMORY INTEGRATION: Store generated charts in memory for future regeneration ===
        try:
            if result.get("charts") and (user_id or session_id):
                storage_id = user_id or session_id
                charts_to_store = result["charts"]

                # Store in short-term memory for immediate access
                memory_manager.store_charts_short_term(
                    charts=charts_to_store,
                    user_prompt=f"Initial chart generation from analyze-data endpoint",
                    generation_context={
                        "generation_source": "chart_analysis_agent",
                        "original_data_size": result.get("raw_data_size", 0),
                        "analysis_summary": result.get("analysis_summary", ""),
                        "session_id": session_id,
                        "user_id": storage_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "chart_count": len(charts_to_store),
                        "data_categories": (
                            list(data.keys()) if isinstance(data, dict) else []
                        ),
                    },
                    session_id=session_id,
                )

                # Also store in long-term memory for persistent access
                memory_manager.store_charts_long_term(
                    charts=charts_to_store,
                    user_prompt=f"Initial chart generation from analyze-data endpoint",
                    generation_context={
                        "generation_source": "chart_analysis_agent",
                        "original_data": data,
                        "analysis_summary": result.get("analysis_summary", ""),
                        "session_id": session_id,
                        "user_id": storage_id,
                        "api_endpoint": "analyze-data",
                        "success_metrics": {
                            "generation_success": True,
                            "chart_quality": "ai_generated",
                            "data_complexity": len(str(data)),
                            "processing_time": result.get("processing_time", 0),
                        },
                    },
                    tags=["analyze-data", "chart_analysis_agent", "initial_generation"],
                    session_id=session_id,
                )

                logging.info(
                    f"📊 Stored {len(charts_to_store)} charts in memory for user/session: {storage_id}"
                )

        except Exception as memory_error:
            # Log memory storage error but don't fail the request
            logging.warning(f"⚠️ Failed to store charts in memory: {memory_error}")

        # Return successful result from the agent with memory storage confirmation
        response_data = {
            "status": "success",
            "message": result["message"],
            "charts": result["charts"],
            "analysis_summary": result["analysis_summary"],
            "raw_data_size": result.get("raw_data_size", 0),
            "memory_stored": bool(
                user_id or session_id
            ),  # Indicate if charts were stored in memory
            "storage_id": user_id or session_id if (user_id or session_id) else None,
        }

        return response_data

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        logging.error(
            f"Unexpected error in analyze_data_for_charts endpoint: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while analyzing the data.",
        )


@router.get("/competitors", operation_id="get-competitors")
async def get_competitors(
    session_id: Optional[str] = Query(None, description="Session ID to filter competitors"),
    company_name: Optional[str] = Query(None, description="Company name to filter competitors"),
    limit: int = Query(10, description="Maximum number of competitors to return", ge=1, le=100),
    skip: int = Query(0, description="Number of competitors to skip", ge=0),
):
    """
    Get competitors data from the database.
    
    Args:
        session_id: Optional session ID to filter results
        company_name: Optional company name to filter results
        limit: Maximum number of results to return (1-100)
        skip: Number of results to skip for pagination
    
    Returns:
        JSON response with competitors data
    """
    try:
        # Build query filter
        query_filter = {}
        if session_id:
            query_filter["analysis_session"] = session_id
        if company_name:
            query_filter["company_name"] = {"$regex": company_name, "$options": "i"}
        
        # Query database
        collection = db.competitors
        cursor = collection.find(query_filter).sort("relevance_score", -1).skip(skip).limit(limit)
        competitors = await cursor.to_list(length=limit)
        
        # Get total count for pagination
        total_count = await collection.count_documents(query_filter)
        
        # Convert ObjectId to string for JSON serialization
        for competitor in competitors:
            if "_id" in competitor:
                competitor["_id"] = str(competitor["_id"])
        
        return {
            "status": "success",
            "data": {
                "competitors": competitors,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "skip": skip,
                    "has_more": (skip + limit) < total_count
                },
                "filters": {
                    "session_id": session_id,
                    "company_name": company_name
                }
            },
            "message": f"Retrieved {len(competitors)} competitors"
        }
        
    except Exception as e:
        logging.error(f"Error fetching competitors: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch competitors data",
                "message": str(e),
                "error_code": "COMPETITORS_FETCH_ERROR"
            }
        )


@router.get("/trends", operation_id="get-trends")
async def get_trends(
    session_id: Optional[str] = Query(None, description="Session ID to filter trends"),
    category: Optional[str] = Query(None, description="Category to filter trends"),
    impact_level: Optional[str] = Query(None, description="Impact level to filter trends"),
    time_horizon: Optional[str] = Query(None, description="Time horizon to filter trends"),
    limit: int = Query(10, description="Maximum number of trends to return", ge=1, le=100),
    skip: int = Query(0, description="Number of trends to skip", ge=0),
):
    """
    Get market trends data from the database.
    
    Args:
        session_id: Optional session ID to filter results
        category: Optional category to filter results
        impact_level: Optional impact level to filter results (high, medium, low)
        time_horizon: Optional time horizon to filter results (short, medium, long)
        limit: Maximum number of results to return (1-100)
        skip: Number of results to skip for pagination
    
    Returns:
        JSON response with market trends data
    """
    try:
        # Build query filter
        query_filter = {}
        if session_id:
            query_filter["analysis_session"] = session_id
        if category:
            query_filter["category"] = {"$regex": category, "$options": "i"}
        if impact_level:
            query_filter["impact_level"] = impact_level.lower()
        if time_horizon:
            query_filter["time_horizon"] = time_horizon.lower()
        
        # Query database
        collection = db.market_trends
        cursor = collection.find(query_filter).sort("confidence_score", -1).skip(skip).limit(limit)
        trends = await cursor.to_list(length=limit)
        
        # Get total count for pagination
        total_count = await collection.count_documents(query_filter)
        
        # Convert ObjectId to string for JSON serialization
        for trend in trends:
            if "_id" in trend:
                trend["_id"] = str(trend["_id"])
        
        return {
            "status": "success",
            "data": {
                "trends": trends,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "skip": skip,
                    "has_more": (skip + limit) < total_count
                },
                "filters": {
                    "session_id": session_id,
                    "category": category,
                    "impact_level": impact_level,
                    "time_horizon": time_horizon
                }
            },
            "message": f"Retrieved {len(trends)} market trends"
        }
        
    except Exception as e:
        logging.error(f"Error fetching trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch trends data",
                "message": str(e),
                "error_code": "TRENDS_FETCH_ERROR"
            }
        )


@router.post("/competitors/generate", operation_id="generate-competitors")
async def generate_competitors(
    company_info: Dict[str, Any] = Body(...),
    session_id: Optional[str] = Header(None),
):
    """
    Generate competitors analysis for a company using AI agents.
    
    Args:
        company_info: Company information including name, sector, services, etc.
        session_id: Optional session identifier
    
    Returns:
        JSON response with generated competitors data
    """
    try:
        if not isinstance(company_info, dict):
            raise HTTPException(
                status_code=422, detail="Request body must be a JSON object."
            )
        
        # Import the MCP tool registry to access competitors agent
        from mcp.registry import get_tool_registry
        
        # Get tool registry and execute competitors detection
        registry = await get_tool_registry()
        result = await registry.execute_tool("top_competitors_detector", {
            "company_info": company_info,
            "session_id": session_id
        })
        
        if result.success:
            return {
                "status": "success",
                "message": "Competitors analysis completed successfully",
                "data": result.data,
                "session_id": session_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Competitors analysis failed",
                    "message": result.error_message,
                    "error_code": "COMPETITORS_GENERATION_FAILED"
                }
            )
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error generating competitors: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal error in competitors generation",
                "message": str(e),
                "error_code": "COMPETITORS_GENERATION_ERROR"
            }
        )


@router.post("/trends/generate", operation_id="generate-trends")
async def generate_trends(
    analysis_data: Dict[str, Any] = Body(...),
    session_id: Optional[str] = Header(None),
):
    """
    Generate market trends analysis using AI agents.
    
    Args:
        analysis_data: Analysis data including market information, time horizons, etc.
        session_id: Optional session identifier
    
    Returns:
        JSON response with generated trends data
    """
    try:
        if not isinstance(analysis_data, dict):
            raise HTTPException(
                status_code=422, detail="Request body must be a JSON object."
            )
        
        # Import the MCP tool registry to access trends agent
        from mcp.registry import get_tool_registry
        
        # Get tool registry and execute trends identification
        registry = await get_tool_registry()
        result = await registry.execute_tool("trends_identifier", {
            "analysis_data": analysis_data,
            "session_id": session_id
        })
        
        if result.success:
            return {
                "status": "success",
                "message": "Market trends analysis completed successfully",
                "data": result.data,
                "session_id": session_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Trends analysis failed",
                    "message": result.error_message,
                    "error_code": "TRENDS_GENERATION_FAILED"
                }
            )
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error generating trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal error in trends generation",
                "message": str(e),
                "error_code": "TRENDS_GENERATION_ERROR"
            }
        )


@router.post("/analyze-data-stream", operation_id="analyze-data-stream")
async def analyze_data_for_charts_stream(
    data: Dict[str, Any] = Body(...),
    session_id: Optional[str] = Header(None),
    user_id: Optional[str] = Query(
        None, description="User identifier for memory storage"
    ),
):
    """
    Analyze data and generate chart configurations with real-time streaming progress updates.
    Similar to ChatGPT's streaming response system. Also stores results in memory for regeneration.

    Args:
        data: JSON object containing the data to analyze
        session_id: Optional session identifier
        user_id: Optional user identifier for memory storage

    Returns:
        Server-Sent Events stream with progress updates and final results
    """

    async def generate_stream():
        """Generate Server-Sent Events stream for real-time updates"""

        def send_event(event_type: str, data: dict):
            """Helper to format SSE events"""
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        try:
            # Send initial connection event
            yield send_event(
                "connected",
                {
                    "message": "Connected to chart analysis service",
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": session_id,
                },
            )

            await asyncio.sleep(0.1)  # Small delay for smooth UX

            # Input validation with progress
            yield send_event(
                "progress",
                {
                    "step": "validation",
                    "message": "Validating input data...",
                    "progress": 10,
                },
            )

            if not isinstance(data, dict):
                yield send_event(
                    "error",
                    {
                        "error": "Request body must be a JSON object.",
                        "error_code": "INVALID_INPUT",
                        "status_code": 422,
                    },
                )
                return

            if not data:
                yield send_event(
                    "error",
                    {
                        "error": "Data cannot be empty.",
                        "error_code": "EMPTY_DATA",
                        "status_code": 400,
                    },
                )
                return

            await asyncio.sleep(0.2)

            # Service availability check
            yield send_event(
                "progress",
                {
                    "step": "service_check",
                    "message": "Checking Gemini AI service availability...",
                    "progress": 20,
                },
            )

            if not chart_analysis_agent.is_service_available():
                yield send_event(
                    "error",
                    {
                        "error": "Chart analysis service is not available. Please check API key configuration.",
                        "error_code": "SERVICE_UNAVAILABLE",
                        "status_code": 503,
                    },
                )
                return

            await asyncio.sleep(0.3)

            # Data preparation
            yield send_event(
                "progress",
                {
                    "step": "data_preparation",
                    "message": "Preparing data for AI analysis...",
                    "progress": 30,
                    "data_size": len(json.dumps(data)),
                },
            )

            await asyncio.sleep(0.5)

            # AI Analysis phase
            yield send_event(
                "progress",
                {
                    "step": "ai_analysis",
                    "message": "Gemini Pro 2.5 is analyzing your data patterns...",
                    "progress": 40,
                },
            )

            await asyncio.sleep(0.3)

            yield send_event(
                "progress",
                {
                    "step": "ai_analysis",
                    "message": "Identifying visualization opportunities...",
                    "progress": 55,
                },
            )

            await asyncio.sleep(0.4)

            yield send_event(
                "progress",
                {
                    "step": "ai_analysis",
                    "message": "Generating intelligent chart configurations...",
                    "progress": 70,
                },
            )

            # Call the actual analysis (this is where the real work happens)
            result = await chart_analysis_agent.analyze_data_for_charts(
                data, session_id
            )

            await asyncio.sleep(0.2)

            # Processing results
            yield send_event(
                "progress",
                {
                    "step": "processing",
                    "message": "Processing AI-generated results...",
                    "progress": 85,
                },
            )

            # Handle error responses from the agent
            if not result.get("success", False):
                error_code = result.get("error_code", "UNKNOWN_ERROR")
                error_message = result.get("error", "Unknown error occurred")

                # Map agent error codes to HTTP status codes
                status_code_mapping = {
                    "INVALID_INPUT": 422,
                    "EMPTY_DATA": 400,
                    "SERVICE_UNAVAILABLE": 503,
                    "NO_RESPONSE": 502,
                    "NO_CANDIDATES": 502,
                    "NO_CONTENT": 502,
                    "NO_PARTS": 502,
                    "EMPTY_TEXT": 502,
                    "TEXT_EXTRACTION_ERROR": 502,
                    "SAFETY_BLOCKED": 400,
                    "MAX_TOKENS_EXCEEDED": 413,
                    "RECITATION_BLOCKED": 400,
                    "UNKNOWN_FINISH_REASON": 502,
                    "TEXT_ACCESS_ERROR": 502,
                    "EMPTY_RESPONSE": 502,
                    "INVALID_JSON": 502,
                    "INVALID_FORMAT": 502,
                    "GEMINI_API_ERROR": 503,
                    "INTERNAL_ERROR": 500,
                }

                status_code = status_code_mapping.get(error_code, 500)

                # Include additional debug info for certain errors
                detail = error_message
                if error_code in ["INVALID_JSON", "GEMINI_API_ERROR", "INTERNAL_ERROR"]:
                    if "details" in result:
                        detail += f" Details: {result['details']}"

                yield send_event(
                    "error",
                    {
                        "error": detail,
                        "error_code": error_code,
                        "status_code": status_code,
                    },
                )
                return

            await asyncio.sleep(0.2)

            # Validation and finalization
            yield send_event(
                "progress",
                {
                    "step": "finalization",
                    "message": "Validating chart configurations...",
                    "progress": 95,
                },
            )

            await asyncio.sleep(0.3)

            # === MEMORY INTEGRATION: Store generated charts in memory for future regeneration ===
            try:
                if result.get("charts") and (user_id or session_id):
                    storage_id = user_id or session_id
                    charts_to_store = result["charts"]

                    # Store in short-term memory for immediate access
                    memory_manager.store_charts_short_term(
                        charts=charts_to_store,
                        user_prompt=f"Initial chart generation from analyze-data-stream endpoint",
                        generation_context={
                            "generation_source": "chart_analysis_agent_stream",
                            "original_data_size": result.get("raw_data_size", 0),
                            "analysis_summary": result.get("analysis_summary", ""),
                            "session_id": session_id,
                            "user_id": storage_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "chart_count": len(charts_to_store),
                            "data_categories": (
                                list(data.keys()) if isinstance(data, dict) else []
                            ),
                            "streaming_mode": True,
                        },
                        session_id=session_id,
                    )

                    # Also store in long-term memory for persistent access
                    memory_manager.store_charts_long_term(
                        charts=charts_to_store,
                        user_prompt=f"Initial chart generation from analyze-data-stream endpoint",
                        generation_context={
                            "generation_source": "chart_analysis_agent_stream",
                            "original_data": data,
                            "analysis_summary": result.get("analysis_summary", ""),
                            "session_id": session_id,
                            "user_id": storage_id,
                            "api_endpoint": "analyze-data-stream",
                            "success_metrics": {
                                "generation_success": True,
                                "chart_quality": "ai_generated_stream",
                                "data_complexity": len(str(data)),
                                "processing_time": result.get("processing_time", 0),
                                "streaming_mode": True,
                            },
                        },
                        tags=[
                            "analyze-data-stream",
                            "chart_analysis_agent_stream",
                            "initial_generation",
                        ],
                        session_id=session_id,
                    )

                    # Send memory storage confirmation
                    yield send_event(
                        "progress",
                        {
                            "step": "memory_storage",
                            "message": f"📊 Stored {len(charts_to_store)} charts in memory for future regeneration",
                            "progress": 98,
                            "storage_id": storage_id,
                        },
                    )

            except Exception as memory_error:
                # Log memory storage error but don't fail the stream
                logging.warning(f"⚠️ Failed to store charts in memory: {memory_error}")
                yield send_event(
                    "warning",
                    {
                        "step": "memory_storage",
                        "message": "Charts generated successfully but memory storage failed",
                        "warning": str(memory_error),
                    },
                )

            # Send completion event
            yield send_event(
                "complete",
                {
                    "step": "complete",
                    "message": f"Successfully generated {len(result['charts'])} chart configurations",
                    "progress": 100,
                },
            )

            await asyncio.sleep(0.1)

            # Send final results
            yield send_event(
                "result",
                {
                    "status": "success",
                    "message": result["message"],
                    "charts": result["charts"],
                    "analysis_summary": result["analysis_summary"],
                    "raw_data_size": result.get("raw_data_size", 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_stored": bool(
                        user_id or session_id
                    ),  # Indicate if charts were stored in memory
                    "storage_id": (
                        user_id or session_id if (user_id or session_id) else None
                    ),
                },
            )

        except Exception as e:
            logging.error(f"Error in streaming analysis: {e}", exc_info=True)
            yield send_event(
                "error",
                {
                    "error": "An internal error occurred while analyzing the data.",
                    "error_code": "INTERNAL_ERROR",
                    "status_code": 500,
                    "details": str(e),
                },
            )

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        },
    )


#


# Pydantic models for request/response
class ReportRequest(BaseModel):
    company: str = Field(..., description="Company name")
    sector: str = Field(..., description="Business sector")
    service: str = Field(..., description="Service type")


class ReportResponse(BaseModel):
    status: str
    pdf_path: str


class ErrorResponse(BaseModel):
    error: str


# API endpoint - Updated to accept JSON body
@router.post("/optigap/report", response_model=ReportResponse)
async def api_get_function(
    request: ReportRequest = Body(...),
    session_id: Optional[str] = Header(None),
):
    """
    Generate a market analysis report for the specified company, sector, and service.
    Returns a non-streaming JSON response for immediate results.

    Args:
        request: JSON object containing company details
        session_id: Optional session identifier

    Request Body:
        - **company**: The name of the company to analyze
        - **sector**: The business sector of the company
        - **service**: The type of service provided by the company

    Returns:
        JSON response with report status and PDF path
    """
    try:
        # Input validation
        if not request.company or not request.company.strip():
            raise HTTPException(status_code=422, detail="Company name cannot be empty.")

        if not request.sector or not request.sector.strip():
            raise HTTPException(
                status_code=422, detail="Business sector cannot be empty."
            )

        if not request.service or not request.service.strip():
            raise HTTPException(status_code=422, detail="Service type cannot be empty.")

        # Generate a session ID if not provided
        if not session_id:
            session_id = f"analysis_{int(time.time())}"

        # Initialize progress tracking
        start_time = time.time()
        analysis_progress[session_id] = {
            "status": "running",
            "progress": 0,
            "step": "initialization",
            "message": "Starting market analysis...",
            "phase": "initialization",
            "start_time": start_time,
            "last_updated": datetime.utcnow().isoformat(),
            "company": request.company,
            "sector": request.sector,
            "service": request.service,
            "error": False,
            "warning": False,
        }

        def progress_handler(update_data):
            """Handle progress updates from Multi_agent_function"""
            try:
                if session_id in analysis_progress:
                    analysis_progress[session_id].update(
                        {
                            "status": (
                                "error" if update_data.get("error") else "running"
                            ),
                            "progress": update_data.get("progress", 0),
                            "step": update_data.get("step", "unknown"),
                            "message": update_data.get("message", "Processing..."),
                            "phase": update_data.get("phase", "processing"),
                            "last_updated": datetime.utcnow().isoformat(),
                            "error": update_data.get("error", False),
                            "warning": update_data.get("warning", False),
                        }
                    )
            except Exception as e:
                print(f"Progress handler error: {e}")

        # Call your function with the request data and progress callback
        result = Multi_agent_function(
            request.company.strip(),
            request.sector.strip(),
            request.service.strip(),
            progress_callback=progress_handler,
        )

        # Update final progress state
        total_time = time.time() - start_time
        if session_id in analysis_progress:
            if result.get("status") == "success":
                analysis_progress[session_id].update(
                    {
                        "status": "completed",
                        "progress": 100,
                        "step": "complete",
                        "message": "✅ Market analysis completed successfully!",
                        "phase": "completed",
                        "last_updated": datetime.utcnow().isoformat(),
                        "execution_time": f"{total_time:.2f}s",
                        "pdf_path": result.get("pdf_path", ""),
                        "error": False,
                        "warning": False,
                    }
                )
            else:
                analysis_progress[session_id].update(
                    {
                        "status": "error",
                        "error": True,
                        "message": f"Analysis failed: {result.get('message', 'Unknown error')}",
                        "last_updated": datetime.utcnow().isoformat(),
                        "execution_time": f"{total_time:.2f}s",
                    }
                )

        # Ensure the result matches the expected response model
        if (
            not isinstance(result, dict)
            or "status" not in result
            or "pdf_path" not in result
        ):
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from Multi_agent_function",
            )

        # Add session_id to the response
        result["session_id"] = session_id
        return result

    except HTTPException as http_exc:
        # Update progress with error
        if session_id and session_id in analysis_progress:
            analysis_progress[session_id].update(
                {
                    "status": "error",
                    "error": True,
                    "message": str(http_exc.detail),
                    "last_updated": datetime.utcnow().isoformat(),
                }
            )
        # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        # Update progress with error
        if session_id and session_id in analysis_progress:
            analysis_progress[session_id].update(
                {
                    "status": "error",
                    "error": True,
                    "message": f"Internal error: {str(e)}",
                    "last_updated": datetime.utcnow().isoformat(),
                }
            )
        logging.error(f"Error in optigap report generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while generating the report.",
        )


@router.post("/optigap/report-stream", operation_id="optigap-report-stream")
async def api_get_function_stream(
    request: ReportRequest = Body(...),
    session_id: Optional[str] = Header(None),
):
    """
    Generate a market analysis report and return the final result as JSON.
    Features: Comprehensive error handling, session tracking, detailed analytics.

    Args:
        request: JSON object containing company details
        session_id: Optional session identifier

    Returns:
        JSON response with final analysis results, PDF path, and analytics
    """

    start_time = time.time()

    # Generate a session ID if not provided
    if not session_id:
        session_id = f"analysis_{int(start_time)}"

    # Initialize progress tracking
    analysis_progress[session_id] = {
        "status": "starting",
        "progress": 0,
        "step": "initialization",
        "message": "Initializing analysis pipeline...",
        "phase": "initialization",
        "start_time": start_time,
        "last_updated": datetime.utcnow().isoformat(),
        "company": request.company,
        "sector": request.sector,
        "service": request.service,
        "error": False,
        "warning": False,
        "velocity": 0,
        "total_steps": 8,
    }

    try:
        # Validate input
        if not request.company or not request.company.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Company name cannot be empty.",
                    "error_code": "INVALID_COMPANY",
                    "field": "company",
                },
            )

        if not request.sector or not request.sector.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Business sector cannot be empty.",
                    "error_code": "INVALID_SECTOR",
                    "field": "sector",
                },
            )

        if not request.service or not request.service.strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Service type cannot be empty.",
                    "error_code": "INVALID_SERVICE",
                    "field": "service",
                },
            )

        # Update progress tracking
        analysis_progress[session_id].update(
            {
                "status": "running",
                "progress": 10,
                "step": "validation_complete",
                "message": "Input validation successful, starting analysis...",
                "phase": "initialization",
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

        # Enhanced progress callback for tracking
        def progress_handler(update_data):
            """Enhanced progress handler for detailed tracking"""
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                progress = update_data.get("progress", 0)
                phase = update_data.get("phase", "processing")

                # Update global progress tracking
                if session_id in analysis_progress:
                    analysis_progress[session_id].update(
                        {
                            "status": (
                                "error" if update_data.get("error") else "running"
                            ),
                            "progress": progress,
                            "step": update_data.get("step", "unknown"),
                            "message": update_data.get("message", "Processing..."),
                            "phase": phase,
                            "last_updated": datetime.utcnow().isoformat(),
                            "error": update_data.get("error", False),
                            "warning": update_data.get("warning", False),
                            "elapsed_time": f"{elapsed:.1f}s",
                        }
                    )

            except Exception as e:
                logging.warning(f"Progress handler error: {e}")

        # Execute multi-agent analysis
        try:
            result = Multi_agent_function(
                request.company.strip(),
                request.sector.strip(),
                request.service.strip(),
                progress_callback=progress_handler,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_details = str(e)

            # Update global progress with error info
            if session_id in analysis_progress:
                analysis_progress[session_id].update(
                    {
                        "status": "error",
                        "error": True,
                        "message": f"Analysis failed: {error_details}",
                        "last_updated": datetime.utcnow().isoformat(),
                        "execution_time": f"{execution_time:.2f}s",
                    }
                )

            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Multi-agent analysis failed: {error_details}",
                    "error_code": "AGENT_PROCESSING_ERROR",
                    "execution_time": f"{execution_time:.2f}s",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        # Validate result
        if (
            not isinstance(result, dict)
            or "status" not in result
            or "pdf_path" not in result
        ):
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Invalid response format from Multi_agent_function",
                    "error_code": "INVALID_RESPONSE_FORMAT",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        # Check analysis success
        if result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.get("message", "Multi-agent analysis failed"),
                    "error_code": "ANALYSIS_FAILED",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        # Calculate final performance metrics
        total_execution_time = time.time() - start_time
        final_velocity = 100 / total_execution_time if total_execution_time > 0 else 0

        # Update global progress with success state
        if session_id in analysis_progress:
            analysis_progress[session_id].update(
                {
                    "status": "completed",
                    "progress": 100,
                    "step": "complete",
                    "message": "✅ Market analysis report generated successfully!",
                    "phase": "completed",
                    "last_updated": datetime.utcnow().isoformat(),
                    "execution_time": f"{total_execution_time:.2f}s",
                    "pdf_path": result.get("pdf_path", ""),
                    "error": False,
                    "warning": False,
                    "final_velocity": round(final_velocity, 2),
                }
            )

        # Return comprehensive JSON response
        return {
            "status": "success",
            "message": f"🎉 Comprehensive market analysis for {request.company} completed successfully!",
            "data": {
                "pdf_path": result["pdf_path"],
                "report_data": result.get("report_data", {}),
                "dashboard_data": result.get(
                    "dashboard_data", {}
                ),  # Include structured dashboard data
                "data_charts": result.get(
                    "data_charts", []
                ),  # Include generated charts
                "report_markdown": result.get("report_markdown"),
                "company": request.company,
                "sector": request.sector,
                "service": request.service,
                "session_id": session_id,
            },
            "analytics": {
                "execution_time": result.get(
                    "execution_time", f"{total_execution_time:.2f}s"
                ),
                "processing_speed": f"{final_velocity:.1f}%/s",
                "report_quality": "Professional Grade",
                "data_sources": result.get("metadata", {}).get(
                    "data_sources", ["Competitors", "News", "LinkedIn", "Trends"]
                ),
                "ai_models_used": ["Gemini Pro", "Multi-Agent System"],
                "analysis_quality": result.get("metadata", {}).get(
                    "analysis_quality", "comprehensive"
                ),
                "performance_metrics": {
                    "total_time": result.get(
                        "execution_time", f"{total_execution_time:.2f}s"
                    ),
                    "average_velocity": f"{final_velocity:.1f}%/s",
                    "report_size": "PDF generated",
                    "quality_score": "High",
                    "processing_time": result.get("metadata", {}).get(
                        "processing_time", total_execution_time
                    ),
                },
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "api_version": "2.0",
                "response_format": "json",
                "processing_mode": "synchronous",
                "analysis_metadata": result.get("metadata", {}),
            },
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        execution_time = time.time() - start_time

        # Log comprehensive error information
        logging.error(f"🚨 Critical error in report generation: {e}", exc_info=True)

        # Update global progress with system error
        if session_id in analysis_progress:
            analysis_progress[session_id].update(
                {
                    "status": "system_error",
                    "error": True,
                    "message": f"System failure: {str(e)}",
                    "last_updated": datetime.utcnow().isoformat(),
                    "execution_time": f"{execution_time:.2f}s",
                }
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Critical system error occurred during report generation.",
                "error_code": "SYSTEM_FAILURE",
                "details": str(e)[:200],  # Limit error details for security
                "execution_time": f"{execution_time:.2f}s",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "support_info": {
                    "contact": "Please contact support with session ID",
                    "session_id": session_id,
                    "company": request.company,
                },
            },
        )


@router.post(
    "/optigap/dynamic-chart",
    operation_id="dynamic-chart-request",
    response_model=DynamicChartResponse,
)
async def dynamic_chart_request(request: DynamicChartRequest):
    """
    Dynamic Chart Agent endpoint that intelligently processes user prompts to either:
    1. Regenerate specific charts based on user specifications
    2. Regenerate all charts when user requests comprehensive updates
    3. Fetch specific data from MongoDB and embedding databases
    4. Handle hybrid requests (both data fetching and chart generation)
    5. Leverage stored charts from memory (generated via /analyze-data endpoints)

    The agent analyzes user intent and routes to appropriate sub-agents with smart regeneration logic:
    - If user provides specific data/requirements: Only regenerate what they ask for
    - If user wants everything: Regenerate all available charts/data
    - Uses memory-stored charts for context and regeneration when available
    - Applies user preferences learned from previous chart generations
    """
    try:
        start_time = time.time()

        # Log the request with intent analysis preview
        logging.info(f"🔄 Dynamic chart request: {request.user_prompt[:100]}...")

        # Process the dynamic request with enhanced logic
        result = await process_dynamic_request(
            user_prompt=request.user_prompt,
            session_id=request.session_id,
            existing_charts=request.existing_charts,
            previous_analysis_data=request.previous_analysis_data,
        )

        execution_time = time.time() - start_time

        if result.get("success"):
            # Enhanced analytics with regeneration scope information
            regeneration_scope = result.get("regeneration_scope", "unknown")
            charts_count = len(result.get("charts", []))
            data_categories_count = len(result.get("data", {}))

            # Determine processing description
            if regeneration_scope == "specific":
                processing_description = "🎯 Processed specific user request"
            elif regeneration_scope == "all":
                processing_description = "🔄 Regenerated comprehensive data set"
            else:
                processing_description = "📊 Processed dynamic request"

            # Enhanced success message based on request type and scope
            request_type = result.get("type", "unknown")
            if request_type == "chart_generation":
                if regeneration_scope == "specific":
                    message = (
                        f"✅ Generated {charts_count} specific chart(s) as requested"
                    )
                else:
                    message = f"✅ Generated {charts_count} comprehensive chart(s)"
            elif request_type == "data_fetch":
                message = (
                    f"✅ Fetched {data_categories_count} data categories successfully"
                )
            elif request_type == "hybrid":
                message = f"✅ Processed hybrid request: {data_categories_count} data categories + {charts_count} charts"
            else:
                message = "✅ Dynamic request processed successfully"

            # Return enhanced successful result
            response_data = {
                "status": "success",
                "message": message,
                "data": {
                    "type": request_type,
                    "charts": result.get("charts", []),
                    "data": result.get("data", {}),
                    "user_request": request.user_prompt,
                    "session_id": request.session_id,
                    "regeneration_scope": regeneration_scope,
                    "user_preferences_applied": result.get(
                        "user_preferences_applied", False
                    ),
                    "existing_charts_updated": result.get("existing_charts_updated", 0),
                    "fallback_used": result.get("fallback", False),
                },
                "analytics": {
                    "execution_time": f"{execution_time:.2f}s",
                    "request_type": request_type,
                    "regeneration_scope": regeneration_scope,
                    "processing_description": processing_description,
                    "charts_generated": charts_count,
                    "data_categories": data_categories_count,
                    "existing_charts_processed": (
                        len(request.existing_charts) if request.existing_charts else 0
                    ),
                    "processing_mode": "smart_dynamic",
                    "user_intent_detected": True,
                    "preferences_applied": result.get(
                        "user_preferences_applied", False
                    ),
                    "performance": {
                        "speed": (
                            f"{charts_count / execution_time:.1f} charts/sec"
                            if execution_time > 0 and charts_count > 0
                            else "instant"
                        ),
                        "efficiency": (
                            "high"
                            if regeneration_scope == "specific"
                            else "comprehensive"
                        ),
                        "accuracy": "ai-powered",
                    },
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "api_version": "2.1",
                    "agent_type": "dynamic_chart_agent",
                    "agent_features": [
                        "smart_regeneration",
                        "intent_analysis",
                        "user_preference_detection",
                        "fallback_handling",
                    ],
                    "processed_at": result.get("generated_at")
                    or result.get("fetched_at")
                    or result.get("processed_at"),
                    "request_analysis": {
                        "has_existing_charts": bool(request.existing_charts),
                        "has_previous_data": bool(request.previous_analysis_data),
                        "prompt_length": len(request.user_prompt),
                        "regeneration_strategy": regeneration_scope,
                    },
                },
            }

            # Log the response to terminal before returning
            logging.info(
                f"✅ Dynamic Chart Response: {json.dumps(response_data, indent=2, default=str)}"
            )

            return response_data
        else:
            # Enhanced error handling with more context
            error_message = result.get("error", "Dynamic request processing failed")
            request_type = result.get("type", "unknown")

            # Provide helpful error messages based on context
            if "No data available" in error_message and request.existing_charts:
                helpful_message = "💡 Try providing more specific chart requirements or check your session data."
            elif "No data available" in error_message:
                helpful_message = "💡 Ensure your session has data or provide existing charts to work with."
            else:
                helpful_message = "💡 Please check your request format and try again."

            error_response = {
                "error": error_message,
                "helpful_message": helpful_message,
                "error_code": "DYNAMIC_REQUEST_FAILED",
                "request_type": request_type,
                "user_prompt": request.user_prompt,
                "session_id": request.session_id,
                "execution_time": f"{execution_time:.2f}s",
                "timestamp": datetime.utcnow().isoformat(),
                "troubleshooting": {
                    "suggestions": [
                        "Verify session data exists in database",
                        "Provide existing_charts if updating specific charts",
                        "Use clearer language for chart generation requests",
                        "Check if requested data categories are available",
                    ],
                    "request_context": {
                        "has_existing_charts": bool(request.existing_charts),
                        "has_previous_data": bool(request.previous_analysis_data),
                        "session_id": request.session_id,
                    },
                },
            }

            # Log the error response to terminal before raising
            logging.error(
                f"❌ Dynamic Chart Error Response: {json.dumps(error_response, indent=2, default=str)}"
            )

            raise HTTPException(
                status_code=400,
                detail=error_response,
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        execution_time = time.time() - start_time

        # Log error with context
        logging.error(f"🚨 Error in dynamic chart request: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Critical error occurred during dynamic request processing.",
                "error_code": "DYNAMIC_SYSTEM_FAILURE",
                "details": str(e)[:200],
                "execution_time": f"{execution_time:.2f}s",
                "user_prompt": request.user_prompt,
                "session_id": request.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "system_info": {
                    "agent_status": "smart_dynamic_chart_agent",
                    "features_available": [
                        "intent_analysis",
                        "smart_regeneration",
                        "fallback_charts",
                        "user_preferences",
                    ],
                    "support_info": "Contact support with session_id for assistance",
                },
            },
        )
