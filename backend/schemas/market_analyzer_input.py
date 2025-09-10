from typing import List

from pydantic import BaseModel


class MarketAnalyzerInput(BaseModel):
    company_name: str
    business_domain: str
    region_or_market: str
    business_needs: str
    product_or_service: str
    target_audience: str
    unique_value_proposition: str
    distribution_channels: str
    revenue_model: str
    key_partners: str
    kpis_or_outcomes: str
    technologies_involved: str
    document_references: str
    start_date: str
    urls: List[str]
