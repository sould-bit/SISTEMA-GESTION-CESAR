"""
🧪 PRUEBAS UNITARIAS PARA ESQUEMAS PYDANTIC DE PRODUCTOS

Estas pruebas validan:
- ✅ Validaciones de precio (positivo, máximo)
- ✅ Validaciones de tasa de impuesto (0-100%)
- ✅ Validaciones de stock (positivo)
- ✅ Campos requeridos y opcionales
- ✅ Validaciones de longitud de strings
- ✅ Validaciones de formato
- ✅ Cálculo de precio final en ProductRead
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.products import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    ProductBase,
    CategoryRead,
    ProductListRead,
    ProductDetailRead
)


class TestProductSchemasValidation:
    """🧪 Pruebas de validación para esquemas Pydantic de productos."""

    # ==================== TESTS PRODUCTCREATE ====================

    @pytest.mark.unit
    def test_product_create_valid_data(self):
        """✅ Test creación de ProductCreate con datos válidos."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Válido",
            description="Descripción válida",
            price=Decimal('99.99'),
            tax_rate=Decimal('0.15'),
            stock=Decimal('50.0'),
            image_url="https://example.com/image.jpg",
            category_id=1
        )

        # Assert
        assert product.name == "Producto Válido"
        assert product.price == Decimal('99.99')
        assert product.tax_rate == Decimal('0.15')
        assert product.stock == Decimal('50.0')
        assert product.is_active is True  # Valor por defecto

    @pytest.mark.unit
    def test_product_create_required_fields_only(self):
        """✅ Test creación con solo campos requeridos."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Mínimo",
            price=Decimal('10.00')
            # Resto de campos opcionales
        )

        # Assert
        assert product.name == "Producto Mínimo"
        assert product.price == Decimal('10.00')
        assert product.tax_rate == Decimal('0')  # Valor por defecto
        assert product.stock is None
        assert product.category_id is None
        assert product.is_active is True

    # ==================== TESTS VALIDACIÓN DE PRECIO ====================

    @pytest.mark.unit
    def test_product_create_price_positive_validation(self):
        """❌ Test precio debe ser positivo."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Inválido",
                price=Decimal('0')  # Precio inválido
            )

        # Pydantic uses "greater than" for gt validation
        errors = str(exc_info.value)
        assert "greater than 0" in errors or "El precio debe ser mayor" in errors

    @pytest.mark.unit
    def test_product_create_price_negative_validation(self):
        """❌ Test precio no puede ser negativo."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Inválido",
                price=Decimal('-10.00')  # Precio negativo
            )

        errors = str(exc_info.value)
        assert "greater than 0" in errors or "El precio debe ser mayor" in errors

    @pytest.mark.unit
    def test_product_create_price_maximum_validation(self):
        """❌ Test precio máximo permitido."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Caro",
                price=Decimal('1000001.00')  # Excede el máximo
            )

        errors = str(exc_info.value)
        assert "El precio no puede exceder" in errors or "less than or equal" in errors

    @pytest.mark.unit
    def test_product_update_price_validation(self):
        """✅ Test validación de precio en actualización."""
        # Arrange & Act - Precio válido
        update = ProductUpdate(price=Decimal('25.50'))
        assert update.price == Decimal('25.50')

        # Act & Assert - Precio inválido
        with pytest.raises(ValidationError):
            ProductUpdate(price=Decimal('0'))

    # ==================== TESTS VALIDACIÓN DE TASA DE IMPUESTO ====================

    @pytest.mark.unit
    def test_product_create_tax_rate_valid_range(self):
        """✅ Test tasa de impuesto en rango válido."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto IVA",
            price=Decimal('100.00'),
            tax_rate=Decimal('0.21')  # 21% IVA
        )

        # Assert
        assert product.tax_rate == Decimal('0.21')

    @pytest.mark.unit
    def test_product_create_tax_rate_zero(self):
        """✅ Test tasa de impuesto cero."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Exento",
            price=Decimal('50.00'),
            tax_rate=Decimal('0')
        )

        # Assert
        assert product.tax_rate == Decimal('0')

    @pytest.mark.unit
    def test_product_create_tax_rate_negative_validation(self):
        """❌ Test tasa de impuesto no puede ser negativa."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Inválido",
                price=Decimal('10.00'),
                tax_rate=Decimal('-0.05')  # Tasa negativa
            )

        errors = str(exc_info.value)
        assert "entre 0% y 100%" in errors or "greater than or equal to 0" in errors or "less than or equal to 1" in errors

    @pytest.mark.unit
    def test_product_create_tax_rate_over_100_percent_validation(self):
        """❌ Test tasa de impuesto no puede exceder 100%."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Inválido",
                price=Decimal('10.00'),
                tax_rate=Decimal('1.5')  # 150%
            )

        errors = str(exc_info.value)
        assert "entre 0% y 100%" in errors or "greater than or equal to 0" in errors or "less than or equal to 1" in errors

    # ==================== TESTS VALIDACIÓN DE STOCK ====================

    @pytest.mark.unit
    def test_product_create_stock_positive(self):
        """✅ Test stock positivo."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Stock",
            price=Decimal('20.00'),
            stock=Decimal('100.5')
        )

        # Assert
        assert product.stock == Decimal('100.5')

    @pytest.mark.unit
    def test_product_create_stock_zero(self):
        """✅ Test stock cero."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Sin Stock",
            price=Decimal('15.00'),
            stock=Decimal('0')
        )

        # Assert
        assert product.stock == Decimal('0')

    @pytest.mark.unit
    def test_product_create_stock_negative_validation(self):
        """❌ Test stock no puede ser negativo."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto Inválido",
                price=Decimal('10.00'),
                stock=Decimal('-5.0')  # Stock negativo
            )

        errors = str(exc_info.value)
        assert "greater than or equal to 0" in errors or "Input should be greater than or equal to 0" in errors

    # ==================== TESTS VALIDACIÓN DE STRINGS ====================

    @pytest.mark.unit
    def test_product_create_name_required(self):
        """❌ Test nombre es requerido."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="",  # Nombre vacío
                price=Decimal('10.00')
            )

        assert "String should have at least 1 character" in str(exc_info.value)

    @pytest.mark.unit
    def test_product_create_name_max_length(self):
        """❌ Test nombre máximo 200 caracteres."""
        # Arrange
        long_name = "A" * 201  # 201 caracteres

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name=long_name,
                price=Decimal('10.00')
            )

        assert "String should have at most 200 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_product_create_description_max_length(self):
        """❌ Test descripción máximo 500 caracteres."""
        # Arrange
        long_description = "A" * 501  # 501 caracteres

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto",
                description=long_description,
                price=Decimal('10.00')
            )

        assert "String should have at most 500 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_product_create_image_url_max_length(self):
        """❌ Test URL de imagen máximo 500 caracteres."""
        # Arrange
        long_url = "https://example.com/" + "a" * 500  # URL muy larga

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto",
                price=Decimal('10.00'),
                image_url=long_url
            )

        assert "String should have at most 500 characters" in str(exc_info.value)

    # ==================== TESTS VALIDACIÓN DE IDs ====================

    @pytest.mark.unit
    def test_product_create_category_id_positive(self):
        """✅ Test category_id positivo."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Categoría",
            price=Decimal('15.00'),
            category_id=5
        )

        # Assert
        assert product.category_id == 5

    @pytest.mark.unit
    def test_product_create_category_id_zero_validation(self):
        """❌ Test category_id debe ser positivo."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto",
                price=Decimal('10.00'),
                category_id=0  # ID inválido
            )

        errors = str(exc_info.value)
        assert "greater than 0" in errors or "Input should be greater than 0" in errors

    @pytest.mark.unit
    def test_product_create_category_id_negative_validation(self):
        """❌ Test category_id no puede ser negativo."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Producto",
                price=Decimal('10.00'),
                category_id=-1  # ID negativo
            )

        errors = str(exc_info.value)
        assert "greater than 0" in errors or "Input should be greater than 0" in errors

    # ==================== TESTS PRODUCTUPDATE ====================

    @pytest.mark.unit
    def test_product_update_all_fields_none(self):
        """✅ Test ProductUpdate con todos los campos None."""
        # Arrange & Act
        update = ProductUpdate()

        # Assert
        assert update.name is None
        assert update.price is None
        assert update.description is None
        assert update.stock is None
        assert update.category_id is None
        assert update.is_active is None

    @pytest.mark.unit
    def test_product_update_partial_fields(self):
        """✅ Test ProductUpdate con campos parciales."""
        # Arrange & Act
        update = ProductUpdate(
            name="Nuevo Nombre",
            price=Decimal('30.00'),
            # Otros campos quedan None
        )

        # Assert
        assert update.name == "Nuevo Nombre"
        assert update.price == Decimal('30.00')
        assert update.description is None

    # ==================== TESTS PRODUCTREAD ====================

    @pytest.mark.unit
    def test_product_read_full_data(self):
        """✅ Test ProductRead con datos completos."""
        # Arrange & Act
        from datetime import datetime

        product = ProductRead(
            id=1,
            company_id=1,
            name="Producto Completo",
            description="Descripción completa",
            price=Decimal('25.00'),
            tax_rate=Decimal('0.10'),
            stock=Decimal('50.0'),
            image_url="https://example.com/image.jpg",
            category_id=2,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=None,
            category=CategoryRead(
                id=2,
                name="Categoría Test",
                is_active=True
            ),
            final_price=Decimal('27.50')  # precio + 10% impuesto
        )

        # Assert
        assert product.id == 1
        assert product.name == "Producto Completo"
        assert product.final_price == Decimal('27.50')
        assert product.category.name == "Categoría Test"

    @pytest.mark.unit
    def test_product_read_calculate_final_price(self):
        """✅ Test cálculo automático de precio final."""
        # Arrange & Act
        from datetime import datetime

        product = ProductRead(
            id=1,
            company_id=1,
            name="Producto Precio",
            price=Decimal('20.00'),
            tax_rate=Decimal('0.15'),  # 15%
            created_at=datetime.utcnow(),
            # final_price no proporcionado, debe calcularse
        )

        # Assert - Precio final = 20 * 1.15 = 23
        expected_final = Decimal('20.00') * (1 + Decimal('0.15'))
        assert product.final_price == expected_final

    @pytest.mark.unit
    def test_product_read_no_tax_rate_final_price_none(self):
        """✅ Test precio final cuando tasa de impuesto es cero."""
        # Arrange & Act
        from datetime import datetime

        product = ProductRead(
            id=1,
            company_id=1,
            name="Producto Sin IVA",
            price=Decimal('10.00'),
            tax_rate=Decimal('0'),  # Sin impuesto
            created_at=datetime.utcnow()
        )

        # Assert - Con tasa 0, precio final = precio * 1.0 = precio
        expected_final = Decimal('10.00') * (1 + Decimal('0'))
        assert product.final_price == expected_final  # 10.00

    # ==================== TESTS CATEGORYREAD ====================

    @pytest.mark.unit
    def test_category_read_basic(self):
        """✅ Test CategoryRead básico."""
        # Arrange & Act
        category = CategoryRead(
            id=1,
            name="Categoría Básica",
            is_active=True
        )

        # Assert
        assert category.id == 1
        assert category.name == "Categoría Básica"
        assert category.is_active is True

    # ==================== TESTS MODEL CONFIG ====================

    @pytest.mark.unit
    def test_schemas_from_attributes_config(self):
        """✅ Test configuración from_attributes en esquemas."""
        # Arrange & Act & Assert
        # Verificar que los esquemas tienen from_attributes=True
        assert ProductBase.model_config['from_attributes'] is True
        assert ProductRead.model_config['from_attributes'] is True
        assert CategoryRead.model_config['from_attributes'] is True

    # ==================== TESTS EDGE CASES ====================

    @pytest.mark.unit
    def test_product_create_decimal_precision(self):
        """✅ Test precisión decimal en precio."""
        # Arrange & Act
        product = ProductCreate(
            name="Producto Preciso",
            price=Decimal('12.3456')  # Más decimales de los que se almacenan
        )

        # Assert - El schema acepta el valor, la BD lo truncará si es necesario
        assert product.price == Decimal('12.3456')

    @pytest.mark.unit
    def test_product_create_minimum_valid_values(self):
        """✅ Test valores mínimos válidos."""
        # Arrange & Act
        product = ProductCreate(
            name="A",  # Nombre mínimo
            price=Decimal('0.01'),  # Precio mínimo válido
            tax_rate=Decimal('0'),  # Tasa mínima
            stock=Decimal('0'),  # Stock mínimo
            category_id=1  # ID mínimo válido
        )

        # Assert
        assert product.name == "A"
        assert product.price == Decimal('0.01')
        assert product.tax_rate == Decimal('0')
        assert product.stock == Decimal('0')
        assert product.category_id == 1

    @pytest.mark.unit
    def test_product_update_empty_strings_allowed(self):
        """❌ Test que strings vacías no son permitidas en update."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdate(name="")  # Nombre vacío no permitido

        assert "String should have at least 1 character" in str(exc_info.value)


