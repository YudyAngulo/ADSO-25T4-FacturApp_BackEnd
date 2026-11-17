
from src.routes.v1.products_routes import products_bp


def register_routes(app):  # register the routes with the flask app
    app.register_blueprint(products_bp)  # register the products blueprint