from flask import Blueprint, jsonify, request

from src.models.invoice_details import InvoiceDetails
from src.models.invoices import Invoices
from src.models.products import Products
from src.models import session
from src.utils.auth import token_required, role_required


invoice_details_bp = Blueprint(
    'invoice_details_v1',
    __name__,
    url_prefix='/api/v1'
)


def invoice_detail_to_dict(detail):
    return {
        'id': detail.id,
        'invoice_id': detail.invoice_id,
        'product_id': detail.product_id,
        'quantity': detail.quantity,
        'unit_price': detail.unit_price,
        'subtotal': detail.quantity * detail.unit_price
    }


@invoice_details_bp.route(
    '/invoices/<int:invoice_id>/details',
    methods=['POST']
)

@token_required
@role_required('ADMIN', 'SELLER')
def post_invoice_detail(current_user, invoice_id):
    data = request.get_json(silent=True) or {}
    errors = {}

    # 1. Buscar la factura
    invoice = Invoices.get_by_id(invoice_id)

    if not invoice:
        return jsonify({
            'success': False,
            'message': 'Invoice not found'
        }), 404

    # 2. Verificar el estado de la factura
    if invoice.active == 0:
        return jsonify({
            'success': False,
            'message': 'Invoice is cancelled and cannot be modified'
        }), 409

    if invoice.completed:
        return jsonify({
            'success': False,
            'message': 'Invoice is completed and cannot be modified'
        }), 409

    # 3. Validar product_id
    product_id = data.get('product_id')

    if product_id is None:
        errors['product_id'] = 'product_id is required'
    else:
        product = Products.get_by_id(product_id)

        if not product:
            errors['product_id'] = 'product_id does not exist'
        elif product.active != 1:
            errors['product_id'] = 'product must be active'

    # 4. Validar quantity
    quantity = data.get('quantity')

    if quantity is None:
        errors['quantity'] = 'quantity is required'
    else:
        try:
            quantity = float(quantity)

            if quantity <= 0:
                errors['quantity'] = 'quantity must be greater than 0'

        except (ValueError, TypeError):
            errors['quantity'] = 'quantity must be a number'

    if errors:
        return jsonify({
            'success': False,
            'message': 'Errors in data validation',
            'validation-errors': errors
        }), 400

    # Continuaremos con la validación del inventario y el registro.

    # 5. Verificar que haya suficiente inventario
    if quantity > product.stock:
        return jsonify({
            'success': False,
            'message': f'not enough stock, available: {product.stock}'
        }), 400

    # 6. Buscar si el producto ya existe en la factura
    detail = InvoiceDetails.get_by_invoice_and_product(
        invoice_id,
        product_id
    )

    if detail:
        detail.quantity += quantity
    else:
        detail = InvoiceDetails(
            invoice_id=invoice_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price
        )
        session.add(detail)

    # 7. Descontar inventario
    product.stock -= quantity

    # 8. Actualizar total de la factura
    invoice.total += quantity * detail.unit_price

    # 9. Guardar los cambios
    session.commit()

    return jsonify({
        'success': True,
        'message': 'Product added to invoice successfully',
        'detail': invoice_detail_to_dict(detail),
        'invoice_total': invoice.total,
        'product_stock': product.stock
    }), 201


@invoice_details_bp.route(
    '/invoices/<int:invoice_id>/details',
    methods=['GET']
)
@token_required
@role_required('ADMIN', 'SELLER')
def get_invoice_details(current_user, invoice_id):

    # 1. Verificar que la factura exista
    invoice = Invoices.get_by_id(invoice_id)

    if not invoice:
        return jsonify({
            'success': False,
            'message': 'Invoice not found'
        }), 404

    # 2. Consultar los detalles de la factura
    details = InvoiceDetails.get_by_invoice(invoice_id)

    # 3. Calcular el subtotal de cada producto
    details_data = [
        invoice_detail_to_dict(detail)
        for detail in details
    ]

    # 4. Responder con los detalles y el total
    return jsonify({
        'invoice_id': invoice.id,
        'details': details_data,
        'invoice_total': invoice.total
    }), 200
