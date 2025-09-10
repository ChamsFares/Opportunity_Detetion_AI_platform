"""
Enhanced main.py for MCP-centric FastAPI application
OpportunityDetection Backend - Migration from Final-back-main
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

# Core imports
from core.config.settings import settings
from core.config.database import db_manager, create_indexes
from mcp.registry import get_tool_registry

# MCP Server
from mcp.server import get_mcp_server

# Import API routes
from routes.api import router as api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if settings.log_to_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    startup_start = time.time()
    
    try:
        # Initialize database connection
        logger.info("Initializing database connection...")
        await db_manager.connect()
        await create_indexes()
        logger.info("Database initialization complete")
        
        # Initialize MCP tool registry
        logger.info("Initializing MCP tool registry...")
        registry = await get_tool_registry()
        logger.info(f"MCP registry initialized with {len(registry.get_tools())} tools")
        
        # Initialize MCP server components
        logger.info("Initializing MCP server...")
        mcp_server = await get_mcp_server()
        logger.info("MCP server initialization complete")
        
        startup_time = time.time() - startup_start
        logger.info(f"Application startup completed in {startup_time:.2f} seconds")
        
        # Log available tools
        tools = registry.get_tools()
        logger.info("Available MCP Tools:")
        for tool_name, tool in tools.items():
            logger.info(f"  - {tool_name}: {tool.description}")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Starting application shutdown...")
        await db_manager.disconnect()
        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        description="OpportunityDetection - AI-Powered Market Analysis Platform with MCP Integration",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Setup routes
    setup_routes(app)
    
    return app


def setup_routes(app: FastAPI):
    """Setup application routes"""
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": time.time()
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic info"""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "Documentation disabled in production",
            "mcp_tools": "/mcp/tools",
            "health": "/health"
        }
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1", tags=["API"])
    
    # MCP Tools endpoint for frontend integration
    @app.get("/api/v1/tools")
    async def list_available_tools():
        """List all available MCP tools for frontend integration"""
        try:
            registry = await get_tool_registry()
            tools = registry.get_tools()
            
            # Format for frontend consumption
            formatted_tools = {}
            for tool_name, tool in tools.items():
                formatted_tools[tool_name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "type": tool.tool_type.value,
                    "version": tool.version,
                    "parameters": tool.parameters,
                    "required_parameters": tool.required_parameters,
                    "tags": tool.tags,
                    "enabled": tool.enabled
                }
            
            return {
                "tools": formatted_tools,
                "total_count": len(formatted_tools),
                "registry_status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to retrieve tools", "message": str(e)}
            )
    
    # Tool execution endpoint for frontend
    @app.post("/api/v1/tools/{tool_name}/execute")
    async def execute_tool_endpoint(tool_name: str, request: Request):
        """Execute a specific tool with parameters"""
        try:
            # Get request body
            body = await request.json()
            parameters = body.get("parameters", {})
            
            # Get registry and execute tool
            registry = await get_tool_registry()
            result = await registry.execute_tool(tool_name, parameters)
            
            return {
                "tool_name": tool_name,
                "execution_result": result.dict(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Tool execution failed for {tool_name}",
                    "message": str(e),
                    "tool_name": tool_name
                }
            )


# Create the FastAPI app
app = create_app()


# Main execution
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower()
    )
