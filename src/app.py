from flask import Flask
from src.models import Base, engine
from src.models.categories import Categories
from src.models.products import Products
from src.models.clients import Clients
from src.models.invoices import Invoices
from src.models.invoice_details import InvoiceDetails

from src.routes import register_routes


app = Flask(__name__)

register_routes(app)  # register the routes with the flask app

app.config["JWT_SECRET_KEY"] = "your_secret_key"  # change this to a secure key in production

Base.metadata.create_all(engine)

@app.route('/')
def health():
    return {
             "success": True,
             "message": "API is running"
    }

if __name__ == '__main__':
    app.run(debug=True)