"""
Menu Engineering Report Service

Implementa la lógica de la Matriz BCG adaptada para restaurantes:
- Stars (Estrellas): Alta popularidad + Alta rentabilidad
- Plowhorses (Caballos): Alta popularidad + Baja rentabilidad  
- Puzzles (Rompecabezas): Baja popularidad + Alta rentabilidad
- Dogs (Perros): Baja popularidad + Baja rentabilidad

Métricas clave:
- Popularidad: % de ventas del producto vs total
- Rentabilidad: Margen de contribución (precio - costo)
- Food Cost %: Costo / Precio de Venta
"""

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.recipe import Recipe
from app.models.order import Order, OrderItem
from app.models.category import Category


class MenuEngineeringService:
    """Servicio de análisis de ingeniería de menú."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_report(
        self,
        company_id: int,
        branch_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[int] = None
    ) -> Dict:
        """
        Genera el reporte completo de ingeniería de menú.
        
        Returns:
            Dict con productos clasificados en la matriz BCG
        """
        # Default: últimos 30 días
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 1. Obtener productos con sus recetas
        products = await self._get_products_with_recipes(company_id, category_id)
        
        # 2. Obtener datos de ventas
        sales_data = await self._get_sales_data(
            company_id, branch_id, start_date, end_date, [p.id for p in products]
        )
        
        # 3. Calcular métricas para cada producto
        product_metrics = []
        total_quantity_sold = sum(s["quantity"] for s in sales_data.values()) or 1
        total_revenue = sum(s["revenue"] for s in sales_data.values()) or Decimal(1)
        
        for product in products:
            sales = sales_data.get(product.id, {"quantity": 0, "revenue": Decimal(0)})
            
            # Calcular costo (de receta activa o estimado)
            cost = await self._get_product_cost(product)
            
            # Métricas
            quantity_sold = sales["quantity"]
            revenue = sales["revenue"]
            avg_price = revenue / quantity_sold if quantity_sold > 0 else product.price
            
            contribution_margin = avg_price - cost
            food_cost_pct = (cost / avg_price * 100) if avg_price > 0 else Decimal(0)
            popularity_pct = (quantity_sold / total_quantity_sold * 100) if total_quantity_sold > 0 else 0
            revenue_share = (revenue / total_revenue * 100) if total_revenue > 0 else Decimal(0)
            
            product_metrics.append({
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category.name if product.category else "Sin categoría",
                "price": float(product.price),
                "cost": float(cost),
                "quantity_sold": quantity_sold,
                "revenue": float(revenue),
                "contribution_margin": float(contribution_margin),
                "food_cost_pct": float(food_cost_pct),
                "popularity_pct": float(popularity_pct),
                "revenue_share": float(revenue_share),
            })
        
        # 4. Calcular promedios para clasificación
        avg_popularity = sum(p["popularity_pct"] for p in product_metrics) / len(product_metrics) if product_metrics else 0
        avg_margin = sum(p["contribution_margin"] for p in product_metrics) / len(product_metrics) if product_metrics else 0
        
        # 5. Clasificar productos
        stars = []
        plowhorses = []
        puzzles = []
        dogs = []
        
        for pm in product_metrics:
            high_popularity = pm["popularity_pct"] >= avg_popularity
            high_margin = pm["contribution_margin"] >= avg_margin
            
            if high_popularity and high_margin:
                pm["classification"] = "star"
                stars.append(pm)
            elif high_popularity and not high_margin:
                pm["classification"] = "plowhorse"
                plowhorses.append(pm)
            elif not high_popularity and high_margin:
                pm["classification"] = "puzzle"
                puzzles.append(pm)
            else:
                pm["classification"] = "dog"
                dogs.append(pm)
        
        # 6. Construir respuesta
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_products": len(product_metrics),
                "total_revenue": float(total_revenue),
                "total_quantity_sold": total_quantity_sold,
                "avg_popularity_threshold": round(avg_popularity, 2),
                "avg_margin_threshold": round(avg_margin, 2),
            },
            "classification_counts": {
                "stars": len(stars),
                "plowhorses": len(plowhorses),
                "puzzles": len(puzzles),
                "dogs": len(dogs),
            },
            "matrix": {
                "stars": sorted(stars, key=lambda x: x["revenue"], reverse=True),
                "plowhorses": sorted(plowhorses, key=lambda x: x["quantity_sold"], reverse=True),
                "puzzles": sorted(puzzles, key=lambda x: x["contribution_margin"], reverse=True),
                "dogs": sorted(dogs, key=lambda x: x["revenue"], reverse=True),
            },
            "all_products": sorted(product_metrics, key=lambda x: x["revenue"], reverse=True),
        }
    
    async def _get_products_with_recipes(
        self, company_id: int, category_id: Optional[int] = None
    ) -> List[Product]:
        """Obtiene productos activos con sus recetas."""
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.company_id == company_id)
            .where(Product.is_active == True)
        )
        
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _get_sales_data(
        self,
        company_id: int,
        branch_id: Optional[int],
        start_date: datetime,
        end_date: datetime,
        product_ids: List[int]
    ) -> Dict[int, Dict]:
        """Obtiene datos de ventas agrupados por producto."""
        stmt = (
            select(
                OrderItem.product_id,
                func.sum(OrderItem.quantity).label("quantity"),
                func.sum(OrderItem.subtotal).label("revenue")
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.company_id == company_id)
            .where(Order.status.in_(["completed", "delivered", "paid"]))
            .where(Order.created_at >= start_date)
            .where(Order.created_at <= end_date)
            .where(OrderItem.product_id.in_(product_ids))
            .group_by(OrderItem.product_id)
        )
        
        if branch_id:
            stmt = stmt.where(Order.branch_id == branch_id)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return {
            row.product_id: {
                "quantity": row.quantity or 0,
                "revenue": Decimal(row.revenue or 0)
            }
            for row in rows
        }
    
    async def _get_product_cost(self, product: Product) -> Decimal:
        """Obtiene el costo del producto desde su receta activa."""
        if product.active_recipe_id:
            stmt = select(Recipe).where(Recipe.id == product.active_recipe_id)
            result = await self.session.execute(stmt)
            recipe = result.scalar_one_or_none()
            if recipe:
                return recipe.total_cost
        
        # Fallback: estimar como 30% del precio (promedio industria)
        return Decimal(float(product.price) * 0.30)
    
    async def get_recommendations(self, report: Dict) -> List[Dict]:
        """
        Genera recomendaciones basadas en el análisis.
        """
        recommendations = []
        
        # Recomendaciones para Dogs
        for dog in report["matrix"]["dogs"][:3]:  # Top 3 más urgentes
            recommendations.append({
                "product": dog["product_name"],
                "classification": "dog",
                "severity": "high",
                "action": "Considerar eliminar del menú o reformular receta",
                "reason": f"Baja popularidad ({dog['popularity_pct']:.1f}%) y bajo margen (${dog['contribution_margin']:.0f})"
            })
        
        # Recomendaciones para Plowhorses
        for horse in report["matrix"]["plowhorses"][:3]:
            recommendations.append({
                "product": horse["product_name"],
                "classification": "plowhorse",
                "severity": "medium",
                "action": "Reducir costos o aumentar precio ligeramente",
                "reason": f"Popular pero food cost alto ({horse['food_cost_pct']:.1f}%)"
            })
        
        # Recomendaciones para Puzzles
        for puzzle in report["matrix"]["puzzles"][:3]:
            recommendations.append({
                "product": puzzle["product_name"],
                "classification": "puzzle",
                "severity": "low",
                "action": "Aumentar visibilidad en menú y promocionar",
                "reason": f"Alto margen (${puzzle['contribution_margin']:.0f}) pero baja rotación"
            })
        
        return recommendations
