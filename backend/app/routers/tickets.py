"""
🧾 Ticket Router - Endpoints para Comandas/Tickets
===================================================

MVP: Descarga de PDFs para impresión manual
Evolución: Impresión automática via WebSocket

Endpoints:
- GET /tickets/order/{id}/receipt.pdf - Ticket de caja (con precios)
- GET /tickets/order/{id}/kitchen.pdf - Comanda cocina (sin precios)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.auth_deps import get_current_user
from app.models.user import User
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/order/{order_id}/receipt.pdf")
async def download_receipt_ticket(
    order_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga ticket de caja en formato PDF.
    
    El PDF tiene formato de ticket térmico (80mm de ancho).
    Incluye: empresa, pedido, items con precios, totales.
    
    # TODO: EVOLUCIÓN OPCIÓN B
    # Cambiar a: POST /tickets/order/{id}/print
    # Que envíe via WebSocket en lugar de descargar PDF
    """
    try:
        ticket_service = TicketService(db)
        pdf_buffer = await ticket_service.generate_ticket_pdf(
            order_id=order_id,
            company_id=current_user.company_id  # Multi-tenant security
        )
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ticket_{order_id}.pdf"
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Servicio de tickets no disponible. Falta dependencia: reportlab"
        )


@router.get("/order/{order_id}/kitchen.pdf")
async def download_kitchen_ticket(
    order_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga comanda de cocina en formato PDF.
    
    Versión simplificada sin precios.
    Destaca: número de pedido, tipo, cantidades, notas.
    
    # TODO: EVOLUCIÓN OPCIÓN B
    # Cambiar a: POST /tickets/order/{id}/print-kitchen
    # Que envíe a impresora de cocina via WebSocket
    """
    try:
        ticket_service = TicketService(db)
        pdf_buffer = await ticket_service.generate_kitchen_ticket_pdf(
            order_id=order_id,
            company_id=current_user.company_id  # Multi-tenant security
        )
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=comanda_{order_id}.pdf"
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Servicio de tickets no disponible. Falta dependencia: reportlab"
        )


# =============================================================================
# EVOLUCIÓN OPCIÓN B: ENDPOINTS DE IMPRESIÓN AUTOMÁTICA
# =============================================================================
#
# Cuando migres a WebSocket + Agente, agrega estos endpoints:
#
# @router.post("/order/{order_id}/print")
# async def print_receipt(
#     order_id: int,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user)
# ):
#     """Envía ticket de caja a impresora via WebSocket."""
#     from app.core.websockets import sio
#     
#     ticket_service = TicketService(db)
#     ticket_data = await ticket_service.build_ticket_data(order_id)
#     
#     await sio.emit(
#         "print_job",
#         {"type": "receipt", "data": ticket_data},
#         room=f"printer_{current_user.branch_id}_receipt"
#     )
#     
#     return {"message": "Ticket enviado a impresora", "order_id": order_id}
#
#
# @router.post("/order/{order_id}/print-kitchen")
# async def print_kitchen(order_id: int, ...):
#     """Envía comanda a impresora de cocina."""
#     ...
#
# =============================================================================
