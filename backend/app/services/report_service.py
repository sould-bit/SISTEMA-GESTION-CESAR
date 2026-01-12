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

    # =========================================================================
    # NUEVOS REPORTES - Inventario, Domiciliarios, Consumo
    # =========================================================================

    @staticmethod
    async def get_inventory_report(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int] = None,
        include_zero_stock: bool = True
    ):
        """
        Genera reporte de estado de inventario.
        
        Incluye: stock actual, valor total, alertas de stock bajo.
        """
        from app.models.inventory import Inventory
        from app.schemas.reports import InventoryReport, InventoryReportItem
        
        filters = [
            Product.company_id == company_id,
            Product.is_active == True
        ]
        
        query = select(
            Product.id,
            Product.name,
            Category.name.label("category_name"),
            Inventory.quantity,
            Inventory.min_stock,
            Inventory.max_stock,
            Product.cost_price
        ).outerjoin(Category, Product.category_id == Category.id)\
         .outerjoin(Inventory, and_(
             Inventory.product_id == Product.id,
             Inventory.company_id == company_id
         ))\
         .where(and_(*filters))
        
        if branch_id:
            query = query.where(Inventory.branch_id == branch_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        items = []
        total_value = Decimal("0")
        low_stock_count = 0
        out_of_stock_count = 0
        
        for row in rows:
            current_stock = row.quantity or Decimal("0")
            min_stock = row.min_stock or Decimal("0")
            max_stock = row.max_stock or Decimal("999999")
            unit_cost = row.cost_price or Decimal("0")
            total_item_value = current_stock * unit_cost
            
            # Determinar status
            if current_stock <= 0:
                stock_status = "OUT"
                out_of_stock_count += 1
            elif current_stock < min_stock:
                stock_status = "LOW"
                low_stock_count += 1
            elif current_stock > max_stock:
                stock_status = "EXCESS"
            else:
                stock_status = "OK"
            
            if not include_zero_stock and current_stock <= 0:
                continue
            
            items.append(InventoryReportItem(
                product_id=row.id,
                product_name=row.name,
                category_name=row.category_name,
                current_stock=current_stock,
                min_stock=min_stock,
                max_stock=max_stock,
                stock_status=stock_status,
                unit_cost=unit_cost,
                total_value=total_item_value
            ))
            
            total_value += total_item_value
        
        return InventoryReport(
            items=items,
            total_value=total_value,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            generated_at=datetime.utcnow()
        )

    @staticmethod
    async def get_delivery_report(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ):
        """
        Genera reporte de rendimiento de domiciliarios.
        
        Incluye: entregas completadas, canceladas, ingresos, tiempo promedio.
        """
        from app.models.delivery_shift import DeliveryShift
        from app.models.user import User
        from app.schemas.reports import DeliveryReport, DeliveryReportItem
        
        filters = [
            Order.company_id == company_id,
            Order.delivery_type == "delivery",
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)
        
        # Obtener estadísticas por domiciliario
        # Nota: Asumimos que delivery_shift tiene assigned_user_id
        query = select(
            DeliveryShift.user_id,
            User.full_name.label("user_name"),
            func.count(DeliveryShift.id).label("total_deliveries"),
            func.sum(Order.total).label("total_revenue")
        ).join(Order, DeliveryShift.order_id == Order.id)\
         .join(User, DeliveryShift.user_id == User.id)\
         .where(and_(*filters))\
         .group_by(DeliveryShift.user_id, User.full_name)
        
        result = await db.execute(query)
        rows = result.all()
        
        delivery_persons = []
        total_deliveries = 0
        total_revenue = Decimal("0")
        
        for row in rows:
            delivery_persons.append(DeliveryReportItem(
                user_id=row.user_id,
                user_name=row.user_name or f"Usuario #{row.user_id}",
                deliveries_completed=row.total_deliveries or 0,
                deliveries_canceled=0,  # TODO: Agregar lógica de cancelados
                total_revenue=row.total_revenue or Decimal("0"),
                avg_delivery_time_minutes=None  # TODO: Calcular tiempo promedio
            ))
            total_deliveries += row.total_deliveries or 0
            total_revenue += row.total_revenue or Decimal("0")
        
        return DeliveryReport(
            delivery_persons=delivery_persons,
            total_deliveries=total_deliveries,
            total_revenue=total_revenue,
            avg_delivery_time_minutes=None,
            period_start=start_date,
            period_end=end_date
        )

    @staticmethod
    async def get_recipe_consumption_report(
        db: AsyncSession,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime
    ):
        """
        Genera reporte de consumo de ingredientes por recetas.
        
        Calcula cuánto de cada ingrediente se consumió basado en recetas
        de los productos vendidos.
        """
        from app.models.recipe import Recipe, RecipeItem
        from app.schemas.reports import RecipeConsumptionReport, RecipeConsumptionItem
        
        filters = [
            Order.company_id == company_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status != OrderStatus.CANCELLED
        ]
        if branch_id:
            filters.append(Order.branch_id == branch_id)
        
        # Obtener productos vendidos con sus cantidades
        query = select(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label("qty_sold")
        ).join(Order, OrderItem.order_id == Order.id)\
         .where(and_(*filters))\
         .group_by(OrderItem.product_id)
        
        result = await db.execute(query)
        products_sold = {row.product_id: row.qty_sold for row in result.all()}
        
        if not products_sold:
            return RecipeConsumptionReport(
                ingredients=[],
                total_cost=Decimal("0"),
                top_consumed=[],
                period_start=start_date,
                period_end=end_date
            )
        
        # Obtener recetas de los productos vendidos
        recipe_query = select(
            Recipe.product_id,
            RecipeItem.ingredient_id,
            Product.name.label("ingredient_name"),
            RecipeItem.quantity,
            RecipeItem.unit,
            Product.cost_price
        ).join(RecipeItem, Recipe.id == RecipeItem.recipe_id)\
         .join(Product, RecipeItem.ingredient_id == Product.id)\
         .where(Recipe.product_id.in_(products_sold.keys()))
        
        recipe_result = await db.execute(recipe_query)
        
        # Calcular consumo por ingrediente
        consumption_map = {}  # ingredient_id -> {name, total_qty, unit, cost}
        
        for row in recipe_result.all():
            product_qty_sold = products_sold.get(row.product_id, 0)
            consumed = float(row.quantity) * float(product_qty_sold)
            ingredient_cost = float(row.cost_price or 0) * consumed
            
            if row.ingredient_id not in consumption_map:
                consumption_map[row.ingredient_id] = {
                    "name": row.ingredient_name,
                    "total": Decimal("0"),
                    "unit": row.unit or "unidad",
                    "cost": Decimal("0")
                }
            
            consumption_map[row.ingredient_id]["total"] += Decimal(str(consumed))
            consumption_map[row.ingredient_id]["cost"] += Decimal(str(ingredient_cost))
        
        # Construir lista de items
        ingredients = [
            RecipeConsumptionItem(
                ingredient_id=ing_id,
                ingredient_name=data["name"],
                total_consumed=data["total"],
                unit=data["unit"],
                avg_cost_per_unit=data["cost"] / data["total"] if data["total"] > 0 else Decimal("0"),
                total_cost=data["cost"]
            )
            for ing_id, data in consumption_map.items()
        ]
        
        # Ordenar por consumo y obtener top 5
        ingredients.sort(key=lambda x: x.total_consumed, reverse=True)
        top_consumed = [ing.ingredient_name for ing in ingredients[:5]]
        
        total_cost = sum(ing.total_cost for ing in ingredients)
        
        return RecipeConsumptionReport(
            ingredients=ingredients,
            total_cost=total_cost,
            top_consumed=top_consumed,
            period_start=start_date,
            period_end=end_date
        )
