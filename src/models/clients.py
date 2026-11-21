from sqlalchemy import Column, Integer, String
from src.models import Base, session


class Clients(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)
    document_number = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    active = Column(Integer, default=1)

    def __init__(self, name, document_type, document_number, email=None, phone=None, address=None):
        self.name = name
        self.document_type = document_type
        self.document_number = document_number
        self.email = email
        self.phone = phone
        self.address = address

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', document_number='{self.document_number}', active={self.active})>"

    def get_by_id(client_id):
        client = session.query(Clients).filter_by(id=client_id).first()
        return client

    def get_by_document(document_number):
        client = session.query(Clients).filter_by(document_number=document_number).first()
        return client

    def save(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()
