"""Import every ORM model so SQLAlchemy can build complete metadata."""

from app.models.category import Category
from app.models.contract import Contract
from app.models.contract_price import ContractPrice
from app.models.customer import Customer
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User

__all__ = [
    "Category", "Contract", "ContractPrice", "Customer", "Order",
    "OrderItem", "OrderStatus", "Product", "User", "UserRole",
]
