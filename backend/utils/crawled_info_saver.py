import json
import os
import warnings
from datetime import datetime, timezone

import chromadb
import torch
from pymongo.errors import PyMongoError
from sentence_transformers import SentenceTransformer

# Suppress specific deprecation warnings from transformers/sentence-transformers
warnings.filterwarnings(
    "ignore", message=".*encoder_attention_mask.*deprecated.*", category=FutureWarning
)

from agents.ollama_api import OllamaQwen3Client
from db.mongo import db
from services.web_scraper import crawl_company_website_if_existing
from utils.logger import get_logger

logger = get_logger("crawled_info_saver")

# Initialize Ollama client for LLM processing
try:
    ollama_client = OllamaQwen3Client()
    logger.info("✅ Ollama client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Ollama client: {e}")
    ollama_client = None

def generate_text(prompt: str) -> str:
    """Generate text using Ollama client"""
    if not ollama_client:
        logger.error("Ollama client not available")
        return ""
    
    try:
        response = ollama_client.generate(prompt, max_tokens=2000)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating text with Ollama: {e}")
        return ""

# Initialize Sentence Transformer model with GPU support
try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🔥 Initializing sentence transformer on device: {device}")

    # Load all-MiniLM-L6-v2 model - lightweight and fast
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

    # Check GPU availability and memory
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"✅ GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
    else:
        logger.info("⚠️ No GPU detected, using CPU for embeddings")

    logger.info("✅ Sentence transformer model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize sentence transformer: {e}")
    embedding_model = None

# Initialize ChromaDB client
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    logger.info("✅ ChromaDB client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize ChromaDB: {e}")
    chroma_client = None


async def generate_embedding(text: str, model: str = "all-MiniLM-L6-v2") -> list:
    """
    Generate embeddings using local sentence transformer model with GPU acceleration.

    Args:
        text (str): Text to generate embedding for
        model (str): Model name (ignored, uses pre-loaded all-MiniLM-L6-v2)

    Returns:
        list: Embedding vector or None if failed
    """
    try:
        if not embedding_model:
            logger.error("Sentence transformer model not initialized")
            return None

        if not text or not isinstance(text, str):
            logger.warning("Invalid text for embedding generation")
            return None

        # Clean and truncate text if too long (sentence transformers can handle up to 512 tokens typically)
        text = text.strip()
        if len(text) > 20000:  # Conservative estimate for token limits
            text = text[:20000] + "..."
            logger.warning("Text truncated for embedding generation")

        # Generate embedding using sentence transformer
        # encode() returns numpy array, convert to list
        embedding = embedding_model.encode(
            text, convert_to_tensor=False, show_progress_bar=False
        )
        embedding_list = embedding.tolist()

        logger.info(
            f"✅ Generated local embedding with {len(embedding_list)} dimensions"
        )
        return embedding_list

    except Exception as e:
        logger.error(f"❌ Failed to generate local embedding: {e}")
        return None


def get_embedding_model_info() -> dict:
    """
    Get information about the current embedding model.

    Returns:
        dict: Model information including device, dimensions, etc.
    """
    try:
        if not embedding_model:
            return {"success": False, "error": "Model not initialized"}

        # Get device info
        device_info = str(embedding_model.device)

        # Get model dimensions by encoding a test string
        test_embedding = embedding_model.encode("test", convert_to_tensor=False)
        dimensions = len(test_embedding)

        # GPU info if available
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "gpu_available": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB",
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}GB",
                "gpu_memory_cached": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}GB",
            }
        else:
            gpu_info = {"gpu_available": False}

        return {
            "success": True,
            "model_name": "all-MiniLM-L6-v2",
            "device": device_info,
            "embedding_dimensions": dimensions,
            "model_type": "sentence-transformer",
            "gpu_info": gpu_info,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def generate_embeddings_batch(texts: list) -> list:
    """
    Generate embeddings for multiple texts in batch for better performance.

    Args:
        texts (list): List of texts to generate embeddings for

    Returns:
        list: List of embedding vectors or None if failed
    """
    try:
        if not embedding_model:
            logger.error("Sentence transformer model not initialized")
            return None

        if not texts or not isinstance(texts, list):
            logger.warning("Invalid texts for batch embedding generation")
            return None

        # Clean and truncate texts
        cleaned_texts = []
        for text in texts:
            if text and isinstance(text, str):
                text = text.strip()
                if len(text) > 20000:
                    text = text[:20000] + "..."
                cleaned_texts.append(text)
            else:
                cleaned_texts.append("")

        # Generate embeddings in batch
        embeddings = embedding_model.encode(
            cleaned_texts,
            convert_to_tensor=False,
            show_progress_bar=True,
            batch_size=32,  # Adjust based on GPU memory
        )

        # Convert to list of lists
        embeddings_list = [emb.tolist() for emb in embeddings]

        logger.info(f"✅ Generated {len(embeddings_list)} local embeddings in batch")
        return embeddings_list

    except Exception as e:
        logger.error(f"❌ Failed to generate batch embeddings: {e}")
        return None


def get_or_create_chroma_collection(collection_name: str = "opportunities"):
    """
    Get or create a ChromaDB collection.

    Args:
        collection_name (str): Name of the collection

    Returns:
        Collection object or None if failed
    """
    try:
        if not chroma_client:
            logger.error("ChromaDB client not initialized")
            return None

        # Try to get existing collection or create new one
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Company opportunities and business summaries"},
        )

        logger.info(f"✅ ChromaDB collection '{collection_name}' ready")
        return collection

    except Exception as e:
        logger.error(
            f"❌ Failed to get/create ChromaDB collection '{collection_name}': {e}"
        )
        return None


async def store_embedding_in_chroma(
    collection,
    mongo_id: str,
    summary: str,
    embedding: list,
    company_name: str,
    sector: str = None,
    region: str = None,
    services: str = None,
) -> dict:
    """
    Store embedding and metadata in ChromaDB.

    Args:
        collection: ChromaDB collection object
        mongo_id (str): MongoDB document ID
        summary (str): Business summary text
        embedding (list): Embedding vector
        company_name (str): Company name
        sector (str): Business sector/domain
        region (str): Company region
        services (str): Main services offered

    Returns:
        dict: Result of the storage operation
    """
    try:
        if not collection or not embedding:
            return {"success": False, "error": "Invalid collection or embedding"}

        # Prepare metadata
        metadata = {
            "company_name": company_name,
            "mongo_id": mongo_id,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        if sector:
            metadata["sector"] = sector
        if region:
            metadata["region"] = region
        if services:
            metadata["services"] = services

        # Store in ChromaDB
        collection.add(
            ids=[mongo_id],
            embeddings=[embedding],
            documents=[summary],
            metadatas=[metadata],
        )

        logger.info(
            f"✅ Stored embedding in ChromaDB for: {company_name} (ID: {mongo_id})"
        )
        return {
            "success": True,
            "chroma_id": mongo_id,
            "company_name": company_name,
            "embedding_dimensions": len(embedding),
        }

    except Exception as e:
        logger.error(f"❌ Failed to store embedding in ChromaDB: {e}")
        return {"success": False, "error": str(e)}


async def save_crawled_info_to_db(data, crawled_info):
    """
    Save or update crawled info to MongoDB with proper validation, error handling, upsert functionality,
    and automatic embedding generation and ChromaDB storage.

    Args:
        data (dict): Company data containing URLs, company name, business domain
        crawled_info (dict): Crawled website information to be saved

    Returns:
        dict: Result of the save operation with success status, MongoDB details, and embedding results
    """
    mongo_result = None
    embedding_result = None
    chroma_result = None

    try:
        # Validate inputs
        if not isinstance(data, dict):
            logger.error("Invalid data parameter: expected dict")
            return {"success": False, "error": "Invalid data parameter"}

        if not isinstance(crawled_info, dict):
            logger.error("Invalid crawled_info parameter: expected dict")
            return {"success": False, "error": "Invalid crawled_info parameter"}

        # Extract and validate required fields
        company_name = data.get("company_name")
        if not company_name:
            logger.error("Missing required field: company_name")
            return {"success": False, "error": "Missing company_name"}

        # Extract URL with better validation
        urls = data.get("urls", [])
        if isinstance(urls, list) and urls:
            url = urls[0]
        elif isinstance(urls, str):
            url = urls
        else:
            url = "N/A"

        # Validate URL format if provided
        if url != "N/A" and not (
            url.startswith("http://") or url.startswith("https://")
        ):
            logger.warning(f"Invalid URL format for {company_name}: {url}")

        current_time = datetime.now(timezone.utc)

        # Prepare document with comprehensive data
        doc = {
            "url": url,
            "company_name": company_name,
            "domain": data.get("business_domain", "N/A"),
            "region": data.get("region_or_market", "N/A"),
            "updated_at": current_time,
            "crawled_info": crawled_info,
            "data_size": len(str(crawled_info)),  # Track data size for monitoring
            "crawled_info_keys": (
                list(crawled_info.keys()) if crawled_info else []
            ),  # Track structure
        }

        collection = db.crawled_infos

        # Check if document already exists (upsert logic)
        existing_doc = await collection.find_one(
            {"company_name": company_name, "url": url}
        )

        mongo_id = None
        action = None

        if existing_doc:
            # Update existing document
            doc["created_at"] = existing_doc.get("created_at", current_time)
            doc["update_count"] = existing_doc.get("update_count", 0) + 1

            result = await collection.replace_one({"_id": existing_doc["_id"]}, doc)
            mongo_id = str(existing_doc["_id"])
            action = "updated"

            mongo_result = {
                "success": True,
                "action": action,
                "company_name": company_name,
                "url": url,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "update_count": doc["update_count"],
                "mongo_id": mongo_id,
            }

            logger.info(
                f"✅ Updated crawled info for: {company_name} | "
                f"domain: {doc['domain']} | url: {url} | "
                f"updates: {doc['update_count']} | data_size: {doc['data_size']} bytes"
            )
        else:
            # Insert new document
            doc["created_at"] = current_time
            doc["update_count"] = 0

            result = await collection.insert_one(doc)
            mongo_id = str(result.inserted_id)
            action = "created"

            mongo_result = {
                "success": True,
                "action": action,
                "company_name": company_name,
                "url": url,
                "inserted_id": mongo_id,
                "update_count": 0,
                "mongo_id": mongo_id,
            }

            logger.info(
                f"✅ Saved new crawled info for: {company_name} | "
                f"domain: {doc['domain']} | url: {url} | "
                f"data_size: {doc['data_size']} bytes"
            )

        # Generate embeddings from crawled_info
        try:
            # Extract meaningful text from crawled_info for embedding
            summary_text = None

            if isinstance(crawled_info, dict):
                # Build comprehensive summary from crawled info
                summary_parts = []

                # Priority fields for summary extraction
                priority_fields = [
                    "business_offerings",
                    "target_markets",
                    "competitive_positioning",
                    "company_overview",
                    "services",
                    "products",
                    "description",
                    "about",
                    "summary",
                ]

                # Extract from priority fields
                for field in priority_fields:
                    if field in crawled_info and crawled_info[field]:
                        value = crawled_info[field]
                        if isinstance(value, list):
                            if value:  # Non-empty list
                                summary_parts.append(
                                    f"{field.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}"
                                )
                        elif isinstance(value, str) and value.strip():
                            summary_parts.append(
                                f"{field.replace('_', ' ').title()}: {value}"
                            )
                        elif isinstance(value, dict):
                            # Convert dict to readable string
                            dict_str = ", ".join(
                                [f"{k}: {v}" for k, v in value.items() if v]
                            )
                            if dict_str:
                                summary_parts.append(
                                    f"{field.replace('_', ' ').title()}: {dict_str}"
                                )

                # If we have structured parts, combine them
                if summary_parts:
                    summary_text = ". ".join(summary_parts)
                    logger.info(
                        f"Extracted structured summary with {len(summary_parts)} components for {company_name}"
                    )
                else:
                    # Fallback: look for any text content in crawled_info
                    text_content = []

                    def extract_text_recursive(obj, depth=0):
                        if depth > 3:  # Prevent deep recursion
                            return

                        if isinstance(obj, str) and len(obj.strip()) > 10:
                            text_content.append(obj.strip())
                        elif isinstance(obj, list):
                            for item in obj[:10]:  # Limit list items
                                extract_text_recursive(item, depth + 1)
                        elif isinstance(obj, dict):
                            for value in list(obj.values())[:10]:  # Limit dict values
                                extract_text_recursive(value, depth + 1)

                    extract_text_recursive(crawled_info)

                    if text_content:
                        # Join and truncate text content
                        summary_text = ". ".join(
                            text_content[:5]
                        )  # Limit to first 5 text pieces
                        if len(summary_text) > 1000:
                            summary_text = summary_text[:1000] + "..."
                        logger.info(
                            f"Extracted text content summary for {company_name}"
                        )
                    else:
                        # Ultimate fallback: use JSON string
                        summary_text = json.dumps(crawled_info, ensure_ascii=False)[
                            :1000
                        ]
                        logger.warning(
                            f"Using JSON fallback summary for {company_name}"
                        )

            elif isinstance(crawled_info, str):
                summary_text = crawled_info
            else:
                summary_text = str(crawled_info)

            # Generate embedding if we have valid text
            if summary_text and len(summary_text.strip()) > 0:
                logger.info(f"Generating embedding for crawled info: {company_name}")
                embedding = await generate_embedding(summary_text)

                if embedding:
                    embedding_result = {
                        "success": True,
                        "embedding_dimensions": len(embedding),
                    }

                    # Get ChromaDB collection for crawled_infos
                    chroma_collection = get_or_create_chroma_collection("crawled_infos")

                    if chroma_collection:
                        # Extract metadata for ChromaDB
                        sector = doc.get("domain", "N/A")
                        region = doc.get("region", "N/A")

                        # Try to extract services from crawled_info
                        services = None
                        service_fields = [
                            "business_offerings",
                            "services",
                            "products",
                            "offerings",
                        ]
                        for field in service_fields:
                            if isinstance(crawled_info, dict) and crawled_info.get(
                                field
                            ):
                                services_data = crawled_info[field]
                                if isinstance(services_data, list):
                                    services = ", ".join(
                                        str(s) for s in services_data[:3]
                                    )  # Limit to first 3
                                elif isinstance(services_data, str):
                                    services = services_data[
                                        :200
                                    ]  # Truncate if too long
                                break

                        # Store in ChromaDB with metadata
                        chroma_result = await store_embedding_in_chroma(
                            collection=chroma_collection,
                            mongo_id=mongo_id,
                            summary=summary_text,
                            embedding=embedding,
                            company_name=company_name,
                            sector=sector,
                            region=region,
                            services=services,
                        )

                        if chroma_result.get("success"):
                            logger.info(
                                f"✅ Stored crawled info embedding in ChromaDB for: {company_name}"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Failed to store embedding in ChromaDB for: {company_name}"
                            )
                    else:
                        chroma_result = {
                            "success": False,
                            "error": "ChromaDB collection not available",
                        }
                        logger.warning(
                            f"ChromaDB collection not available for {company_name}"
                        )
                else:
                    embedding_result = {
                        "success": False,
                        "error": "Failed to generate embedding",
                    }
                    logger.warning(
                        f"Failed to generate embedding for crawled info: {company_name}"
                    )
            else:
                embedding_result = {
                    "success": False,
                    "error": "No valid text content found for embedding",
                }
                logger.warning(
                    f"No valid text content found for embedding: {company_name}"
                )

        except Exception as e:
            embedding_result = {
                "success": False,
                "error": f"Embedding generation failed: {str(e)}",
            }
            logger.error(
                f"❌ Error generating embedding for crawled info {company_name}: {e}"
            )

        # Compile comprehensive result
        final_result = {
            "success": True,
            "company_name": company_name,
            "url": url,
            "mongo_id": mongo_id,
            "action": action,
            "mongo_operation": mongo_result,
            "embedding_operation": embedding_result,
            "chroma_operation": chroma_result,
        }

        # Log overall pipeline status
        if (
            embedding_result
            and embedding_result.get("success")
            and chroma_result
            and chroma_result.get("success")
        ):
            logger.info(
                f"✅ Complete crawled info pipeline success for {company_name}: MongoDB + Embedding + ChromaDB"
            )
        elif embedding_result and not embedding_result.get("success"):
            logger.warning(
                f"⚠️ Partial crawled info success for {company_name}: MongoDB ✅, Embedding ❌, ChromaDB skipped"
            )
        elif chroma_result and not chroma_result.get("success"):
            logger.warning(
                f"⚠️ Partial crawled info success for {company_name}: MongoDB ✅, Embedding ✅, ChromaDB ❌"
            )

        return final_result

    except Exception as e:
        error_msg = f"Error saving crawled info for {data.get('company_name', 'unknown')}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "company_name": data.get("company_name", "unknown"),
            "mongo_operation": {"success": False, "error": str(e)},
            "embedding_operation": None,
            "chroma_operation": None,
        }


def save_crawled_info_to_db_sync(data, crawled_info):
    """
    Synchronous wrapper for backward compatibility.
    Note: This should be phased out in favor of the async version.
    """
    import asyncio

    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.warning(
                "Cannot run async operation in sync context with running loop. Use async version instead."
            )
            return {
                "success": False,
                "error": "Async operation not supported in this context",
            }
        else:
            return loop.run_until_complete(save_crawled_info_to_db(data, crawled_info))
    except RuntimeError:
        # No event loop exists, create new one
        return asyncio.run(save_crawled_info_to_db(data, crawled_info))


async def crawl_and_filter_company_info(data):
    """
    Centralized logic for crawling company website and filtering with Gemini LLM.
    Enhanced with better error handling, logging, and data validation.

    Args:
        data (dict): Company data containing URLs and company information

    Returns:
        dict: Filtered crawled info, raw crawled info, or error information
    """
    website_crawled_info = None
    filtered_crawled_info = None

    try:
        company_name = data.get("company_name", "Unknown Company")
        logger.info(f"Starting crawl and filter process for: {company_name}")

        # Attempt to crawl website
        crawled_path = crawl_company_website_if_existing({"data": data})

        if not crawled_path:
            logger.warning(f"No crawled data path returned for: {company_name}")
            return {
                "error": "No website data could be crawled",
                "company_name": company_name,
            }

        if not crawled_path or not isinstance(crawled_path, str):
            logger.warning(f"Invalid crawled path for: {company_name}")
            return {"error": "Invalid crawled data path", "company_name": company_name}

        # Load crawled data from file
        try:
            with open(crawled_path, "r", encoding="utf-8") as f:
                website_crawled_info = json.load(f)

            if not website_crawled_info:
                logger.warning(f"Empty crawled data for: {company_name}")
                return {"error": "Empty crawled data", "company_name": company_name}

            logger.info(
                f"Successfully loaded crawled data for: {company_name} ({len(str(website_crawled_info))} bytes)"
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {company_name}: {e}")
            return {
                "error": f"Invalid JSON in crawled data: {str(e)}",
                "company_name": company_name,
            }
        except FileNotFoundError as e:
            logger.error(f"Crawled file not found for {company_name}: {e}")
            return {
                "error": f"Crawled file not found: {str(e)}",
                "company_name": company_name,
            }
        except Exception as e:
            logger.error(f"Error reading crawled file for {company_name}: {e}")
            return {
                "error": f"Error reading crawled data: {str(e)}",
                "company_name": company_name,
            }

        # Apply LLM filtering
        try:
            filter_prompt = (
                "You are a market intelligence agent specializing in opportunity detection and gap analysis.\n\n"
                "From the following crawled website data, extract only strategic, high-signal insights that support:\n"
                "1. Opportunity detection – e.g., unique offerings, unmet needs, underserved markets, innovation patterns\n"
                "2. Gap analysis – e.g., missing services, technologies, weak positioning, or market absences\n\n"
                "Use semantic reasoning — do not rely only on keywords.\n\n"
                "Respond in **valid JSON format only**. No explanations, no preamble, no markdown.\n\n"
                "Include the following keys when relevant:\n"
                '- "business_offerings": []\n'
                '- "target_markets": []\n'
                '- "strategic_partnerships": []\n'
                '- "competitive_positioning": []\n'
                '- "emerging_opportunities": []\n'
                '- "gaps_or_omissions": []\n\n'
                "You may also include **additional fields** that you judge relevant to strategic opportunity detection, such as:\n"
                '- "technologies_used": []\n'
                '- "customer_segments": []\n'
                '- "regulatory_mentions": []\n'
                '- "sustainability_focus": []\n'
                '- "recent_initiatives": []\n\n'
                "Omit empty fields. Output must be a single, syntactically correct JSON object only.\n\n"
                f"Website Data:\n{json.dumps(website_crawled_info)}"
            )

            logger.info(f"Applying LLM filtering for: {company_name}")
            filtered_text = generate_text(filter_prompt)

            if not filtered_text:
                logger.warning(f"Empty LLM response for: {company_name}")
                return website_crawled_info

            # Clean and parse LLM response
            cleaned_text = (
                filtered_text.replace("```json", "").replace("```", "").strip()
            )

            try:
                filtered_crawled_info = json.loads(cleaned_text)
                logger.info(f"Successfully filtered crawled data for: {company_name}")

                # Add metadata about the filtering process
                filtered_crawled_info["_metadata"] = {
                    "company_name": company_name,
                    "filtering_applied": True,
                    "original_data_size": len(str(website_crawled_info)),
                    "filtered_data_size": len(str(filtered_crawled_info)),
                    "filtered_at": datetime.now(timezone.utc).isoformat(),
                }

            except json.JSONDecodeError as e:
                logger.warning(
                    f"LLM response is not valid JSON for {company_name}: {e}"
                )
                # Return raw LLM text as fallback
                filtered_crawled_info = {
                    "raw_llm_response": filtered_text,
                    "parse_error": str(e),
                    "_metadata": {
                        "company_name": company_name,
                        "filtering_applied": False,
                        "error": "JSON parse error",
                    },
                }

        except Exception as e:
            logger.error(f"Error during LLM filtering for {company_name}: {e}")
            # Return original crawled data if filtering fails
            return {
                **website_crawled_info,
                "_metadata": {
                    "company_name": company_name,
                    "filtering_applied": False,
                    "filtering_error": str(e),
                },
            }

        # Return filtered data or original data as fallback
        return filtered_crawled_info if filtered_crawled_info else website_crawled_info

    except Exception as e:
        logger.error(
            f"Unexpected error in crawl_and_filter_company_info for {data.get('company_name', 'unknown')}: {e}"
        )
        return {
            "error": f"Unexpected error: {str(e)}",
            "company_name": data.get("company_name", "unknown"),
        }


async def bulk_save_crawled_info(companies_data_list):
    """
    Save multiple crawled company info records efficiently.

    Args:
        companies_data_list (list): List of (data, crawled_info) tuples

    Returns:
        dict: Summary of bulk save operation
    """
    if not companies_data_list or not isinstance(companies_data_list, list):
        logger.error("Invalid companies_data_list: expected non-empty list")
        return {"success": False, "error": "Invalid input"}

    results = {
        "total": len(companies_data_list),
        "successful": 0,
        "failed": 0,
        "updated": 0,
        "created": 0,
        "errors": [],
    }

    logger.info(f"Starting bulk save for {results['total']} companies")

    for i, (data, crawled_info) in enumerate(companies_data_list):
        try:
            result = await save_crawled_info_to_db(data, crawled_info)

            if result.get("success"):
                results["successful"] += 1
                if result.get("action") == "updated":
                    results["updated"] += 1
                elif result.get("action") == "created":
                    results["created"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "index": i,
                        "company": data.get("company_name", "unknown"),
                        "error": result.get("error", "unknown error"),
                    }
                )

        except Exception as e:
            results["failed"] += 1
            results["errors"].append(
                {
                    "index": i,
                    "company": data.get("company_name", "unknown"),
                    "error": str(e),
                }
            )
            logger.error(f"Error in bulk save for company {i}: {e}")

    logger.info(
        f"Bulk save completed: {results['successful']}/{results['total']} successful "
        f"({results['created']} created, {results['updated']} updated, {results['failed']} failed)"
    )

    return results


async def save_crawled_company(
    company_name: str, business_summary: dict, website_url: str = None
):
    """
    Save or update crawled company business summary to the crawled_company collection,
    then generate embeddings and store in ChromaDB.

    Args:
        company_name (str): Name of the company
        business_summary (dict): Business summary data from crawling
        website_url (str, optional): Company website URL

    Returns:
        dict: Result of the save operation including embedding and ChromaDB status
    """
    mongo_result = None
    embedding_result = None
    chroma_result = None

    try:
        collection = db["crawled_company"]
        current_time = datetime.now(timezone.utc)

        # Prepare the document
        document = {
            "company_name": company_name,
            "business_summary": business_summary,
            "website_url": website_url,
            "updated_at": current_time,
        }

        # Check if company already exists
        existing_company = await collection.find_one({"company_name": company_name})

        mongo_id = None
        action = None

        if existing_company:
            # Update existing document
            document["created_at"] = existing_company.get("created_at", current_time)
            result = await collection.replace_one(
                {"company_name": company_name}, document
            )
            mongo_id = str(existing_company["_id"])
            action = "updated"

            mongo_result = {
                "success": True,
                "action": action,
                "company_name": company_name,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "mongo_id": mongo_id,
            }
            logger.info(f"✅ Updated crawled company data for: {company_name}")
        else:
            # Insert new document
            document["created_at"] = current_time
            result = await collection.insert_one(document)
            mongo_id = str(result.inserted_id)
            action = "created"

            mongo_result = {
                "success": True,
                "action": action,
                "company_name": company_name,
                "inserted_id": mongo_id,
                "mongo_id": mongo_id,
            }
            logger.info(f"✅ Saved new crawled company data for: {company_name}")

        # Extract summary for embedding generation
        summary_text = None
        try:
            # Try to extract summary from business_summary
            if isinstance(business_summary, dict):
                # Build a comprehensive summary from structured data
                summary_parts = []

                # Company overview (highest priority)
                if business_summary.get("company_overview"):
                    summary_parts.append(
                        f"Company Overview: {business_summary['company_overview']}"
                    )

                # Main products and services
                if business_summary.get("main_products_services"):
                    services = business_summary["main_products_services"]
                    if isinstance(services, list):
                        summary_parts.append(f"Services: {', '.join(services)}")
                    else:
                        summary_parts.append(f"Services: {services}")

                # Target markets
                if business_summary.get("target_markets"):
                    markets = business_summary["target_markets"]
                    if isinstance(markets, list):
                        summary_parts.append(f"Target Markets: {', '.join(markets)}")
                    else:
                        summary_parts.append(f"Target Markets: {markets}")

                # Business model
                if business_summary.get("business_model"):
                    summary_parts.append(
                        f"Business Model: {business_summary['business_model']}"
                    )

                # Competitive advantages
                if business_summary.get("competitive_advantages"):
                    advantages = business_summary["competitive_advantages"]
                    if isinstance(advantages, list):
                        summary_parts.append(
                            f"Competitive Advantages: {', '.join(advantages)}"
                        )
                    else:
                        summary_parts.append(f"Competitive Advantages: {advantages}")

                # Geographic presence
                if business_summary.get("geographic_presence"):
                    presence = business_summary["geographic_presence"]
                    if isinstance(presence, list):
                        summary_parts.append(
                            f"Geographic Presence: {', '.join(presence)}"
                        )
                    else:
                        summary_parts.append(f"Geographic Presence: {presence}")

                # Key technologies
                if (
                    business_summary.get("key_technologies")
                    and business_summary["key_technologies"]
                ):
                    technologies = business_summary["key_technologies"]
                    if isinstance(technologies, list):
                        summary_parts.append(f"Technologies: {', '.join(technologies)}")
                    else:
                        summary_parts.append(f"Technologies: {technologies}")

                # Recent developments
                if business_summary.get("recent_developments"):
                    developments = business_summary["recent_developments"]
                    if isinstance(developments, list):
                        summary_parts.append(
                            f"Recent Developments: {'; '.join(developments)}"
                        )
                    else:
                        summary_parts.append(f"Recent Developments: {developments}")

                # Partnerships
                if business_summary.get("partnerships"):
                    partnerships = business_summary["partnerships"]
                    if isinstance(partnerships, list):
                        summary_parts.append(
                            f"Key Partnerships: {', '.join(partnerships)}"
                        )
                    else:
                        summary_parts.append(f"Key Partnerships: {partnerships}")

                # Combine all parts into a comprehensive summary
                if summary_parts:
                    summary_text = ". ".join(summary_parts)
                    logger.info(
                        f"Constructed structured summary with {len(summary_parts)} components for {company_name}"
                    )
                else:
                    # Fallback: look for legacy summary fields
                    summary_fields = [
                        "summary",
                        "business_summary",
                        "description",
                        "overview",
                    ]
                    for field in summary_fields:
                        if field in business_summary and business_summary[field]:
                            if isinstance(business_summary[field], str):
                                summary_text = business_summary[field]
                                break
                            elif isinstance(business_summary[field], dict):
                                summary_text = str(business_summary[field])
                                break

                    # Ultimate fallback: use entire business_summary as JSON string
                    if not summary_text:
                        summary_text = json.dumps(business_summary, ensure_ascii=False)
                        logger.warning(f"Using full JSON as summary for {company_name}")

            elif isinstance(business_summary, str):
                summary_text = business_summary
            else:
                summary_text = str(business_summary)

        except Exception as e:
            logger.warning(f"Could not extract summary text for {company_name}: {e}")
            summary_text = str(business_summary)

        # Generate embedding and store in ChromaDB
        if summary_text and len(summary_text.strip()) > 0:
            try:
                logger.info(f"Generating embedding for: {company_name}")
                embedding = await generate_embedding(summary_text)

                if embedding:
                    embedding_result = {
                        "success": True,
                        "embedding_dimensions": len(embedding),
                    }

                    # Get ChromaDB collection
                    chroma_collection = get_or_create_chroma_collection(
                        "crawled_companies"
                    )

                    if chroma_collection:
                        # Extract metadata from business_summary
                        sector = None
                        region = None
                        services = None

                        if isinstance(business_summary, dict):
                            # Extract sector/domain information - improved for structured format
                            sector_sources = [
                                (
                                    "target_markets",
                                    lambda x: (
                                        x[0]
                                        if isinstance(x, list) and x
                                        else str(x) if x else None
                                    ),
                                ),
                                ("business_model", str),
                                ("sector", str),
                                ("domain", str),
                                ("business_domain", str),
                                ("industry", str),
                            ]

                            for field, converter in sector_sources:
                                if (
                                    field in business_summary
                                    and business_summary[field]
                                ):
                                    try:
                                        sector = converter(business_summary[field])
                                        if sector and sector.strip():
                                            break
                                    except Exception:
                                        continue

                            # Extract region information - improved for structured format
                            region_sources = [
                                (
                                    "geographic_presence",
                                    lambda x: (
                                        ", ".join(x) if isinstance(x, list) else str(x)
                                    ),
                                ),
                                ("region", str),
                                ("location", str),
                                ("market", str),
                                ("region_or_market", str),
                            ]

                            for field, converter in region_sources:
                                if (
                                    field in business_summary
                                    and business_summary[field]
                                ):
                                    try:
                                        region = converter(business_summary[field])
                                        if region and region.strip():
                                            break
                                    except Exception:
                                        continue

                            # Extract main services for additional metadata
                            if business_summary.get("main_products_services"):
                                services_data = business_summary[
                                    "main_products_services"
                                ]
                                if isinstance(services_data, list):
                                    services = ", ".join(
                                        services_data[:5]
                                    )  # Limit to first 5 services
                                else:
                                    services = str(services_data)

                        # Store in ChromaDB with enhanced metadata
                        chroma_result = await store_embedding_in_chroma(
                            collection=chroma_collection,
                            mongo_id=mongo_id,
                            summary=summary_text,
                            embedding=embedding,
                            company_name=company_name,
                            sector=sector,
                            region=region,
                            services=services,  # Add services as additional metadata
                        )
                    else:
                        chroma_result = {
                            "success": False,
                            "error": "ChromaDB collection not available",
                        }
                        logger.warning(
                            f"ChromaDB collection not available for {company_name}"
                        )
                else:
                    embedding_result = {
                        "success": False,
                        "error": "Failed to generate embedding",
                    }
                    logger.warning(f"Failed to generate embedding for {company_name}")

            except Exception as e:
                embedding_result = {
                    "success": False,
                    "error": f"Embedding generation failed: {str(e)}",
                }
                logger.error(f"❌ Error generating embedding for {company_name}: {e}")
        else:
            embedding_result = {
                "success": False,
                "error": "No valid summary text found",
            }
            logger.warning(
                f"No valid summary text found for embedding generation: {company_name}"
            )

        # Compile final result
        final_result = {
            "success": True,
            "company_name": company_name,
            "mongo_id": mongo_id,
            "action": action,
            "mongo_operation": mongo_result,
            "embedding_operation": embedding_result,
            "chroma_operation": chroma_result,
        }

        # Log overall success/failure status
        if (
            embedding_result
            and embedding_result.get("success")
            and chroma_result
            and chroma_result.get("success")
        ):
            logger.info(
                f"✅ Complete pipeline success for {company_name}: MongoDB + Embedding + ChromaDB"
            )
        elif embedding_result and not embedding_result.get("success"):
            logger.warning(
                f"⚠️ Partial success for {company_name}: MongoDB ✅, Embedding ❌, ChromaDB skipped"
            )
        elif chroma_result and not chroma_result.get("success"):
            logger.warning(
                f"⚠️ Partial success for {company_name}: MongoDB ✅, Embedding ✅, ChromaDB ❌"
            )

        return final_result

    except PyMongoError as e:
        logger.error(
            f"❌ MongoDB error saving crawled company data for {company_name}: {e}"
        )
        return {
            "success": False,
            "error": f"MongoDB error: {str(e)}",
            "company_name": company_name,
            "mongo_operation": {"success": False, "error": str(e)},
            "embedding_operation": None,
            "chroma_operation": None,
        }
    except Exception as e:
        logger.error(
            f"❌ Unexpected error saving crawled company data for {company_name}: {e}"
        )
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "company_name": company_name,
            "mongo_operation": {"success": False, "error": str(e)},
            "embedding_operation": None,
            "chroma_operation": None,
        }


async def test_embedding_pipeline(
    company_name: str = "Test Company",
    test_summary: str = "This is a test business summary for embedding generation.",
):
    """
    Test function to verify embedding generation and ChromaDB storage.

    Args:
        company_name (str): Test company name
        test_summary (str): Test summary text

    Returns:
        dict: Test results
    """
    logger.info(f"🧪 Testing embedding pipeline for: {company_name}")

    try:
        # Test embedding generation
        embedding = await generate_embedding(test_summary)
        if not embedding:
            return {"success": False, "error": "Embedding generation failed"}

        logger.info(f"✅ Test embedding generated: {len(embedding)} dimensions")

        # Test ChromaDB storage
        collection = get_or_create_chroma_collection("opportunities")
        if not collection:
            return {"success": False, "error": "ChromaDB collection creation failed"}

        # Use a test ID
        test_id = f"test_{company_name.lower().replace(' ', '_')}"

        chroma_result = await store_embedding_in_chroma(
            collection=collection,
            mongo_id=test_id,
            summary=test_summary,
            embedding=embedding,
            company_name=company_name,
            sector="Technology",
            region="Test Region",
            services="Software Development, AI Solutions",
        )

        if chroma_result.get("success"):
            logger.info(f"✅ Test embedding stored in ChromaDB successfully")

            # Test retrieval
            try:
                results = collection.get(ids=[test_id])
                if results and results["ids"]:
                    logger.info(
                        f"✅ Test embedding retrieved successfully from ChromaDB"
                    )
                    return {
                        "success": True,
                        "embedding_dimensions": len(embedding),
                        "chroma_id": test_id,
                        "retrieved": True,
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to retrieve test embedding",
                    }
            except Exception as e:
                return {"success": False, "error": f"Retrieval test failed: {str(e)}"}
        else:
            return {
                "success": False,
                "error": f"ChromaDB storage failed: {chroma_result.get('error')}",
            }

    except Exception as e:
        logger.error(f"❌ Test embedding pipeline failed: {e}")
        return {"success": False, "error": str(e)}


async def query_similar_companies(
    query_text: str, n_results: int = 5, collection_name: str = "opportunities"
) -> dict:
    """
    Query ChromaDB for similar companies based on text similarity.

    Args:
        query_text (str): Text to search for similar companies
        n_results (int): Number of results to return
        collection_name (str): ChromaDB collection name

    Returns:
        dict: Query results with similar companies
    """
    try:
        # Generate embedding for query text
        query_embedding = await generate_embedding(query_text)
        if not query_embedding:
            return {"success": False, "error": "Failed to generate query embedding"}

        # Get ChromaDB collection
        collection = get_or_create_chroma_collection(collection_name)
        if not collection:
            return {"success": False, "error": "ChromaDB collection not available"}

        # Query for similar embeddings
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("ids") or not results["ids"][0]:
            return {
                "success": True,
                "results": [],
                "message": "No similar companies found",
            }

        # Format results
        similar_companies = []
        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, company_id in enumerate(ids):
            company_data = {
                "mongo_id": company_id,
                "company_name": (
                    metadatas[i].get("company_name", "Unknown")
                    if i < len(metadatas)
                    else "Unknown"
                ),
                "sector": (
                    metadatas[i].get("sector", "N/A") if i < len(metadatas) else "N/A"
                ),
                "region": (
                    metadatas[i].get("region", "N/A") if i < len(metadatas) else "N/A"
                ),
                "services": (
                    metadatas[i].get("services", "N/A") if i < len(metadatas) else "N/A"
                ),
                "similarity_score": (
                    1 - distances[i] if i < len(distances) else 0
                ),  # Convert distance to similarity
                "summary": documents[i] if i < len(documents) else "N/A",
            }
            similar_companies.append(company_data)

        logger.info(
            f"✅ Found {len(similar_companies)} similar companies for query: '{query_text[:50]}...'"
        )

        return {
            "success": True,
            "query": query_text,
            "results": similar_companies,
            "total_found": len(similar_companies),
        }

    except Exception as e:
        logger.error(f"❌ Error querying similar companies: {e}")
        return {"success": False, "error": str(e)}


def get_collection_stats(collection_name: str = "opportunities") -> dict:
    """
    Get statistics about the ChromaDB collection.

    Args:
        collection_name (str): ChromaDB collection name

    Returns:
        dict: Collection statistics
    """
    try:
        collection = get_or_create_chroma_collection(collection_name)
        if not collection:
            return {"success": False, "error": "ChromaDB collection not available"}

        # Get collection count
        count = collection.count()

        # Get some sample records to analyze metadata
        sample_results = collection.peek(limit=min(10, count))

        # Analyze metadata for unique sectors and regions
        sectors = set()
        regions = set()

        if sample_results and sample_results.get("metadatas"):
            for metadata in sample_results["metadatas"]:
                if metadata.get("sector"):
                    sectors.add(metadata["sector"])
                if metadata.get("region"):
                    regions.add(metadata["region"])

        logger.info(f"✅ Retrieved stats for ChromaDB collection '{collection_name}'")

        return {
            "success": True,
            "collection_name": collection_name,
            "total_companies": count,
            "unique_sectors": list(sectors),
            "unique_regions": list(regions),
            "sample_companies": (
                sample_results.get("metadatas", [])[:5] if sample_results else []
            ),
        }

    except Exception as e:
        logger.error(f"❌ Error getting collection stats: {e}")
        return {"success": False, "error": str(e)}
