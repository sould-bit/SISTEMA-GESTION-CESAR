"""
Schemas for Menu Engineering Reports
"""

from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class MenuEngineeringProductMetrics(BaseModel):
    """Métricas de un producto en el análisis de ingeniería de menú."""
    product_id: int
    product_name: str
    category: str
    price: float
    cost: float
    quantity_sold: int
    revenue: float
    contribution_margin: float
    food_cost_pct: float
    popularity_pct: float
    revenue_share: float
    classification: Optional[str] = None  # star, plowhorse, puzzle, dog


class ReportPeriod(BaseModel):
    start: str
    end: str


class ReportSummary(BaseModel):
    total_products: int
    total_revenue: float
    total_quantity_sold: int
    avg_popularity_threshold: float
    avg_margin_threshold: float


class ClassificationCounts(BaseModel):
    stars: int
    plowhorses: int
    puzzles: int
    dogs: int


class BCGMatrix(BaseModel):
    stars: List[MenuEngineeringProductMetrics]
    plowhorses: List[MenuEngineeringProductMetrics]
    puzzles: List[MenuEngineeringProductMetrics]
    dogs: List[MenuEngineeringProductMetrics]


class MenuEngineeringReportResponse(BaseModel):
    """Respuesta completa del reporte de ingeniería de menú."""
    period: ReportPeriod
    summary: ReportSummary
    classification_counts: ClassificationCounts
    matrix: BCGMatrix
    all_products: List[MenuEngineeringProductMetrics]


class RecommendationItem(BaseModel):
    product: str
    classification: str
    severity: str  # high, medium, low
    action: str
    reason: str


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]


class MenuEngineeringReportRequest(BaseModel):
    """Parámetros para generar el reporte."""
    branch_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None
