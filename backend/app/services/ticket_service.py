"""
🧾 Ticket Service - Generación de Tickets/Comandas
===================================================

MVP: Generación de PDF descargable para impresión manual
Evolución: WebSocket + Agente Local para impresión automática

Autor: Sistema de Gestión César
"""

import io
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.company import Company
from app.models.branch import Branch

# Para generación de PDF
try:
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.units import mm as mm_unit
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# =============================================================================
# CONSTANTES DE FORMATO
# =============================================================================

# Tamaño de ticket térmico estándar (80mm x longitud variable)
TICKET_WIDTH = 80 * mm_unit
TICKET_MIN_HEIGHT = 200 * mm_unit

# Márgenes
MARGIN_LEFT = 5 * mm_unit
MARGIN_RIGHT = 5 * mm_unit
CONTENT_WIDTH = TICKET_WIDTH - MARGIN_LEFT - MARGIN_RIGHT


class TicketService:
    """
    Servicio para generación de tickets/comandas.
    
    MVP: Genera PDFs descargables
    
    # TODO: EVOLUCIÓN OPCIÓN B - WebSocket + Agente Local
    # =====================================================
    # Para migrar a impresión automática via WebSocket:
    #
    # 1. Agregar método send_to_printer():
    #    async def send_to_printer(self, order_id: int, branch_id: int):
    #        from app.core.websockets import sio
    #        ticket_data = await self._build_ticket_data(order_id)
    #        await sio.emit("print_ticket", ticket_data, room=f"printer_{branch_id}")
    #
    # 2. Crear agente local (print_agent.py) que escuche WebSocket:
    #    - Conectarse a ws://backend/socket.io
    #    - Escuchar evento "print_ticket"
    #    - Usar python-escpos para imprimir
    #
    # 3. Modificar endpoint para llamar send_to_printer() en lugar de generar PDF
    # =====================================================
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_ticket_pdf(self, order_id: int) -> io.BytesIO:
        """
        Genera un PDF con formato de ticket térmico (80mm de ancho).
        
        Args:
            order_id: ID del pedido
            
        Returns:
            BytesIO con el contenido del PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab no está instalado. Ejecuta: pip install reportlab")
        
        # 1. Obtener datos del pedido
        order = await self._get_order_with_details(order_id)
        if not order:
            raise ValueError(f"Pedido {order_id} no encontrado")
        
        # 2. Crear PDF en memoria
        buffer = io.BytesIO()
        
        # Calcular altura dinámica basada en items
        num_items = len(order.items) if order.items else 0
        height = TICKET_MIN_HEIGHT + (num_items * 15 * mm_unit)
        
        c = canvas.Canvas(buffer, pagesize=(TICKET_WIDTH, height))
        
        # 3. Dibujar contenido
        y_position = height - 10 * mm_unit  # Empezar desde arriba
        
        # --- ENCABEZADO ---
        y_position = self._draw_header(c, order, y_position)
        
        # --- LÍNEA SEPARADORA ---
        y_position = self._draw_separator(c, y_position)
        
        # --- INFORMACIÓN DEL PEDIDO ---
        y_position = self._draw_order_info(c, order, y_position)
        
        # --- LÍNEA SEPARADORA ---
        y_position = self._draw_separator(c, y_position)
        
        # --- ITEMS ---
        y_position = self._draw_items(c, order, y_position)
        
        # --- LÍNEA SEPARADORA ---
        y_position = self._draw_separator(c, y_position)
        
        # --- TOTALES ---
        y_position = self._draw_totals(c, order, y_position)
        
        # --- PIE DE PÁGINA ---
        self._draw_footer(c, y_position)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    async def generate_kitchen_ticket_pdf(self, order_id: int) -> io.BytesIO:
        """
        Genera ticket para cocina (solo items, sin precios).
        
        # TODO: EVOLUCIÓN OPCIÓN B
        # Este método se convertiría en:
        # async def send_to_kitchen(self, order_id: int):
        #     await self.send_to_printer(order_id, printer_type="kitchen")
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab no está instalado")
        
        order = await self._get_order_with_details(order_id)
        if not order:
            raise ValueError(f"Pedido {order_id} no encontrado")
        
        buffer = io.BytesIO()
        num_items = len(order.items) if order.items else 0
        height = 150 * mm_unit + (num_items * 20 * mm_unit)
        
        c = canvas.Canvas(buffer, pagesize=(TICKET_WIDTH, height))
        y_position = height - 10 * mm_unit
        
        # --- ENCABEZADO COCINA ---
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(TICKET_WIDTH / 2, y_position, "*** COCINA ***")
        y_position -= 20
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(TICKET_WIDTH / 2, y_position, f"PEDIDO {order.order_number}")
        y_position -= 15
        
        # Tipo de pedido destacado
        delivery_type_display = {
            "dine_in": "🍽️ MESA",
            "takeaway": "📦 PARA LLEVAR", 
            "delivery": "🛵 DOMICILIO"
        }.get(order.delivery_type, order.delivery_type.upper())
        
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(TICKET_WIDTH / 2, y_position, delivery_type_display)
        y_position -= 15
        
        y_position = self._draw_separator(c, y_position)
        
        # --- ITEMS (SIN PRECIOS, SOLO CANTIDADES) ---
        c.setFont("Helvetica-Bold", 12)
        for item in order.items:
            product_name = item.product.name if item.product else f"Producto #{item.product_id}"
            
            # Cantidad grande y destacada
            c.setFont("Helvetica-Bold", 14)
            c.drawString(MARGIN_LEFT, y_position, f"{int(item.quantity)}x")
            
            # Nombre del producto
            c.setFont("Helvetica", 11)
            c.drawString(MARGIN_LEFT + 15 * mm_unit, y_position, product_name[:25])
            y_position -= 8
            
            # Notas del item (si las hay)
            if item.notes:
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(MARGIN_LEFT + 15 * mm_unit, y_position, f"→ {item.notes[:30]}")
                y_position -= 8
            
            y_position -= 8
        
        # --- NOTAS DEL CLIENTE ---
        if order.customer_notes:
            y_position = self._draw_separator(c, y_position)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(MARGIN_LEFT, y_position, "NOTAS:")
            y_position -= 12
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN_LEFT, y_position, order.customer_notes[:50])
            y_position -= 10
        
        # --- HORA ---
        y_position = self._draw_separator(c, y_position)
        c.setFont("Helvetica", 10)
        c.drawCentredString(TICKET_WIDTH / 2, y_position, order.created_at.strftime("%H:%M:%S"))
        
        c.save()
        buffer.seek(0)
        return buffer
    
    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================
    
    async def _get_order_with_details(self, order_id: int) -> Optional[Order]:
        """Obtiene pedido con items, productos y empresa."""
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.company),
                selectinload(Order.branch)
            )
        )
        return result.scalar_one_or_none()
    
    def _draw_header(self, c, order: Order, y: float) -> float:
        """Dibuja encabezado con nombre de empresa."""
        company_name = order.company.name if order.company else "Mi Restaurante"
        branch_name = order.branch.name if order.branch else ""
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(TICKET_WIDTH / 2, y, company_name.upper())
        y -= 12
        
        if branch_name:
            c.setFont("Helvetica", 10)
            c.drawCentredString(TICKET_WIDTH / 2, y, branch_name)
            y -= 10
        
        return y
    
    def _draw_order_info(self, c, order: Order, y: float) -> float:
        """Dibuja información del pedido."""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN_LEFT, y, f"Pedido: {order.order_number}")
        y -= 12
        
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN_LEFT, y, f"Fecha: {order.created_at.strftime('%d/%m/%Y %H:%M')}")
        y -= 10
        
        # Tipo de pedido
        delivery_labels = {
            "dine_in": "Mesa",
            "takeaway": "Para llevar",
            "delivery": "Domicilio"
        }
        c.drawString(MARGIN_LEFT, y, f"Tipo: {delivery_labels.get(order.delivery_type, order.delivery_type)}")
        y -= 10
        
        return y
    
    def _draw_items(self, c, order: Order, y: float) -> float:
        """Dibuja lista de items."""
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN_LEFT, y, "Cant")
        c.drawString(MARGIN_LEFT + 12 * mm_unit, y, "Descripción")
        c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, "Total")
        y -= 12
        
        c.setFont("Helvetica", 9)
        for item in order.items:
            product_name = item.product.name if item.product else f"Item #{item.product_id}"
            subtotal = item.subtotal or (item.quantity * item.unit_price)
            
            c.drawString(MARGIN_LEFT, y, f"{int(item.quantity)}")
            c.drawString(MARGIN_LEFT + 12 * mm_unit, y, product_name[:20])
            c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, f"${subtotal:,.0f}")
            y -= 10
        
        return y
    
    def _draw_totals(self, c, order: Order, y: float) -> float:
        """Dibuja totales."""
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN_LEFT, y, "Subtotal:")
        c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, f"${order.subtotal:,.0f}")
        y -= 10
        
        if order.tax_total and order.tax_total > 0:
            c.drawString(MARGIN_LEFT, y, "IVA:")
            c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, f"${order.tax_total:,.0f}")
            y -= 10
        
        if order.delivery_fee and order.delivery_fee > 0:
            c.drawString(MARGIN_LEFT, y, "Domicilio:")
            c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, f"${order.delivery_fee:,.0f}")
            y -= 10
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN_LEFT, y, "TOTAL:")
        c.drawRightString(TICKET_WIDTH - MARGIN_RIGHT, y, f"${order.total:,.0f}")
        y -= 12
        
        return y
    
    def _draw_separator(self, c, y: float) -> float:
        """Dibuja línea separadora."""
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setDash(1, 2)
        c.line(MARGIN_LEFT, y - 3, TICKET_WIDTH - MARGIN_RIGHT, y - 3)
        c.setDash()
        return y - 10
    
    def _draw_footer(self, c, y: float):
        """Dibuja pie de página."""
        c.setFont("Helvetica", 8)
        c.drawCentredString(TICKET_WIDTH / 2, y, "¡Gracias por su compra!")
        y -= 10
        c.drawCentredString(TICKET_WIDTH / 2, y, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


# =============================================================================
# EVOLUCIÓN OPCIÓN B: WEBSOCKET + AGENTE
# =============================================================================
#
# Para activar impresión automática, crear estos componentes:
#
# 1. BACKEND - Agregar evento WebSocket:
# ----------------------------------------
# # En app/core/websockets.py o nuevo archivo
#
# @sio.on("printer_register")
# async def register_printer(sid, data):
#     """Registrar una impresora (agente se conecta)"""
#     branch_id = data.get("branch_id")
#     printer_type = data.get("type", "receipt")  # receipt, kitchen
#     await sio.enter_room(sid, f"printer_{branch_id}_{printer_type}")
#     logger.info(f"🖨️ Printer registered: Branch {branch_id}, Type {printer_type}")
#
# async def emit_print_job(order_id: int, branch_id: int, printer_type: str = "receipt"):
#     """Enviar trabajo de impresión a agentes conectados"""
#     ticket_data = await build_ticket_data(order_id)  # JSON con datos del ticket
#     await sio.emit("print_job", ticket_data, room=f"printer_{branch_id}_{printer_type}")
#
#
# 2. AGENTE LOCAL - print_agent.py (instalar en cada PC):
# --------------------------------------------------------
# """
# Agente de impresión para FastOps.
# Instalar en cada PC con impresora conectada.
# 
# Requisitos:
#   pip install python-socketio python-escpos
#
# Uso:
#   python print_agent.py --backend ws://tu-servidor:8000 --branch 1
# """
# import socketio
# from escpos.printer import Usb, Network
#
# sio = socketio.Client()
# printer = Usb(0x04b8, 0x0e15)  # Cambiar según modelo
#
# @sio.event
# def connect():
#     sio.emit("printer_register", {"branch_id": BRANCH_ID, "type": "receipt"})
#
# @sio.on("print_job")
# def print_ticket(data):
#     printer.set(align="center")
#     printer.text(data["header"] + "\n")
#     printer.set(align="left")
#     for item in data["items"]:
#         printer.text(f"{item['qty']}x {item['name']}\n")
#     printer.cut()
#
# sio.connect(f"ws://{BACKEND_URL}/socket.io")
# sio.wait()
#
# =============================================================================
