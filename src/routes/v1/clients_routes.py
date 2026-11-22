from flask import Blueprint, jsonify, request

from src.models.clients import Clients, DocumentType
from src.utils.auth import token_required, role_required
import re

clients_bp = Blueprint('clients_v1', __name__, url_prefix='/api/v1')


def client_to_dict(client):
    return {
        'id': client.id,
        'document_type': client.document_type,
        'document_number': client.document_number,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'active': client.active
    }



def validate_client_data(data, is_update=False, client_id=None):
    errors = {}

    fields = [
        'document_type',
        'document_number',
        'name',
        'email',
        'phone',
        'address'
    ]

    for field in fields:
        if is_update and field not in data:
            continue

        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            errors[field] = f'{field} is required'
            continue

        value = value.strip()

        if field == 'document_type':
            if value.upper() not in [
                item.value for item in DocumentType
            ]:
                errors[field] = 'document_type must be one of: CC, NIT, CE'

        elif field == 'document_number':
            existing = Clients.get_by_document_number(value)

            if existing and existing.id != client_id:
                errors[field] = 'document_number must be unique'

        elif field == 'email':
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

            if not re.match(email_pattern, value):
               errors[field] = 'email is not valid'

    if is_update and 'active' in data:
        active = data['active']

        if type(active) is not int or active not in (0, 1):
            errors['active'] = 'active must be 0 or 1'

    return errors



@clients_bp.route('/clients', methods=['GET'])
@token_required
@role_required('ADMIN', 'SELLER')
def get_clients(current_user):
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

    clients, total_clients = Clients.get_paginated(page, per_page)
    total_pages = (total_clients + per_page - 1) // per_page

    return jsonify({
        'data': [client_to_dict(client) for client in clients],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_clients': total_clients,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }), 200


@clients_bp.route('/clients/<int:client_id>', methods=['GET'])
@token_required
@role_required('ADMIN', 'SELLER')
def get_client_by_id(current_user, client_id):
    client = Clients.get_by_id(client_id)

    if not client:
        return jsonify({
            'success': False,
            'message': 'Client not found'
        }), 404

    return jsonify(client_to_dict(client)), 200


@clients_bp.route('/clients', methods=['POST'])
@token_required
@role_required('ADMIN')
def post_clients(current_user):
    data = request.get_json(silent=True) or {}

    errors = validate_client_data(data)

    if errors:
        return jsonify({
            'success': False,
            'message': 'Errors in data validation',
            'validation-errors': errors
        }), 400

    new_client = Clients(
        document_type=data['document_type'].strip().upper(),
        document_number=data['document_number'].strip(),
        name=data['name'].strip(),
        email=data['email'].strip(),
        phone=data['phone'].strip(),
        address=data['address'].strip()
    )

    new_client.save()

    return jsonify(client_to_dict(new_client)), 201


@clients_bp.route('/clients/<int:client_id>', methods=['PUT'])
@token_required
@role_required('ADMIN')
def put_clients(current_user, client_id):
    client = Clients.get_by_id(client_id)

    if not client:
        return jsonify({
            'success': False,
            'message': 'Client not found'
        }), 404

    data = request.get_json(silent=True) or {}

    errors = validate_client_data(
        data,
        is_update=True,
        client_id=client_id
    )

    if errors:
        return jsonify({
            'success': False,
            'message': 'Errors in data validation',
            'validation-errors': errors
        }), 400

    for field in (
        'document_type',
        'document_number',
        'name',
        'email',
        'phone',
        'address'
    ):
        if field in data:
            value = data[field]
            if field == 'document_type':
                value = value.strip().upper()
            elif isinstance(value, str):
                value = value.strip()

            setattr(client, field, value)

    if 'active' in data:
        client.active = data['active']

    client.update()

    return jsonify(client_to_dict(client)), 200
