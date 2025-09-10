"""
Enhanced MCP Server configuration and startup
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config.settings import settings
from core.config.database import db_manager, create_indexes
from mcp.registry import get_tool_registry, ToolRegistry
from mcp.tools import MCPToolSchema, ToolExecutionResult, ToolStatus

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


class MCPServer:
    """Enhanced MCP Server with tool orchestration"""
    
    def __init__(self):
        self.app: Optional[FastAPI] = None
        self.registry: Optional[ToolRegistry] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the MCP server"""
        if self._initialized:
            return
        
        try:
            # Initialize database
            await db_manager.connect()
            await create_indexes()
            
            # Initialize tool registry
            self.registry = await get_tool_registry()
            
            # Create FastAPI app
            self.app = self._create_app()
            
            self._initialized = True
            logger.info(f"MCP Server initialized with {len(self.registry.get_tools())} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan management"""
            logger.info(f"Starting {settings.mcp_server_name}...")
            
            try:
                if not self._initialized:
                    await self.initialize()
                
                logger.info(f"Server ready with {len(self.registry.get_tools())} tools")
                yield
                
            except Exception as e:
                logger.error(f"Server startup failed: {e}")
                raise
            finally:
                # Cleanup
                await db_manager.disconnect()
                logger.info("Server shutdown complete")
        
        app = FastAPI(
            title=settings.mcp_server_name,
            description=settings.mcp_server_description,
            version=settings.mcp_server_version,
            debug=settings.debug,
            lifespan=lifespan,
            docs_url="/docs" if settings.debug else None,
            redoc_url="/redoc" if settings.debug else None
        )
        
        # Add middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )
        
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Setup MCP routes
        self._setup_mcp_routes(app)
        
        return app
    
    def _setup_mcp_routes(self, app: FastAPI):
        """Setup MCP-specific routes"""
        
        @app.get("/mcp/tools", response_model=Dict[str, MCPToolSchema])
        async def list_tools():
            """List all available MCP tools"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            return self.registry.get_tools()
        
        @app.get("/mcp/tools/{tool_name}", response_model=MCPToolSchema)
        async def get_tool(tool_name: str):
            """Get details of a specific tool"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            tool = self.registry.get_tool(tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail="Tool not found")
            
            return tool
        
        @app.post("/mcp/tools/{tool_name}/execute", response_model=ToolExecutionResult)
        async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
            """Execute a specific tool with parameters"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            try:
                result = await self.registry.execute_tool(tool_name, parameters)
                return result
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/mcp/tools/type/{tool_type}", response_model=List[MCPToolSchema])
        async def get_tools_by_type(tool_type: str):
            """Get tools by type"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            from .tools import ToolType
            try:
                type_enum = ToolType(tool_type)
                tools = self.registry.get_tools_by_type(type_enum)
                return tools
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid tool type")
        
        @app.get("/mcp/metrics")
        async def get_metrics():
            """Get tool execution metrics"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            return self.registry.get_metrics()
        
        @app.get("/mcp/history")
        async def get_execution_history(limit: Optional[int] = 100):
            """Get tool execution history"""
            if not self.registry:
                raise HTTPException(status_code=503, detail="Registry not initialized")
            
            return self.registry.get_execution_history(limit)
        
        @app.get("/mcp/status")
        async def get_server_status():
            """Get MCP server status"""
            from .registry import get_registry_status
            
            return {
                "server": {
                    "name": settings.mcp_server_name,
                    "version": settings.mcp_server_version,
                    "initialized": self._initialized,
                    "environment": settings.environment
                },
                "registry": get_registry_status(),
                "database": {
                    "connected": db_manager._client is not None,
                    "database": settings.mongodb_database
                }
            }
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server": settings.mcp_server_name,
                "version": settings.mcp_server_version,
                "timestamp": logger.handlers[0].formatter.formatTime(
                    logging.LogRecord(
                        name="health",
                        level=logging.INFO,
                        pathname="",
                        lineno=0,
                        msg="",
                        args=(),
                        exc_info=None
                    )
                )
            }
    
    async def run(self, host: str = None, port: int = None):
        """Run the MCP server"""
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("App not initialized")
        
        config = uvicorn.Config(
            app=self.app,
            host=host or settings.host,
            port=port or settings.port,
            reload=settings.reload,
            workers=settings.workers if not settings.reload else 1,
            log_level=settings.log_level.lower()
        )
        
        server = uvicorn.Server(config)
        await server.serve()


# Global MCP server instance
mcp_server = MCPServer()


async def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance"""
    if not mcp_server._initialized:
        await mcp_server.initialize()
    return mcp_server
