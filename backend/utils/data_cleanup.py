"""
Enhanced Data Cleanup Utility for MCP Backend
Comprehensive data cleaning, validation, and preprocessing system.
"""

import re
import html
import json
import unicodedata
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse, parse_qs
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

# Local imports
from .logger import MCPLogger


@dataclass
class CleaningRule:
    """Data cleaning rule configuration."""
    
    name: str
    field_pattern: str  # Regex pattern for field names
    cleaning_function: str  # Name of cleaning function
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Higher numbers execute first
    enabled: bool = True
    description: str = ""


@dataclass
class CleaningResult:
    """Result of data cleaning operation."""
    
    original_value: Any
    cleaned_value: Any
    rules_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def was_modified(self) -> bool:
        """Check if value was modified during cleaning."""
        return self.original_value != self.cleaned_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_value": str(self.original_value),
            "cleaned_value": str(self.cleaned_value),
            "was_modified": self.was_modified,
            "rules_applied": self.rules_applied,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata
        }


class MCPDataCleaner:
    """Comprehensive data cleaning system for MCP backend."""
    
    def __init__(self, logger: Optional[MCPLogger] = None):
        self.logger = logger or MCPLogger()
        self._cleaning_rules = []
        self._custom_functions = {}
        self._statistics = {
            "total_cleanings": 0,
            "fields_processed": 0,
            "modifications_made": 0,
            "errors_encountered": 0,
            "start_time": datetime.utcnow()
        }
        
        # Register default cleaning functions
        self._register_default_functions()
        
        # Default cleaning rules
        self._setup_default_rules()
    
    def _register_default_functions(self):
        """Register default cleaning functions."""
        self._custom_functions.update({
            "clean_text": self._clean_text,
            "clean_email": self._clean_email,
            "clean_url": self._clean_url,
            "clean_phone": self._clean_phone,
            "clean_numeric": self._clean_numeric,
            "clean_currency": self._clean_currency,
            "clean_date": self._clean_date,
            "clean_html": self._clean_html,
            "clean_whitespace": self._clean_whitespace,
            "normalize_case": self._normalize_case,
            "remove_duplicates": self._remove_duplicates,
            "validate_json": self._validate_json,
            "clean_social_media": self._clean_social_media,
            "clean_business_name": self._clean_business_name,
            "standardize_country": self._standardize_country,
            "clean_industry": self._clean_industry
        })
    
    def _setup_default_rules(self):
        """Setup default cleaning rules."""
        default_rules = [
            CleaningRule(
                name="html_cleanup",
                field_pattern=r".*description.*|.*content.*|.*text.*",
                cleaning_function="clean_html",
                priority=10,
                description="Remove HTML tags and decode entities"
            ),
            CleaningRule(
                name="whitespace_cleanup",
                field_pattern=r".*",
                cleaning_function="clean_whitespace",
                priority=9,
                description="Normalize whitespace characters"
            ),
            CleaningRule(
                name="email_validation",
                field_pattern=r".*email.*|.*contact.*",
                cleaning_function="clean_email",
                priority=8,
                description="Validate and normalize email addresses"
            ),
            CleaningRule(
                name="url_validation",
                field_pattern=r".*url.*|.*website.*|.*link.*",
                cleaning_function="clean_url",
                priority=8,
                description="Validate and normalize URLs"
            ),
            CleaningRule(
                name="phone_cleanup",
                field_pattern=r".*phone.*|.*tel.*|.*mobile.*",
                cleaning_function="clean_phone",
                priority=7,
                description="Normalize phone numbers"
            ),
            CleaningRule(
                name="currency_cleanup",
                field_pattern=r".*price.*|.*cost.*|.*revenue.*|.*salary.*",
                cleaning_function="clean_currency",
                priority=7,
                description="Clean and normalize currency values"
            ),
            CleaningRule(
                name="business_name_cleanup",
                field_pattern=r".*company.*|.*business.*|.*organization.*",
                cleaning_function="clean_business_name",
                priority=6,
                description="Standardize business names"
            ),
            CleaningRule(
                name="industry_standardization",
                field_pattern=r".*industry.*|.*sector.*|.*vertical.*",
                cleaning_function="clean_industry",
                priority=6,
                description="Standardize industry classifications"
            )
        ]
        
        for rule in default_rules:
            self.add_cleaning_rule(rule)
    
    def add_cleaning_rule(self, rule: CleaningRule):
        """Add a cleaning rule."""
        self._cleaning_rules.append(rule)
        self._cleaning_rules.sort(key=lambda r: r.priority, reverse=True)
        
        self.logger.debug(
            f"Added cleaning rule: {rule.name}",
            rule_name=rule.name,
            field_pattern=rule.field_pattern,
            priority=rule.priority
        )
    
    def register_custom_function(self, name: str, function: Callable):
        """Register a custom cleaning function."""
        self._custom_functions[name] = function
        self.logger.info(f"Registered custom cleaning function: {name}")
    
    def clean_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
        rules: Optional[List[str]] = None,
        return_metadata: bool = False
    ) -> Union[Any, Tuple[Any, Dict[str, Any]]]:
        """
        Clean data using configured rules.
        
        Args:
            data: Data to clean (dict, list of dicts, or DataFrame)
            rules: Specific rules to apply (None for all enabled rules)
            return_metadata: Whether to return cleaning metadata
            
        Returns:
            Cleaned data, optionally with metadata
        """
        start_time = datetime.utcnow()
        self._statistics["total_cleanings"] += 1
        
        metadata = {
            "cleaning_started": start_time.isoformat(),
            "rules_applied": [],
            "fields_processed": 0,
            "modifications_made": 0,
            "warnings": [],
            "errors": []
        }
        
        try:
            if isinstance(data, pd.DataFrame):
                cleaned_data, clean_metadata = self._clean_dataframe(data, rules)
            elif isinstance(data, list):
                cleaned_data, clean_metadata = self._clean_list(data, rules)
            elif isinstance(data, dict):
                cleaned_data, clean_metadata = self._clean_dict(data, rules)
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            # Merge metadata
            metadata.update(clean_metadata)
            metadata["cleaning_completed"] = datetime.utcnow().isoformat()
            metadata["processing_time"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Update statistics
            self._statistics["fields_processed"] += metadata["fields_processed"]
            self._statistics["modifications_made"] += metadata["modifications_made"]
            self._statistics["errors_encountered"] += len(metadata["errors"])
            
            self.logger.performance_log(
                "data_cleaning",
                metadata["processing_time"],
                metadata={
                    "fields_processed": metadata["fields_processed"],
                    "modifications_made": metadata["modifications_made"],
                    "data_type": type(data).__name__
                }
            )
            
            if return_metadata:
                return cleaned_data, metadata
            return cleaned_data
            
        except Exception as e:
            self.logger.error("Error during data cleaning", error=e)
            metadata["errors"].append(str(e))
            
            if return_metadata:
                return data, metadata
            return data
    
    def _clean_dataframe(self, df: pd.DataFrame, rules: Optional[List[str]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Clean pandas DataFrame."""
        cleaned_df = df.copy()
        metadata = {
            "rules_applied": [],
            "fields_processed": 0,
            "modifications_made": 0,
            "warnings": [],
            "errors": []
        }
        
        for column in df.columns:
            try:
                cleaned_series, col_metadata = self._clean_series(df[column], column, rules)
                cleaned_df[column] = cleaned_series
                
                metadata["fields_processed"] += 1
                metadata["rules_applied"].extend(col_metadata.get("rules_applied", []))
                metadata["warnings"].extend(col_metadata.get("warnings", []))
                metadata["errors"].extend(col_metadata.get("errors", []))
                
                if not cleaned_series.equals(df[column]):
                    metadata["modifications_made"] += 1
                    
            except Exception as e:
                metadata["errors"].append(f"Error cleaning column {column}: {str(e)}")
                self.logger.error(f"Error cleaning DataFrame column {column}", error=e)
        
        return cleaned_df, metadata
    
    def _clean_series(self, series: pd.Series, field_name: str, rules: Optional[List[str]]) -> Tuple[pd.Series, Dict[str, Any]]:
        """Clean pandas Series."""
        cleaned_series = series.copy()
        metadata = {
            "rules_applied": [],
            "warnings": [],
            "errors": []
        }
        
        applicable_rules = self._get_applicable_rules(field_name, rules)
        
        for rule in applicable_rules:
            try:
                cleaning_func = self._custom_functions.get(rule.cleaning_function)
                if not cleaning_func:
                    continue
                
                # Apply function to each non-null value
                for idx in series.index:
                    if pd.notna(series.iloc[idx]):
                        original_value = series.iloc[idx]
                        result = cleaning_func(original_value, **rule.parameters)
                        
                        if isinstance(result, CleaningResult):
                            cleaned_series.iloc[idx] = result.cleaned_value
                            metadata["warnings"].extend(result.warnings)
                            metadata["errors"].extend(result.errors)
                        else:
                            cleaned_series.iloc[idx] = result
                
                metadata["rules_applied"].append(rule.name)
                
            except Exception as e:
                metadata["errors"].append(f"Error applying rule {rule.name}: {str(e)}")
        
        return cleaned_series, metadata
    
    def _clean_list(self, data_list: List[Dict[str, Any]], rules: Optional[List[str]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Clean list of dictionaries."""
        cleaned_list = []
        metadata = {
            "rules_applied": [],
            "fields_processed": 0,
            "modifications_made": 0,
            "warnings": [],
            "errors": []
        }
        
        for item in data_list:
            if isinstance(item, dict):
                cleaned_item, item_metadata = self._clean_dict(item, rules)
                cleaned_list.append(cleaned_item)
                
                metadata["fields_processed"] += item_metadata["fields_processed"]
                metadata["rules_applied"].extend(item_metadata["rules_applied"])
                metadata["warnings"].extend(item_metadata["warnings"])
                metadata["errors"].extend(item_metadata["errors"])
                
                if cleaned_item != item:
                    metadata["modifications_made"] += 1
            else:
                cleaned_list.append(item)
        
        return cleaned_list, metadata
    
    def _clean_dict(self, data_dict: Dict[str, Any], rules: Optional[List[str]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Clean dictionary."""
        cleaned_dict = {}
        metadata = {
            "rules_applied": [],
            "fields_processed": 0,
            "modifications_made": 0,
            "warnings": [],
            "errors": []
        }
        
        for field_name, value in data_dict.items():
            try:
                cleaned_value, field_metadata = self._clean_field(field_name, value, rules)
                cleaned_dict[field_name] = cleaned_value
                
                metadata["fields_processed"] += 1
                metadata["rules_applied"].extend(field_metadata.get("rules_applied", []))
                metadata["warnings"].extend(field_metadata.get("warnings", []))
                metadata["errors"].extend(field_metadata.get("errors", []))
                
                if cleaned_value != value:
                    metadata["modifications_made"] += 1
                    
            except Exception as e:
                metadata["errors"].append(f"Error cleaning field {field_name}: {str(e)}")
                cleaned_dict[field_name] = value  # Keep original on error
        
        return cleaned_dict, metadata
    
    def _clean_field(self, field_name: str, value: Any, rules: Optional[List[str]]) -> Tuple[Any, Dict[str, Any]]:
        """Clean individual field."""
        if value is None or value == "":
            return value, {"rules_applied": [], "warnings": [], "errors": []}
        
        cleaned_value = value
        metadata = {
            "rules_applied": [],
            "warnings": [],
            "errors": []
        }
        
        applicable_rules = self._get_applicable_rules(field_name, rules)
        
        for rule in applicable_rules:
            try:
                cleaning_func = self._custom_functions.get(rule.cleaning_function)
                if not cleaning_func:
                    continue
                
                result = cleaning_func(cleaned_value, **rule.parameters)
                
                if isinstance(result, CleaningResult):
                    cleaned_value = result.cleaned_value
                    metadata["rules_applied"].extend(result.rules_applied)
                    metadata["warnings"].extend(result.warnings)
                    metadata["errors"].extend(result.errors)
                else:
                    cleaned_value = result
                    metadata["rules_applied"].append(rule.name)
                    
            except Exception as e:
                metadata["errors"].append(f"Error applying rule {rule.name}: {str(e)}")
        
        return cleaned_value, metadata
    
    def _get_applicable_rules(self, field_name: str, rules: Optional[List[str]]) -> List[CleaningRule]:
        """Get rules applicable to a field."""
        applicable_rules = []
        
        for rule in self._cleaning_rules:
            if not rule.enabled:
                continue
            
            if rules is not None and rule.name not in rules:
                continue
            
            if re.search(rule.field_pattern, field_name, re.IGNORECASE):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    # Cleaning function implementations
    def _clean_text(self, value: Any, **kwargs) -> CleaningResult:
        """Clean general text content."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = []
        
        # Remove excessive whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        rules_applied.append("whitespace_normalization")
        
        # Remove control characters
        value = ''.join(char for char in value if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        rules_applied.append("control_character_removal")
        
        # Normalize unicode
        value = unicodedata.normalize('NFKC', value)
        rules_applied.append("unicode_normalization")
        
        # Check for suspicious patterns
        if len(value) > 10000:
            warnings.append("Very long text detected")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    def _clean_email(self, value: Any, **kwargs) -> CleaningResult:
        """Clean and validate email addresses."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        errors = []
        rules_applied = ["email_cleaning"]
        
        # Basic cleaning
        value = value.strip().lower()
        
        # Email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            errors.append("Invalid email format")
            # Try to fix common issues
            if ' ' in value:
                value = value.replace(' ', '')
                if re.match(email_pattern, value):
                    warnings.append("Removed spaces from email")
                    errors.clear()
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings,
            errors=errors
        )
    
    def _clean_url(self, value: Any, **kwargs) -> CleaningResult:
        """Clean and validate URLs."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        errors = []
        rules_applied = ["url_cleaning"]
        
        # Basic cleaning
        value = value.strip()
        
        # Add protocol if missing
        if not value.startswith(('http://', 'https://')):
            if value.startswith('www.'):
                value = 'https://' + value
                warnings.append("Added HTTPS protocol")
            elif '.' in value and not value.startswith('//'):
                value = 'https://' + value
                warnings.append("Added HTTPS protocol")
        
        # Validate URL
        try:
            parsed = urlparse(value)
            if not parsed.netloc:
                errors.append("Invalid URL format")
        except Exception:
            errors.append("URL parsing failed")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings,
            errors=errors
        )
    
    def _clean_phone(self, value: Any, **kwargs) -> CleaningResult:
        """Clean and normalize phone numbers."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = ["phone_cleaning"]
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', value)
        
        # Normalize international format
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]
        elif cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = '+' + cleaned
        elif not cleaned.startswith('+') and len(cleaned) == 10:
            cleaned = '+1' + cleaned
        
        if len(cleaned) < 8:
            warnings.append("Phone number seems too short")
        elif len(cleaned) > 15:
            warnings.append("Phone number seems too long")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    def _clean_currency(self, value: Any, **kwargs) -> CleaningResult:
        """Clean and normalize currency values."""
        original_value = value
        warnings = []
        errors = []
        rules_applied = ["currency_cleaning"]
        
        if isinstance(value, (int, float)):
            return CleaningResult(
                original_value=original_value,
                cleaned_value=float(value),
                rules_applied=rules_applied
            )
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove currency symbols and normalize
        value = re.sub(r'[^\d.,\-+]', '', value)
        
        # Handle comma as thousands separator
        if ',' in value and '.' in value:
            # Assume comma is thousands separator
            value = value.replace(',', '')
        elif ',' in value:
            # Could be decimal separator
            if value.count(',') == 1 and len(value.split(',')[1]) <= 2:
                value = value.replace(',', '.')
            else:
                value = value.replace(',', '')
        
        try:
            cleaned_value = float(value)
        except ValueError:
            errors.append("Could not convert to numeric value")
            cleaned_value = original_value
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned_value,
            rules_applied=rules_applied,
            warnings=warnings,
            errors=errors
        )
    
    def _clean_html(self, value: Any, **kwargs) -> CleaningResult:
        """Remove HTML tags and decode entities."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        rules_applied = ["html_cleaning"]
        
        # Remove HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        
        # Decode HTML entities
        value = html.unescape(value)
        
        # Clean up extra whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied
        )
    
    def _clean_whitespace(self, value: Any, **kwargs) -> CleaningResult:
        """Normalize whitespace."""
        if not isinstance(value, str):
            return CleaningResult(
                original_value=value,
                cleaned_value=value,
                rules_applied=[]
            )
        
        original_value = value
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=["whitespace_normalization"]
        )
    
    def _clean_business_name(self, value: Any, **kwargs) -> CleaningResult:
        """Standardize business names."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = ["business_name_standardization"]
        
        # Title case
        value = value.title()
        
        # Standardize common business suffixes
        suffixes = {
            ' Inc': ' Inc.',
            ' Corp': ' Corp.',
            ' Llc': ' LLC',
            ' Ltd': ' Ltd.',
            ' Co': ' Co.',
        }
        
        for old, new in suffixes.items():
            if value.endswith(old):
                value = value[:-len(old)] + new
                warnings.append(f"Standardized suffix: {old} -> {new}")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    def _clean_industry(self, value: Any, **kwargs) -> CleaningResult:
        """Standardize industry classifications."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = ["industry_standardization"]
        
        # Title case
        value = value.title()
        
        # Common industry mappings
        industry_mappings = {
            'It': 'Information Technology',
            'Ai': 'Artificial Intelligence',
            'Ml': 'Machine Learning',
            'Saas': 'Software as a Service',
            'E-Commerce': 'E-commerce',
            'Fintech': 'Financial Technology',
            'Edtech': 'Educational Technology',
            'Healthtech': 'Health Technology'
        }
        
        for old, new in industry_mappings.items():
            if old.lower() in value.lower():
                value = value.replace(old, new)
                warnings.append(f"Standardized industry term: {old} -> {new}")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    # Additional utility methods
    def _normalize_case(self, value: Any, case_type: str = "title", **kwargs) -> CleaningResult:
        """Normalize text case."""
        if not isinstance(value, str):
            return CleaningResult(
                original_value=value,
                cleaned_value=value,
                rules_applied=[]
            )
        
        original_value = value
        
        if case_type == "title":
            value = value.title()
        elif case_type == "lower":
            value = value.lower()
        elif case_type == "upper":
            value = value.upper()
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=[f"case_normalization_{case_type}"]
        )
    
    def _clean_numeric(self, value: Any, **kwargs) -> CleaningResult:
        """Clean numeric values."""
        original_value = value
        errors = []
        rules_applied = ["numeric_cleaning"]
        
        if isinstance(value, (int, float)):
            return CleaningResult(
                original_value=original_value,
                cleaned_value=value,
                rules_applied=rules_applied
            )
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove non-numeric characters except decimal point and minus
        value = re.sub(r'[^\d.\-+]', '', value)
        
        try:
            if '.' in value:
                cleaned_value = float(value)
            else:
                cleaned_value = int(value)
        except ValueError:
            errors.append("Could not convert to numeric value")
            cleaned_value = original_value
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned_value,
            rules_applied=rules_applied,
            errors=errors
        )
    
    def _clean_date(self, value: Any, **kwargs) -> CleaningResult:
        """Clean and parse date values."""
        original_value = value
        errors = []
        warnings = []
        rules_applied = ["date_cleaning"]
        
        if isinstance(value, (date, datetime)):
            return CleaningResult(
                original_value=original_value,
                cleaned_value=value,
                rules_applied=rules_applied
            )
        
        if not isinstance(value, str):
            value = str(value)
        
        # Try to parse various date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt).date()
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            errors.append("Could not parse date")
            cleaned_value = original_value
        else:
            cleaned_value = parsed_date.isoformat()
            if parsed_date.year < 1900 or parsed_date.year > 2100:
                warnings.append("Date year seems unusual")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned_value,
            rules_applied=rules_applied,
            warnings=warnings,
            errors=errors
        )
    
    def _validate_json(self, value: Any, **kwargs) -> CleaningResult:
        """Validate and clean JSON data."""
        original_value = value
        errors = []
        rules_applied = ["json_validation"]
        
        if isinstance(value, (dict, list)):
            return CleaningResult(
                original_value=original_value,
                cleaned_value=value,
                rules_applied=rules_applied
            )
        
        if not isinstance(value, str):
            value = str(value)
        
        try:
            cleaned_value = json.loads(value)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
            cleaned_value = original_value
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned_value,
            rules_applied=rules_applied,
            errors=errors
        )
    
    def _remove_duplicates(self, value: Any, **kwargs) -> CleaningResult:
        """Remove duplicate items from lists."""
        original_value = value
        rules_applied = ["duplicate_removal"]
        
        if isinstance(value, list):
            # Preserve order while removing duplicates
            seen = set()
            cleaned_value = []
            for item in value:
                if item not in seen:
                    seen.add(item)
                    cleaned_value.append(item)
        else:
            cleaned_value = value
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=cleaned_value,
            rules_applied=rules_applied
        )
    
    def _clean_social_media(self, value: Any, **kwargs) -> CleaningResult:
        """Clean social media handles and URLs."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = ["social_media_cleaning"]
        
        # Remove @ symbol from handles
        if value.startswith('@'):
            value = value[1:]
            warnings.append("Removed @ symbol from handle")
        
        # Extract username from full URLs
        social_patterns = {
            'twitter': r'twitter\.com/([^/\?]+)',
            'linkedin': r'linkedin\.com/in/([^/\?]+)',
            'facebook': r'facebook\.com/([^/\?]+)',
            'instagram': r'instagram\.com/([^/\?]+)'
        }
        
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                value = match.group(1)
                warnings.append(f"Extracted {platform} username from URL")
                break
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    def _standardize_country(self, value: Any, **kwargs) -> CleaningResult:
        """Standardize country names."""
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        warnings = []
        rules_applied = ["country_standardization"]
        
        # Common country name mappings
        country_mappings = {
            'usa': 'United States',
            'us': 'United States',
            'america': 'United States',
            'uk': 'United Kingdom',
            'britain': 'United Kingdom',
            'england': 'United Kingdom'
        }
        
        value_lower = value.lower()
        if value_lower in country_mappings:
            value = country_mappings[value_lower]
            warnings.append(f"Standardized country name: {original_value} -> {value}")
        
        return CleaningResult(
            original_value=original_value,
            cleaned_value=value,
            rules_applied=rules_applied,
            warnings=warnings
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data cleaning statistics."""
        uptime = (datetime.utcnow() - self._statistics["start_time"]).total_seconds()
        
        return {
            **self._statistics,
            "uptime_seconds": uptime,
            "average_processing_rate": self._statistics["fields_processed"] / max(uptime, 1),
            "modification_rate": self._statistics["modifications_made"] / max(self._statistics["fields_processed"], 1),
            "error_rate": self._statistics["errors_encountered"] / max(self._statistics["fields_processed"], 1),
            "active_rules": len([r for r in self._cleaning_rules if r.enabled]),
            "total_rules": len(self._cleaning_rules),
            "custom_functions": len(self._custom_functions)
        }


# Global data cleaner instance
mcp_data_cleaner = MCPDataCleaner()


# Convenience functions
def clean_data(data: Any, rules: Optional[List[str]] = None, return_metadata: bool = False):
    """Global data cleaning function."""
    return mcp_data_cleaner.clean_data(data, rules, return_metadata)


def register_cleaning_rule(rule: CleaningRule):
    """Register a new cleaning rule globally."""
    mcp_data_cleaner.add_cleaning_rule(rule)


def register_cleaning_function(name: str, function: Callable):
    """Register a new cleaning function globally."""
    mcp_data_cleaner.register_custom_function(name, function)


# Example usage and testing
if __name__ == "__main__":
    # Test data cleaning
    test_data = {
        "company_name": "  TECH corp INC  ",
        "email": " JOHN.DOE@EXAMPLE.COM ",
        "website": "www.example.com",
        "phone": "(555) 123-4567",
        "revenue": "$1,250,000.50",
        "description": "<p>This is a <strong>great</strong> company!</p>",
        "industry": "it"
    }
    
    cleaner = MCPDataCleaner()
    cleaned_data, metadata = cleaner.clean_data(test_data, return_metadata=True)
    
    print(f"Original: {test_data}")
    print(f"Cleaned: {cleaned_data}")
    print(f"Metadata: {json.dumps(metadata, indent=2, default=str)}")
    
    # Get statistics
    stats = cleaner.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")
