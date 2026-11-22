from flask import Blueprint, jsonify, request

from src.models.invoices import Invoices
from src.models.clients import Clients
from src.models.users import Users, Role
from src.utils.auth import token_required, role_required


invoices_bp = Blueprint('invoices_v1', __name__, url_prefix='/api/v1')


def invoice_to_dict(invoice):
    return {
        'id': invoice.id,
        'client_id': invoice.client_id,
        'user_id': invoice.user_id,
        'date': invoice.date.isoformat(),
        'total': invoice.total,
        'completed': invoice.completed,
        'active': invoice.active
    }


@invoices_bp.route('/invoices', methods=['POST'])
@token_required
@role_required('ADMIN', 'SELLER')
def post_invoices(current_user):
    data = request.get_json(silent=True) or {}
    errors = {}

    client_id = data.get('client_id')
    user_id = data.get('user_id')

    # Validar cliente
    if client_id is None:
        errors['client_id'] = 'client_id is required'
    else:
        client = Clients.get_by_id(client_id)

        if not client:
            errors['client_id'] = 'client_id does not exist'
        elif client.active != 1:
            errors['client_id'] = 'client must be active'

    # Validar vendedor
    if user_id is None:
        errors['user_id'] = 'user_id is required'
    else:
        seller = Users.get_by_id(user_id)

        if not seller:
            errors['user_id'] = 'user_id does not exist'
        elif seller.active != 1:
            errors['user_id'] = 'user must be active'
        elif seller.role != Role.SELLER:
            errors['user_id'] = 'user must have SELLER role'

    # Un SELLER solo puede crear facturas a su nombre
    if current_user.role == 'SELLER' and user_id != current_user.id:
        errors['user_id'] = 'SELLER can only create invoices with their own user_id'

    if errors:
        return jsonify({
            'success': False,
            'message': 'Errors in data validation',
            'validation-errors': errors
        }), 400

    new_invoice = Invoices(
        client_id=client_id,
        user_id=user_id
    )

    new_invoice.save()

    return jsonify(invoice_to_dict(new_invoice)), 201


@invoices_bp.route('/invoices', methods=['GET'])
@token_required
@role_required('ADMIN', 'SELLER')
def get_invoices(current_user):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 3))

        if page < 1 or per_page < 1:
            raise ValueError

    except ValueError:
        return jsonify({
            'success': False,
            'message': 'page and per_page must be positive integers'
        }), 400

    invoices, total_invoices = Invoices.get_paginated(page, per_page)
    total_pages = (total_invoices + per_page - 1) // per_page

    return jsonify({
        'data': [invoice_to_dict(invoice) for invoice in invoices],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_invoices': total_invoices,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }), 200


@invoices_bp.route('/invoices/<int:invoice_id>', methods=['GET'])
@token_required
@role_required('ADMIN', 'SELLER')
def get_invoice_by_id(current_user, invoice_id):
    invoice = Invoices.get_by_id(invoice_id)

    if not invoice:
        return jsonify({
            'success': False,
            'message': 'Invoice not found'
        }), 404

    return jsonify(invoice_to_dict(invoice)), 200
