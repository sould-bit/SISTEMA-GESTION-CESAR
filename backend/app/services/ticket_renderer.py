"""
🎨 Ticket Renderer - Renderizado de Tickets PDF
================================================

Responsabilidad ÚNICA: Dibujar/renderizar tickets en formato PDF.
Modificar este archivo para cambiar cómo se ven los tickets.

Estructura:
- TicketConfig: Configuración de estilos (fuentes, colores, márgenes)
- TicketRenderer: Métodos de renderizado
"""

import io
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# Verificar disponibilidad de reportlab
try:
    from reportlab.lib.units import mm as mm_unit
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    mm_unit = 1  # Fallback para que no falle el import


# =============================================================================
# CONFIGURACIÓN DE ESTILOS
# =============================================================================

@dataclass
class TicketConfig:
    """
    Configuración de estilos del ticket.
    
    Modifica estos valores para cambiar la apariencia global.
    """
    # Dimensiones (80mm es estándar para impresoras térmicas)
    width_mm: float = 80
    min_height_mm: float = 200
    margin_left_mm: float = 5
    margin_right_mm: float = 5
    
    # Fuentes
    font_title: str = "Helvetica-Bold"
    font_normal: str = "Helvetica"
    font_italic: str = "Helvetica-Oblique"
    
    # Tamaños de fuente
    size_header: int = 14
    size_subheader: int = 12
    size_normal: int = 10
    size_small: int = 9
    size_tiny: int = 8
    
    # Espaciado
    line_height: float = 10
    separator_dash: tuple = (1, 2)  # (dash_length, gap_length)
    
    # Textos personalizables
    footer_message: str = "¡Gracias por su compra!"
    kitchen_header: str = "*** COCINA ***"
    
    # Etiquetas de tipo de pedido
    delivery_labels: Dict[str, str] = field(default_factory=lambda: {
        "dine_in": "Mesa",
        "takeaway": "Para llevar",
        "delivery": "Domicilio"
    })
    
    # Etiquetas destacadas para cocina
    delivery_labels_kitchen: Dict[str, str] = field(default_factory=lambda: {
        "dine_in": "🍽️ MESA",
        "takeaway": "📦 PARA LLEVAR",
        "delivery": "🛵 DOMICILIO"
    })
    
    @property
    def width(self) -> float:
        return self.width_mm * mm_unit
    
    @property
    def min_height(self) -> float:
        return self.min_height_mm * mm_unit
    
    @property
    def margin_left(self) -> float:
        return self.margin_left_mm * mm_unit
    
    @property
    def margin_right(self) -> float:
        return self.margin_right_mm * mm_unit
    
    @property
    def content_width(self) -> float:
        return self.width - self.margin_left - self.margin_right


# Configuración por defecto (puedes crear variantes)
DEFAULT_CONFIG = TicketConfig()


# =============================================================================
# RENDERER DE TICKETS
# =============================================================================

class TicketRenderer:
    """
    Renderiza tickets en formato PDF.
    
    Para personalizar el diseño:
    1. Modifica los métodos draw_* para cambiar secciones específicas
    2. Crea una subclase y sobrescribe métodos
    3. Pasa una TicketConfig diferente
    """
    
    def __init__(self, config: TicketConfig = None):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab no está instalado. Ejecuta: pip install reportlab")
        self.config = config or DEFAULT_CONFIG
    
    def render_receipt(self, order_data: Dict[str, Any]) -> io.BytesIO:
        """
        Renderiza ticket de caja (con precios).
        
        Args:
            order_data: Diccionario con datos del pedido
            
        Returns:
            BytesIO con el PDF generado
        """
        buffer = io.BytesIO()
        
        # Calcular altura dinámica
        num_items = len(order_data.get("items", []))
        height = self.config.min_height + (num_items * 15 * mm_unit)
        
        c = canvas.Canvas(buffer, pagesize=(self.config.width, height))
        y = height - 10 * mm_unit
        
        # Renderizar secciones
        y = self.draw_header(c, order_data, y)
        y = self.draw_separator(c, y)
        y = self.draw_order_info(c, order_data, y)
        y = self.draw_separator(c, y)
        y = self.draw_items(c, order_data.get("items", []), y)
        y = self.draw_separator(c, y)
        y = self.draw_totals(c, order_data, y)
        self.draw_footer(c, y)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def render_kitchen(self, order_data: Dict[str, Any]) -> io.BytesIO:
        """
        Renderiza ticket de cocina (sin precios).
        
        Args:
            order_data: Diccionario con datos del pedido
            
        Returns:
            BytesIO con el PDF generado
        """
        buffer = io.BytesIO()
        
        num_items = len(order_data.get("items", []))
        height = 150 * mm_unit + (num_items * 20 * mm_unit)
        
        c = canvas.Canvas(buffer, pagesize=(self.config.width, height))
        y = height - 10 * mm_unit
        
        # Encabezado cocina
        y = self.draw_kitchen_header(c, order_data, y)
        y = self.draw_separator(c, y)
        
        # Items (sin precios)
        y = self.draw_kitchen_items(c, order_data.get("items", []), y)
        
        # Notas del cliente
        if order_data.get("customer_notes"):
            y = self.draw_separator(c, y)
            y = self.draw_notes(c, order_data["customer_notes"], y)
        
        # Hora
        y = self.draw_separator(c, y)
        self.draw_time(c, order_data.get("created_at"), y)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    # =========================================================================
    # MÉTODOS DE DIBUJO - MODIFICA ESTOS PARA CAMBIAR EL DISEÑO
    # =========================================================================
    
    def draw_header(self, c, order_data: Dict, y: float) -> float:
        """Dibuja encabezado con nombre de empresa."""
        company_name = order_data.get("company_name", "Mi Restaurante")
        branch_name = order_data.get("branch_name", "")
        
        c.setFont(self.config.font_title, self.config.size_header)
        c.drawCentredString(self.config.width / 2, y, company_name.upper())
        y -= 12
        
        if branch_name:
            c.setFont(self.config.font_normal, self.config.size_normal)
            c.drawCentredString(self.config.width / 2, y, branch_name)
            y -= 10
        
        return y
    
    def draw_kitchen_header(self, c, order_data: Dict, y: float) -> float:
        """Dibuja encabezado para ticket de cocina."""
        c.setFont(self.config.font_title, 16)
        c.drawCentredString(self.config.width / 2, y, self.config.kitchen_header)
        y -= 20
        
        c.setFont(self.config.font_title, self.config.size_header)
        order_number = order_data.get("order_number", "---")
        c.drawCentredString(self.config.width / 2, y, f"PEDIDO {order_number}")
        y -= 15
        
        # Tipo de pedido destacado
        delivery_type = order_data.get("delivery_type", "dine_in")
        label = self.config.delivery_labels_kitchen.get(delivery_type, delivery_type.upper())
        c.setFont(self.config.font_title, self.config.size_subheader)
        c.drawCentredString(self.config.width / 2, y, label)
        y -= 15
        
        return y
    
    def draw_order_info(self, c, order_data: Dict, y: float) -> float:
        """Dibuja información del pedido."""
        c.setFont(self.config.font_title, self.config.size_subheader)
        c.drawString(self.config.margin_left, y, f"Pedido: {order_data.get('order_number', '---')}")
        y -= 12
        
        c.setFont(self.config.font_normal, self.config.size_normal)
        created_at = order_data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                c.drawString(self.config.margin_left, y, f"Fecha: {created_at[:16].replace('T', ' ')}")
            else:
                c.drawString(self.config.margin_left, y, f"Fecha: {created_at.strftime('%d/%m/%Y %H:%M')}")
        y -= 10
        
        delivery_type = order_data.get("delivery_type", "dine_in")
        label = self.config.delivery_labels.get(delivery_type, delivery_type)
        c.drawString(self.config.margin_left, y, f"Tipo: {label}")
        y -= 10
        
        return y
    
    def draw_items(self, c, items: List[Dict], y: float) -> float:
        """Dibuja lista de items con precios."""
        # Encabezado de columnas
        c.setFont(self.config.font_title, self.config.size_normal)
        c.drawString(self.config.margin_left, y, "Cant")
        c.drawString(self.config.margin_left + 12 * mm_unit, y, "Descripción")
        c.drawRightString(self.config.width - self.config.margin_right, y, "Total")
        y -= 12
        
        # Items
        c.setFont(self.config.font_normal, self.config.size_small)
        for item in items:
            product_name = item.get("product_name", f"Item #{item.get('product_id', '?')}")
            quantity = item.get("quantity", 1)
            subtotal = item.get("subtotal", 0)
            
            # Convertir a número si es string
            if isinstance(quantity, str):
                quantity = float(quantity)
            if isinstance(subtotal, str):
                subtotal = float(subtotal)
            
            c.drawString(self.config.margin_left, y, f"{int(quantity)}")
            c.drawString(self.config.margin_left + 12 * mm_unit, y, product_name[:20])
            c.drawRightString(self.config.width - self.config.margin_right, y, f"${subtotal:,.0f}")
            y -= self.config.line_height
        
        return y
    
    def draw_kitchen_items(self, c, items: List[Dict], y: float) -> float:
        """Dibuja items para cocina (sin precios, cantidad destacada)."""
        for item in items:
            product_name = item.get("product_name", f"Producto #{item.get('product_id', '?')}")
            quantity = item.get("quantity", 1)
            if isinstance(quantity, str):
                quantity = float(quantity)
            
            # Cantidad grande
            c.setFont(self.config.font_title, self.config.size_header)
            c.drawString(self.config.margin_left, y, f"{int(quantity)}x")
            
            # Nombre producto
            c.setFont(self.config.font_normal, 11)
            c.drawString(self.config.margin_left + 15 * mm_unit, y, product_name[:25])
            y -= 8
            
            # Notas del item
            notes = item.get("notes")
            if notes:
                c.setFont(self.config.font_italic, self.config.size_small)
                c.drawString(self.config.margin_left + 15 * mm_unit, y, f"→ {notes[:30]}")
                y -= 8
            
            y -= 8
        
        return y
    
    def draw_totals(self, c, order_data: Dict, y: float) -> float:
        """Dibuja totales."""
        c.setFont(self.config.font_normal, self.config.size_normal)
        
        subtotal = order_data.get("subtotal", 0)
        tax_total = order_data.get("tax_total", 0)
        delivery_fee = order_data.get("delivery_fee", 0)
        total = order_data.get("total", 0)
        
        # Convertir strings a números
        for val_name in ["subtotal", "tax_total", "delivery_fee", "total"]:
            val = order_data.get(val_name, 0)
            if isinstance(val, str):
                locals()[val_name] = float(val)
        
        subtotal = float(subtotal) if isinstance(subtotal, str) else subtotal
        tax_total = float(tax_total) if isinstance(tax_total, str) else tax_total
        delivery_fee = float(delivery_fee) if isinstance(delivery_fee, str) else delivery_fee
        total = float(total) if isinstance(total, str) else total
        
        c.drawString(self.config.margin_left, y, "Subtotal:")
        c.drawRightString(self.config.width - self.config.margin_right, y, f"${subtotal:,.0f}")
        y -= self.config.line_height
        
        if tax_total and tax_total > 0:
            c.drawString(self.config.margin_left, y, "IVA:")
            c.drawRightString(self.config.width - self.config.margin_right, y, f"${tax_total:,.0f}")
            y -= self.config.line_height
        
        if delivery_fee and delivery_fee > 0:
            c.drawString(self.config.margin_left, y, "Domicilio:")
            c.drawRightString(self.config.width - self.config.margin_right, y, f"${delivery_fee:,.0f}")
            y -= self.config.line_height
        
        c.setFont(self.config.font_title, self.config.size_subheader)
        c.drawString(self.config.margin_left, y, "TOTAL:")
        c.drawRightString(self.config.width - self.config.margin_right, y, f"${total:,.0f}")
        y -= 12
        
        return y
    
    def draw_notes(self, c, notes: str, y: float) -> float:
        """Dibuja notas del cliente."""
        c.setFont(self.config.font_title, self.config.size_normal)
        c.drawString(self.config.margin_left, y, "NOTAS:")
        y -= 12
        c.setFont(self.config.font_normal, self.config.size_small)
        c.drawString(self.config.margin_left, y, notes[:50])
        y -= 10
        return y
    
    def draw_separator(self, c, y: float) -> float:
        """Dibuja línea separadora punteada."""
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setDash(*self.config.separator_dash)
        c.line(self.config.margin_left, y - 3, self.config.width - self.config.margin_right, y - 3)
        c.setDash()
        return y - 10
    
    def draw_footer(self, c, y: float):
        """Dibuja pie de página."""
        c.setFont(self.config.font_normal, self.config.size_tiny)
        c.drawCentredString(self.config.width / 2, y, self.config.footer_message)
        y -= 10
        c.drawCentredString(self.config.width / 2, y, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    def draw_time(self, c, created_at, y: float):
        """Dibuja hora del pedido."""
        c.setFont(self.config.font_normal, self.config.size_normal)
        if created_at:
            if isinstance(created_at, str):
                time_str = created_at[11:19] if len(created_at) > 19 else created_at
            else:
                time_str = created_at.strftime("%H:%M:%S")
            c.drawCentredString(self.config.width / 2, y, time_str)
