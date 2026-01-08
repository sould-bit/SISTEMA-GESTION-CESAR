from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.services.report_service import ReportService
from app.schemas.reports import (
    SalesSummary, TopProduct, CategorySale, 
    PaymentMethodSale, ReportsCollection
)

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/dashboard", response_model=ReportsCollection)
@require_permission("reports.sales")
async def get_dashboard_report(
    branch_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el reporte completo para el dashboard.
    Default: Últimos 30 días.
    """
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser posterior a la de fin.")

    return await ReportService.get_dashboard_report(
        db, current_user.company_id, branch_id, start_date, end_date
    )

@router.get("/summary", response_model=SalesSummary)
@require_permission("reports.sales")
async def get_sales_summary(
    branch_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Resumen de ventas y salud operativa."""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    return await ReportService.get_sales_summary(
        db, current_user.company_id, branch_id, start_date, end_date
    )

@router.get("/top-products", response_model=List[TopProduct])
@require_permission("reports.sales")
async def get_top_products(
    branch_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(5, gt=0),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Top productos más vendidos."""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    return await ReportService.get_top_products(
        db, current_user.company_id, branch_id, start_date, end_date, limit
    )

@router.get("/categories", response_model=List[CategorySale])
@require_permission("reports.sales")
async def get_sales_by_category(
    branch_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Ventas distribuidas por categoría."""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    return await ReportService.get_sales_by_category(
        db, current_user.company_id, branch_id, start_date, end_date
    )

@router.get("/payments", response_model=List[PaymentMethodSale])
@require_permission("reports.sales")
async def get_sales_by_payment_method(
    branch_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Ventas desglosadas por método de pago."""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    return await ReportService.get_sales_by_payment_method(
        db, current_user.company_id, branch_id, start_date, end_date
    )
