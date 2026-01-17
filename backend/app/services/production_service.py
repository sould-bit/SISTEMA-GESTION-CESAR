from decimal import Decimal
from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import uuid

from app.models.production_event import ProductionEvent
from app.services.inventory_service import InventoryService
from app.models.ingredient import Ingredient, IngredientType

class ProductionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)

    async def register_production_event(
        self,
        company_id: int,
        branch_id: int,
        user_id: int,
        inputs: list[dict], # List of {ingredient_id: UUID, quantity: float}
        output: dict, # {ingredient_id: UUID} OR {name: str, base_unit: str, category_id: int}
        output_quantity: float,
        notes: str = None
    ) -> ProductionEvent:
        """
        Registra una transformación de insumos Múltiples -> Uno.
        
        Args:
            inputs: Lista de insumos a consumir.
            output: Dict con 'ingredient_id' (existente) O datos para crear uno nuevo ('name', 'base_unit', etc).
            output_quantity: Cantidad producida.
        """
        from app.models.production_event_input import ProductionEventInput
        from app.services.ingredient_service import IngredientService
        
        # 0. Validaciones básicas
        if output_quantity <= 0:
            raise HTTPException(status_code=400, detail="Output quantity must be positive")
        if not inputs:
            raise HTTPException(status_code=400, detail="At least one input is required")

        # 1. Resolver Insumo Destino (Get or Create)
        ingredient_service = IngredientService(self.db)
        output_ing_id = output.get('ingredient_id')
        output_ing_name = None
        
        if output_ing_id:
            # Verificar existencia y compañía
            stmt = select(Ingredient).where(Ingredient.id == output_ing_id)
            res = await self.db.execute(stmt)
            output_ing = res.scalar_one_or_none()
            if not output_ing or output_ing.company_id != company_id:
                raise HTTPException(status_code=404, detail="Output ingredient not found")
            output_ing_name = output_ing.name
        else:
            # Crear Nuevo Insumo Procesado
            from app.schemas.ingredients import IngredientCreate
            
            # Generar SKU o dejar que el servicio lo haga
            new_data = IngredientCreate(
                name=output.get('name'),
                base_unit=output.get('base_unit', 'units'),
                ingredient_type='PROCESSED',
                category_id=output.get('category_id'),
                current_cost=0 # Se calculará
            )
            # Llamamos al create del servicio que ya maneja SKU autogen
            # Llamamos al create del servicio
            new_ing = await ingredient_service.create(
                company_id=company_id,
                name=new_data.name,
                sku=new_data.sku,
                base_unit=new_data.base_unit,
                current_cost=new_data.current_cost,
                category_id=new_data.category_id,
                yield_factor=1.0,
                ingredient_type='PROCESSED'
            )
            output_ing_id = new_ing.id
            output_ing_name = new_ing.name

        # 2. Consumir Insumos Origen (Loop Inputs)
        total_input_cost = Decimal(0)
        event_inputs = []
        # Track batch consumptions to store after flush
        batch_consumption_records = []

        for item in inputs:
            ing_id = item['ingredient_id']
            qty = item['quantity']
            
            if qty <= 0:
                continue

            # Verificar ingrediente (opcional, el inventory update fallará si no existe o no hay stock)
            
            qty_decimal = Decimal(qty)
            
            # Update Stock (OUT) and Get Cost + Batch Details
            _, consumed_cost, _, batch_consumptions = await self.inventory_service.update_ingredient_stock(
                branch_id=branch_id,
                ingredient_id=ing_id,
                quantity_delta=qty_decimal * -1, 
                transaction_type="PRODUCTION_OUT",
                user_id=user_id,
                reason=f"Producción de {output_ing_name}"
            )
            
            total_input_cost += consumed_cost
            
            # Prepare Input Record
            input_record = ProductionEventInput(
                ingredient_id=ing_id,
                quantity=qty,
                cost_allocated=consumed_cost
            )
            event_inputs.append(input_record)
            
            # Store batch consumption details for later
            batch_consumption_records.append({
                "input_record": input_record,
                "consumptions": batch_consumptions
            })

        # 3. Calcular Costo Unitario
        qty_out_decimal = Decimal(output_quantity)
        unit_cost_out = total_input_cost / qty_out_decimal if qty_out_decimal > 0 else 0
        
        # 4. Agregar Insumo Destino (IN)
        _, _, created_batch, _ = await self.inventory_service.update_ingredient_stock(
            branch_id=branch_id,
            ingredient_id=output_ing_id,
            quantity_delta=qty_out_decimal,
            transaction_type="PRODUCTION_IN",
            user_id=user_id,
            reason="Producción Interna",
            cost_per_unit=unit_cost_out,
            supplier="Internal Production"
        )
        
        # 5. Registrar Evento Header
        # Guardamos el primer input como referencia legacy si se desea, o null
        primary_input_id = inputs[0]['ingredient_id'] if inputs else None
        primary_input_qty = inputs[0]['quantity'] if inputs else 0
        
        event = ProductionEvent(
            company_id=company_id,
            input_ingredient_id=primary_input_id, # Legacy/Reference
            input_quantity=primary_input_qty,      # Legacy/Reference
            input_cost_total=total_input_cost,
            output_ingredient_id=output_ing_id,
            output_quantity=output_quantity,
            output_batch_id=created_batch.id if created_batch else None,
            calculated_unit_cost=unit_cost_out,
            user_id=user_id,
            notes=notes
        )
        self.db.add(event)
        await self.db.flush() # Para obtener ID
        
        # 6. Registrar Inputs Details
        for inp in event_inputs:
            inp.production_event_id = event.id
            self.db.add(inp)
        
        await self.db.flush()  # Flush to get input IDs for batch consumption records
        
        # 7. Store Batch Consumption Details (for precise undo)
        from app.models.production_event_input_batch import ProductionEventInputBatch
        
        for record in batch_consumption_records:
            input_obj = record["input_record"]
            for consumption in record["consumptions"]:
                batch_consumption = ProductionEventInputBatch(
                    production_event_input_id=input_obj.id,
                    source_batch_id=consumption["batch_id"],
                    quantity_consumed=consumption["quantity_consumed"],
                    cost_attributed=consumption["cost_attributed"]
                )
                self.db.add(batch_consumption)
            
        await self.db.commit()
        await self.db.refresh(event)
        
        return event

    async def revert_production_by_output_batch(self, batch_id: uuid.UUID) -> bool:
        """
        Revertir una producción dado el ID del lote resultante (batch_id).
        Restaura el stock de los insumos consumidos a sus lotes originales.
        
        Args:
            batch_id: El ID del lote de producto terminado (output_batch_id en ProductionEvent).
            
        Returns:
            bool: True si se revirtió una producción, False si no se encontró evento asociado.
        """
        from sqlalchemy.orm import selectinload
        from app.models.production_event_input import ProductionEventInput
        
        # 1. Buscar el evento de producción asociado a este lote
        # Load inputs AND their batch_consumptions for precise reversal
        stmt = select(ProductionEvent).where(
            ProductionEvent.output_batch_id == batch_id
        ).options(
            selectinload(ProductionEvent.inputs).selectinload(ProductionEventInput.batch_consumptions)
        )
        
        result = await self.db.execute(stmt)
        event = result.scalar_one_or_none()
        
        if not event:
            return False
        
        branch_id = await self._get_branch_id_from_batch(batch_id)
            
        # 2. Iterate over inputs and their batch consumptions for PRECISE restoration
        for inp in event.inputs:
            # Check if we have granular batch consumption data
            if hasattr(inp, 'batch_consumptions') and inp.batch_consumptions:
                # NEW: Precise restoration to each original batch
                for consumption in inp.batch_consumptions:
                    await self.inventory_service.restore_stock_to_batch(
                        batch_id=consumption.source_batch_id,
                        quantity=consumption.quantity_consumed,
                        branch_id=branch_id,
                        ingredient_id=inp.ingredient_id,
                        user_id=event.user_id,
                        reason=f"Rollback Producción {event.id}"
                    )
            else:
                # LEGACY: Fallback for events without batch consumption tracking
                if inp.quantity > 0:
                    await self.inventory_service.restore_stock_to_batches(
                        branch_id=branch_id,
                        ingredient_id=inp.ingredient_id,
                        quantity=Decimal(inp.quantity),
                        user_id=event.user_id,
                        reason=f"Rollback Producción {event.id} (Legacy)"
                    )
                
        # 3. Eliminar el evento (Cascade debería borrar los inputs y batch_consumptions)
        await self.db.delete(event)
        await self.db.commit()
        
        return True

    async def _get_branch_id_from_batch(self, batch_id: uuid.UUID) -> int:
        from app.models.ingredient_batch import IngredientBatch
        stmt = select(IngredientBatch.branch_id).where(IngredientBatch.id == batch_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()
