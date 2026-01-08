from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.models.order import Order, OrderStatus, OrderItem
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.category import Category
from app.schemas.reports import (
    SalesSummary, TopProduct, CategorySale, 
    PaymentMethodSale, ReportsCollection
)

class ReportService:
    @classmethod
    async def get_sales_summary(
        cls,
        db: AsyncSession, 
        company_id: int, 
        branch_id: Optional[int], 
        start_date: datetime, 
        end_date: datetime
    ) -> SalesSummary:

        """
        Calcula el resumen de ventas (Bruto, Neto, Impuestos, Cantidades).
        """
        # Filtros comunes
        filters = [
            Order.company_id == company_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)

        # 1. Métricas de Pedidos Exitosos (Todo menos Cancelados)
        success_status = [
            OrderStatus.PENDING, OrderStatus.CONFIRMED, 
            OrderStatus.PREPARING, OrderStatus.READY, 
            OrderStatus.DELIVERED
        ]
        
        query_success = select(
            func.sum(Order.total).label("gross"),
            func.sum(Order.subtotal).label("net"),
            func.sum(Order.tax_total).label("tax"),
            func.count(Order.id).label("count")
        ).where(and_(*filters, Order.status.in_(success_status)))
        
        result_success = await db.execute(query_success)
        metrics = result_success.first()
        
        gross = metrics.gross or Decimal("0.00")
        net = metrics.net or Decimal("0.00")
        tax = metrics.tax or Decimal("0.00")
        count = metrics.count or 0

        # 2. Cantidad de Cancelados
        query_canceled = select(func.count(Order.id)).where(
            and_(*filters, Order.status == OrderStatus.CANCELLED)
        )
        canceled_count = (await db.execute(query_canceled)).scalar() or 0

        # 3. Cantidad de Items Vendidos (Solo pedidos exitosos)
        query_items = select(func.sum(OrderItem.quantity)).join(Order).where(
            and_(*filters, Order.status.in_(success_status))
        )
        items_count = (await db.execute(query_items)).scalar() or Decimal("0.00")

        # 4. Cálculos derivados
        avg_ticket = net / count if count > 0 else Decimal("0.00")
        total_orders = count + canceled_count
        conversion_rate = (count / total_orders * 100) if total_orders > 0 else 0.0

        # 5. Crecimiento (Growth Rate)
        growth_rate = await cls.get_growth_rate(
            db, company_id, branch_id, start_date, end_date, net
        )

        return SalesSummary(
            gross_revenue=gross,
            net_revenue=net,
            tax_total=tax,
            order_count=count,
            canceled_orders_count=canceled_count,
            items_sold_count=items_count,
            average_ticket=avg_ticket,
            conversion_rate=conversion_rate,
            growth_rate=growth_rate,
            period_start=start_date,
            period_end=end_date
        )

    @classmethod
    async def get_dashboard_report(
        cls,
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ) -> ReportsCollection:
        """Genera la colección completa de reportes para el dashboard."""
        summary = await cls.get_sales_summary(db, company_id, branch_id, start_date, end_date)
        top_products = await cls.get_top_products(db, company_id, branch_id, start_date, end_date)
        categories = await cls.get_sales_by_category(db, company_id, branch_id, start_date, end_date)
        payments = await cls.get_sales_by_payment_method(db, company_id, branch_id, start_date, end_date)

        return ReportsCollection(
            summary=summary,
            top_products=top_products,
            categories=categories,
            payments=payments
        )

    @staticmethod
    async def get_top_products(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime,
        limit: int = 5
    ) -> List[TopProduct]:
        """Ranking de productos más vendidos."""
        filters = [
            Order.company_id == company_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status != OrderStatus.CANCELLED
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)

        query = select(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label("total_qty"),
            func.sum(OrderItem.subtotal).label("total_revenue")
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .join(Order, Order.id == OrderItem.order_id)\
         .where(and_(*filters))\
         .group_by(Product.id, Product.name)\
         .order_by(desc("total_qty"))\
         .limit(limit)

        result = await db.execute(query)
        return [
            TopProduct(
                product_id=row.id,
                product_name=row.name,
                quantity_sold=row.total_qty,
                revenue=row.total_revenue
            ) for row in result.all()
        ]

    @staticmethod
    async def get_sales_by_category(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ) -> List[CategorySale]:
        """Distribución de ventas por categoría."""
        filters = [
            Order.company_id == company_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status != OrderStatus.CANCELLED
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)

        # 1. Obtener ingresos por categoría
        query = select(
            Category.id,
            Category.name,
            func.sum(OrderItem.subtotal).label("revenue")
        ).join(Product, Product.category_id == Category.id)\
         .join(OrderItem, OrderItem.product_id == Product.id)\
         .join(Order, Order.id == OrderItem.order_id)\
         .where(and_(*filters))\
         .group_by(Category.id, Category.name)

        result = await db.execute(query)
        rows = result.all()
        
        total_revenue = sum(row.revenue for row in rows) if rows else Decimal("0.00")
        
        return [
            CategorySale(
                category_id=row.id,
                category_name=row.name,
                revenue=row.revenue,
                percentage=(float(row.revenue / total_revenue * 100)) if total_revenue > 0 else 0.0
            ) for row in rows
        ]

    @staticmethod
    async def get_sales_by_payment_method(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ) -> List[PaymentMethodSale]:
        """Ventas desglosadas por método de pago."""
        filters = [
            Payment.company_id == company_id,
            Payment.created_at >= start_date,
            Payment.created_at <= end_date,
            Payment.status == PaymentStatus.COMPLETED
        ]
        if branch_id:
            filters.append(Payment.branch_id == branch_id)

        query = select(
            Payment.method,
            func.sum(Payment.amount).label("revenue"),
            func.count(Payment.id).label("count")
        ).where(and_(*filters))\
         .group_by(Payment.method)

        result = await db.execute(query)
        return [
            PaymentMethodSale(
                method=row.method,
                revenue=row.revenue,
                count=row.count
            ) for row in result.all()
        ]

    @classmethod
    async def get_growth_rate(
        cls,
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime,
        current_net: Decimal
    ) -> Optional[float]:
        """Calcula el crecimiento comparando con el periodo anterior de igual duración."""
        duration = end_date - start_date
        prev_start = start_date - duration
        prev_end = start_date

        filters = [
            Order.company_id == company_id,
            Order.created_at >= prev_start,
            Order.created_at < prev_end,
            Order.status != OrderStatus.CANCELLED
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)

        query_prev = select(func.sum(Order.subtotal)).where(and_(*filters))
        prev_net = (await db.execute(query_prev)).scalar() or Decimal("0.00")

        if prev_net == 0:
            return None if current_net == 0 else 100.0
            
        growth = float((current_net - prev_net) / prev_net * 100)
        return growth
