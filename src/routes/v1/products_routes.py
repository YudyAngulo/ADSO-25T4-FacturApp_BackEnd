from flask import Blueprint, jsonify, request
from src.models.products import Products
from sqlalchemy import Float

products_bp = Blueprint('products_v1', __name__, url_prefix="/api/v1")

@products_bp.route('/products', methods=['GET'])
def get_products():
    page = 1
    per_page = 3
    products, total_products = Products.get_paginated(page=page, per_page=per_page)
    total_pages = (total_products + per_page - 1) // per_page  # calculate total pages based on per_page=3
    return jsonify({     
        "data":  
                [{
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'category_id': product.category_id,
                'active': product.active
            } for product in products],
            "meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_products": total_products,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }      
     ), 200

@products_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    product = Products.get_by_id(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "descriptio": product.description,
            "price": product.price,
            "stock": product.stock,
            "category_id": product.category_id,
            "active": product.active,
        })
    else:
        return jsonify({"success": False,
                         "message": "product not found"}), 404

@products_bp.route("/products",methods=["POST"])
def post_products():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock', 0)
    category_id = data.get('category_id')
    errors = {}
    if not name:
        errors["neme"] = "name is required"
    if not price:
        errors["price"] = 'price is required'
    else:
        try:
            price = float(price)
            if price < 0:
                errors["price"] = "price must be a non-negative number"
        except ValueError:
            errors["price"] = "price must be a number"
    if not category_id:
        errors["category_id"] = 'category_id is required'
    if errors:
       return jsonify({ "success": False,
                        "validation-error": errors
                     }), 400    
                      
    existing_product = Products.get_by_name(name)

    if existing_product:
        return jsonify({'error': 'Nombre duplicado'}), 409
   
    new_product = Products(name=name, description=description, price=price, stock=stock, category_id=category_id)
    
    Products.save(new_product)

    return jsonify({
        'id': new_product.id,
        'name': new_product.name,
        'description': new_product.description,
        'price': new_product.price,
        'stock': new_product.stock,
        'category_id': new_product.category_id,
        'active': new_product.active
      }), 201


def validar_numero(valor, campo, errores):
    try:
        numero = float(valor)

        if numero < 0:
            errores[campo] = f'{campo} must be a non-negative number'
            return None

        return numero

    except (ValueError, TypeError):
        errores[campo] = f'{campo} must be a number'
        return None


@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def put_products(product_id):

    product = Products.get_by_id(product_id)

    if not product:
        return jsonify({
            'success': False,
            'message': 'Product not found'
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required'
        }), 400

    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    category_id = data.get('category_id')

    errors = {}

    # Validar precio
    if price is not None:
        price = validar_numero(price, 'price', errors)

    # Validar stock
    if stock is not None:
        stock = validar_numero(stock, 'stock', errors)

    # Retornar errores de validación
    if errors:
        return jsonify({
            'success': False,
            'message': 'Errors in data validation',
            'validation-errors': errors
        }), 400

    # Actualizar únicamente los campos enviados
    if name is not None:
        product.name = name

    if description is not None:
        product.description = description

    if price is not None:
        product.price = price

    if stock is not None:
        product.stock = stock

    if category_id is not None:
        product.category_id = category_id

    # Guardar actualización
        product.update()

    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'category_id': product.category_id,
        'active': product.active
    })
