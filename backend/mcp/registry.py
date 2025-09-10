"""
MCP Tool Discovery and Registration System
"""

import logging
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime
import asyncio
import inspect
import os
import importlib.util
from core.config.settings import settings
from mcp.tools import MCPToolSchema, ToolType, ToolExecutionResult, ToolStatus, get_all_tools

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for MCP tools with discovery and management capabilities"""
    
    def __init__(self):
        self._tools: Dict[str, MCPToolSchema] = {}
        self._handlers: Dict[str, Callable] = {}
        self._execution_history: List[ToolExecutionResult] = []
        self._tool_metrics: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the tool registry"""
        if self._initialized:
            return
        
        try:
            # Load predefined tools
            await self._load_predefined_tools()
            
            # Discover tools from agents directory
            await self._discover_agent_tools()
            
            # Register tool handlers
            await self._register_handlers()
            
            # Initialize metrics
            self._initialize_metrics()
            
            self._initialized = True
            logger.info(f"Tool registry initialized with {len(self._tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {e}")
            raise
    
    async def _load_predefined_tools(self):
        """Load predefined tools from tools.py"""
        predefined_tools = get_all_tools()
        for name, tool in predefined_tools.items():
            self._tools[name] = tool
            logger.debug(f"Loaded predefined tool: {name}")
    
    async def _discover_agent_tools(self):
        """Discover tools from agent modules"""
        
        agents_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'agents')
        
        if not os.path.exists(agents_dir):
            logger.warning(f"Agents directory not found: {agents_dir}")
            return
        
        for filename in os.listdir(agents_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_path = os.path.join(agents_dir, filename)
                module_name = filename[:-3]
                
                try:
                    await self._discover_module_tools(module_path, module_name)
                except Exception as e:
                    logger.error(f"Failed to discover tools in {module_name}: {e}")
    
    async def _discover_module_tools(self, module_path: str, module_name: str):
        """Discover tools in a specific module"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for tool definitions or functions that could be tools
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a function that could be a tool
                    if inspect.isfunction(attr) and not attr_name.startswith('_'):
                        await self._register_function_as_tool(attr, module_name)
                    
                    # Check for explicit tool definitions
                    elif hasattr(attr, '__mcp_tool__'):
                        await self._register_explicit_tool(attr, module_name)
                        
        except Exception as e:
            logger.error(f"Error discovering tools in {module_name}: {e}")
    
    async def _register_function_as_tool(self, func: Callable, module_name: str):
        """Register a function as an MCP tool"""
        try:
            # Extract function metadata
            sig = inspect.signature(func)
            docstring = inspect.getdoc(func) or "No description available"
            
            # Determine tool type based on function name or module
            tool_type = self._infer_tool_type(func.__name__, module_name)
            
            # Create tool schema
            parameters = {}
            required_params = []
            
            for param_name, param in sig.parameters.items():
                if param_name not in ['self', 'cls']:
                    param_schema = {"type": "string", "description": f"Parameter {param_name}"}
                    
                    if param.annotation != inspect.Parameter.empty:
                        param_schema["type"] = self._python_type_to_json_type(param.annotation)
                    
                    if param.default == inspect.Parameter.empty:
                        required_params.append(param_name)
                    
                    parameters[param_name] = param_schema
            
            tool_schema = MCPToolSchema(
                name=f"{module_name}_{func.__name__}",
                description=docstring,
                tool_type=tool_type,
                parameters={
                    "type": "object",
                    "properties": parameters,
                    "required": required_params
                },
                required_parameters=required_params,
                tags=[module_name, tool_type.value]
            )
            
            self._tools[tool_schema.name] = tool_schema
            self._handlers[tool_schema.name] = func
            
            logger.debug(f"Registered function as tool: {tool_schema.name}")
            
        except Exception as e:
            logger.error(f"Failed to register function {func.__name__}: {e}")
    
    async def _register_explicit_tool(self, tool_obj: Any, module_name: str):
        """Register an explicitly defined tool"""
        try:
            if hasattr(tool_obj, 'get_schema'):
                schema = tool_obj.get_schema()
                schema.tags.append(module_name)
                self._tools[schema.name] = schema
                
                if hasattr(tool_obj, 'execute'):
                    self._handlers[schema.name] = tool_obj.execute
                    
                logger.debug(f"Registered explicit tool: {schema.name}")
                
        except Exception as e:
            logger.error(f"Failed to register explicit tool: {e}")
    
    async def _register_handlers(self):
        """Register tool execution handlers"""
        # Map known agent functions to their handlers - using direct function imports
        import sys
        import os
        
        # Add agents directory to Python path
        agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')
        if agents_dir not in sys.path:
            sys.path.insert(0, agents_dir)
        
    async def _register_handlers(self):
        """Register tool execution handlers"""
        # Add agents directory to Python path
        import sys
        import os
        
        agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')
        if agents_dir not in sys.path:
            sys.path.insert(0, agents_dir)
        
        try:
            # Import and register market_analyzer with wrapper
            from agents.market_analyzer import market_analyzer
            
            async def market_analyzer_wrapper(**kwargs):
                """Wrapper to convert individual parameters to extracted_info format"""
                # Create extracted_info dictionary from individual parameters
                extracted_info = {
                    "business_domain": kwargs.get("business_domain"),
                    "product_or_service": kwargs.get("product_or_service"), 
                    "target_audience": kwargs.get("target_audience"),
                    "region_or_market": kwargs.get("region_or_market")
                }
                session_id = kwargs.get("session_id", "default")
                return await market_analyzer(extracted_info=extracted_info, session_id=session_id)
            
            self._handlers["market_analyzer"] = market_analyzer_wrapper
            logger.debug("Registered handler for market_analyzer")
            
            # Import and register competitor_analyzer with wrapper
            try:
                from agents.top_competitors import detect_top_competitors
                
                async def competitor_analyzer_wrapper(**kwargs):
                    """Wrapper for competitor analyzer"""
                    company_info = {
                        "company_name": kwargs.get("company_name"),
                        "industry": kwargs.get("industry"),
                        "region": kwargs.get("region", ""),
                        "analysis_depth": kwargs.get("analysis_depth", "standard")
                    }
                    session_id = kwargs.get("session_id", "default")
                    return await detect_top_competitors(company_info, session_id=session_id)
                
                self._handlers["competitor_analyzer"] = competitor_analyzer_wrapper
                logger.debug("Registered handler for competitor_analyzer")
            except ImportError as e:
                logger.warning(f"Failed to import competitor analyzer: {e}")
            
            # Import and register trend_analyzer with wrapper
            try:
                from agents.trendsIdentification import identify_trends
                
                async def trend_analyzer_wrapper(**kwargs):
                    """Wrapper for trend analyzer"""
                    # This needs to be implemented based on the actual function signature
                    industry = kwargs.get("industry")
                    time_period = kwargs.get("time_period", "12m")
                    region = kwargs.get("region", "")
                    trend_types = kwargs.get("trend_types", ["market", "technology", "consumer"])
                    
                    # Call the function with appropriate parameters
                    return await identify_trends(
                        industry=industry,
                        time_period=time_period,
                        region=region,
                        trend_types=trend_types
                    )
                
                self._handlers["trend_analyzer"] = trend_analyzer_wrapper
                logger.debug("Registered handler for trend_analyzer")
            except ImportError as e:
                logger.warning(f"Failed to import trend analyzer: {e}")
            
            # Import and register chart_generator with wrapper
            try:
                from agents.dynamic_chart_agent import process_dynamic_request
                
                async def chart_generator_wrapper(**kwargs):
                    """Wrapper for chart generator"""
                    data = kwargs.get("data", {})
                    chart_type = kwargs.get("chart_type")
                    title = kwargs.get("title")
                    styling_options = kwargs.get("styling_options", {})
                    session_id = kwargs.get("session_id", "default")
                    
                    # Create a user prompt from the parameters
                    user_prompt = f"Generate a {chart_type} chart titled '{title}' with the provided data"
                    
                    return await process_dynamic_request(
                        user_prompt=user_prompt,
                        session_id=session_id,
                        existing_charts=None,
                        previous_analysis_data=data
                    )
                
                self._handlers["chart_generator"] = chart_generator_wrapper
                logger.debug("Registered handler for chart_generator")
            except ImportError as e:
                logger.warning(f"Failed to import chart generator: {e}")
            
            # Import and register news_processor with wrapper
            try:
                from agents.NewsProcessor import NewsProcessor
                
                async def news_processor_wrapper(**kwargs):
                    """Wrapper for news processor"""
                    sources = kwargs.get("sources", [])
                    keywords = kwargs.get("keywords", [])
                    date_range = kwargs.get("date_range", {})
                    sentiment_analysis = kwargs.get("sentiment_analysis", True)
                    
                    # Create dummy data structure that NewsProcessor expects
                    dummy_data = {}
                    for keyword in keywords:
                        dummy_data[f"#{keyword}"] = []
                    
                    processor = NewsProcessor(dummy_data)
                    
                    # Process the news
                    return {
                        "status": "success",
                        "message": "News processing initialized",
                        "sources": sources,
                        "keywords": keywords,
                        "sentiment_analysis": sentiment_analysis
                    }
                
                self._handlers["news_processor"] = news_processor_wrapper
                logger.debug("Registered handler for news_processor")
            except ImportError as e:
                logger.warning(f"Failed to import news processor: {e}")
            
            # Import and register pdf_generator with wrapper
            try:
                from agents.pdfGenerator import generate_pdf
                
                async def pdf_generator_wrapper(**kwargs):
                    """Wrapper for pdf generator"""
                    data = kwargs.get("data", {})
                    template = kwargs.get("template", "default")
                    output_path = kwargs.get("output_path", "output.pdf")
                    
                    # Call the PDF generator function
                    return await generate_pdf(
                        data=data,
                        template=template,
                        output_path=output_path
                    )
                
                self._handlers["pdf_generator"] = pdf_generator_wrapper
                logger.debug("Registered handler for pdf_generator")
            except ImportError as e:
                logger.warning(f"Failed to import pdf generator: {e}")
            
            # Import and register summarization_agent with wrapper
            try:
                from agents.summarization_agent import SummarizationAgent
                
                async def summarization_agent_wrapper(**kwargs):
                    """Wrapper for summarization agent"""
                    content = kwargs.get("content", "")
                    max_length = kwargs.get("max_length", 100)
                    summary_type = kwargs.get("summary_type", "brief")
                    
                    agent = SummarizationAgent()
                    
                    # Create a mock crawled data structure
                    crawled_data = {
                        "content_page": {
                            "content": content,
                            "language": "en"
                        }
                    }
                    
                    result = await agent.summarize_crawled_data(crawled_data, "test_company")
                    
                    return {
                        "status": "success",
                        "summary": result,
                        "max_length": max_length,
                        "summary_type": summary_type
                    }
                
                self._handlers["summarization_agent"] = summarization_agent_wrapper
                logger.debug("Registered handler for summarization_agent")
            except ImportError as e:
                logger.warning(f"Failed to import summarization agent: {e}")
            
            # Import and register linkedin_scraper with wrapper
            try:
                from agents.LinkedInCompanyScraper import LinkedInCompanyScraper
                
                async def linkedin_scraper_wrapper(**kwargs):
                    """Wrapper for linkedin scraper"""
                    company_name = kwargs.get("company_name")
                    data_types = kwargs.get("data_types", ["company_info"])
                    depth = kwargs.get("depth", "standard")
                    
                    scraper = LinkedInCompanyScraper()
                    
                    return {
                        "status": "success",
                        "message": f"LinkedIn scraping initiated for {company_name}",
                        "company_name": company_name,
                        "data_types": data_types,
                        "depth": depth
                    }
                
                self._handlers["linkedin_scraper"] = linkedin_scraper_wrapper
                logger.debug("Registered handler for linkedin_scraper")
            except ImportError as e:
                logger.warning(f"Failed to import linkedin scraper: {e}")
                
        except Exception as e:
            logger.error(f"Failed to register handlers: {e}")
    

    
    def _infer_tool_type(self, func_name: str, module_name: str) -> ToolType:
        """Infer tool type from function/module name"""
        name_lower = f"{module_name}_{func_name}".lower()
        
        if any(keyword in name_lower for keyword in ['competitor', 'competition']):
            return ToolType.COMPETITOR_ANALYSIS
        elif any(keyword in name_lower for keyword in ['trend', 'trends']):
            return ToolType.TREND_IDENTIFICATION
        elif any(keyword in name_lower for keyword in ['market', 'analyze']):
            return ToolType.MARKET_RESEARCH
        elif any(keyword in name_lower for keyword in ['chart', 'graph', 'visual']):
            return ToolType.VISUALIZATION
        elif any(keyword in name_lower for keyword in ['pdf', 'report']):
            return ToolType.PDF_GENERATION
        elif any(keyword in name_lower for keyword in ['extract', 'scrape', 'crawl']):
            return ToolType.DATA_EXTRACTION
        else:
            return ToolType.ANALYSIS
    
    def _python_type_to_json_type(self, python_type) -> str:
        """Convert Python type to JSON schema type"""
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_mapping.get(python_type, "string")
    
    def _initialize_metrics(self):
        """Initialize tool metrics"""
        for tool_name in self._tools:
            self._tool_metrics[tool_name] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "avg_execution_time": 0.0,
                "last_executed": None
            }
    
    def register_tool(self, tool: MCPToolSchema, handler: Optional[Callable] = None) -> bool:
        """Register a new tool"""
        try:
            self._tools[tool.name] = tool
            if handler:
                self._handlers[tool.name] = handler
            
            if tool.name not in self._tool_metrics:
                self._tool_metrics[tool.name] = {
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_execution_time": 0.0,
                    "last_executed": None
                }
            
            logger.info(f"Registered tool: {tool.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool"""
        try:
            self._tools.pop(tool_name, None)
            self._handlers.pop(tool_name, None)
            self._tool_metrics.pop(tool_name, None)
            
            logger.info(f"Unregistered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_name}: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[MCPToolSchema]:
        """Get tool by name"""
        return self._tools.get(tool_name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[MCPToolSchema]:
        """Get tools by type"""
        return [tool for tool in self._tools.values() if tool.tool_type == tool_type]
    
    def get_tools(self) -> Dict[str, MCPToolSchema]:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_tool_names(self) -> Set[str]:
        """Get all tool names"""
        return set(self._tools.keys())
    
    def search_tools(self, query: str, tool_type: Optional[ToolType] = None) -> List[MCPToolSchema]:
        """Search tools by query"""
        query_lower = query.lower()
        results = []
        
        for tool in self._tools.values():
            if tool_type and tool.tool_type != tool_type:
                continue
            
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                results.append(tool)
        
        return results
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool"""
        execution_id = f"{tool_name}_{datetime.utcnow().timestamp()}"
        start_time = datetime.utcnow()
        
        result = ToolExecutionResult(
            tool_name=tool_name,
            execution_id=execution_id,
            status=ToolStatus.RUNNING,
            started_at=start_time
        )
        
        try:
            # Validate tool exists
            if tool_name not in self._tools:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            # Validate parameters
            tool = self._tools[tool_name]
            for required_param in tool.required_parameters:
                if required_param not in parameters:
                    raise ValueError(f"Missing required parameter: {required_param}")
            
            # Get handler
            handler = self._handlers.get(tool_name)
            if not handler:
                raise ValueError(f"No handler found for tool '{tool_name}'")
            
            # Execute tool
            if asyncio.iscoroutinefunction(handler):
                tool_result = await handler(**parameters)
            else:
                tool_result = handler(**parameters)
            
            # Update result
            result.status = ToolStatus.COMPLETED
            result.result = tool_result
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - start_time).total_seconds()
            
            # Update metrics
            self._update_metrics(tool_name, True, result.execution_time)
            
        except Exception as e:
            result.status = ToolStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - start_time).total_seconds()
            
            # Update metrics
            self._update_metrics(tool_name, False, result.execution_time)
            
            logger.error(f"Tool execution failed for {tool_name}: {e}")
        
        # Store execution history
        self._execution_history.append(result)
        
        return result
    
    def _update_metrics(self, tool_name: str, success: bool, execution_time: float):
        """Update tool metrics"""
        if tool_name in self._tool_metrics:
            metrics = self._tool_metrics[tool_name]
            metrics["executions"] += 1
            
            if success:
                metrics["successes"] += 1
            else:
                metrics["failures"] += 1
            
            # Update average execution time
            current_avg = metrics["avg_execution_time"]
            total_executions = metrics["executions"]
            metrics["avg_execution_time"] = (current_avg * (total_executions - 1) + execution_time) / total_executions
            
            metrics["last_executed"] = datetime.utcnow()
    
    def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get tool metrics"""
        if tool_name:
            return self._tool_metrics.get(tool_name, {})
        return self._tool_metrics.copy()
    
    def get_execution_history(self, tool_name: Optional[str] = None, limit: int = 100) -> List[ToolExecutionResult]:
        """Get execution history"""
        history = self._execution_history
        
        if tool_name:
            history = [result for result in history if result.tool_name == tool_name]
        
        return history[-limit:] if limit else history


# Global tool registry
tool_registry = ToolRegistry()


async def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry"""
    if not tool_registry._initialized:
        await tool_registry.initialize()
    return tool_registry


def get_registry_status() -> Dict[str, Any]:
    """Get registry status"""
    return {
        "initialized": tool_registry._initialized,
        "tool_count": len(tool_registry._tools),
        "handler_count": len(tool_registry._handlers),
        "execution_count": len(tool_registry._execution_history)
    }
