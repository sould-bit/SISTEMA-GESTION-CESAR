"""
Menu Engineering Report API Router
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.services.menu_engineering_service import MenuEngineeringService
from app.schemas.menu_engineering import (
    MenuEngineeringReportResponse,
    RecommendationsResponse,
    RecommendationItem
)
from app.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/reports/menu-engineering", tags=["Reports - Menu Engineering"])


@router.get("/", response_model=MenuEngineeringReportResponse)
async def get_menu_engineering_report(
    branch_id: Optional[int] = Query(None, description="Filtrar por sucursal"),
    start_date: Optional[datetime] = Query(None, description="Fecha inicio (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Fecha fin (ISO 8601)"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Genera el reporte de ingeniería de menú con clasificación BCG.
    
    Clasifica productos en:
    - **Stars**: Alta popularidad + Alto margen
    - **Plowhorses**: Alta popularidad + Bajo margen
    - **Puzzles**: Baja popularidad + Alto margen
    - **Dogs**: Baja popularidad + Bajo margen
    """
    service = MenuEngineeringService(session)
    report = await service.generate_report(
        company_id=current_user.company_id,
        branch_id=branch_id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )
    return report


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_menu_recommendations(
    branch_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Genera recomendaciones accionables basadas en el análisis.
    """
    service = MenuEngineeringService(session)
    report = await service.generate_report(
        company_id=current_user.company_id,
        branch_id=branch_id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )
    recommendations = await service.get_recommendations(report)
    return {"recommendations": recommendations}


@router.get("/summary")
async def get_menu_summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Resumen rápido del estado del menú (últimos 30 días).
    Ideal para dashboards.
    """
    service = MenuEngineeringService(session)
    report = await service.generate_report(company_id=current_user.company_id)
    
    return {
        "period_days": 30,
        "total_products": report["summary"]["total_products"],
        "total_revenue": report["summary"]["total_revenue"],
        "classification": report["classification_counts"],
        "top_stars": [
            {"name": p["product_name"], "revenue": p["revenue"]}
            for p in report["matrix"]["stars"][:3]
        ],
        "urgent_dogs": [
            {"name": p["product_name"], "food_cost_pct": p["food_cost_pct"]}
            for p in report["matrix"]["dogs"][:3]
        ],
    }
