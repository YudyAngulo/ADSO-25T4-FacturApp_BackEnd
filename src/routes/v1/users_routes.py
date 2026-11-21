from flask import Blueprint, jsonify, request

from src.models.users import Users, Role
from src.utils.auth import token_required, role_required


users_bp = Blueprint('users_v1', __name__, url_prefix='/api/v1')


@users_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@role_required('ADMIN')
def update_user_role(current_user, user_id):

    user = Users.get_by_id(user_id)

    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404

    data = request.get_json()

    if not data or 'role' not in data:
        return jsonify({
            'success': False,
            'message': 'Role is required'
        }), 400

    new_role = data.get('role')

    if new_role not in [role.value for role in Role]:
        return jsonify({
            'success': False,
            'message': 'Invalid role'
        }), 400

    user.role = new_role
    user.update()

    return jsonify({
        'success': True,
        'message': 'User role updated successfully',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 200