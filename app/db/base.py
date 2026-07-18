# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base

# We will import models here as we create them
from app.models.user import User
from app.models.inventory import Category, Product, Warehouse, Stock
from app.models.sales import Customer, Order, OrderItem
from app.models.hr import Employee, Leave
from app.models.crm import Lead, Opportunity
from app.models.finance import Transaction
