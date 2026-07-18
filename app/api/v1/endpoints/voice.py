from datetime import datetime, date
import re
import random
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.core.config import settings

# Database models
from app.models.user import User, UserRole
from app.models.inventory import Category, Product, Warehouse, Stock
from app.models.crm import Lead, LeadStatus
from app.models.finance import Transaction, TransactionType
from app.models.hr import Employee
from app.models.sales import Customer, Order, OrderStatus
from app.core.security import get_password_hash

router = APIRouter()

class VoiceCommandRequest(BaseModel):
    command: str

@router.post("/voice/command")
def process_voice_command(
    request: VoiceCommandRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    cmd = request.command.strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Command text is empty")
    
    # Try calling OpenAI if API key exists
    parsed = None
    if getattr(settings, "OPENAI_API_KEY", None):
        try:
            parsed = parse_command_with_openai(cmd)
        except Exception as e:
            pass
            
    # Fallback to local NLP rule-engine
    if not parsed:
        parsed = parse_command_locally(cmd)
        
    intent = parsed.get("intent")
    params = parsed.get("parameters", {})
    
    if intent == "navigate":
        page = params.get("page")
        return {
            "intent": "navigate",
            "parameters": {"page": page},
            "response_text": f"Navigating to {page}."
        }
        
    elif intent == "add_product":
        name = params.get("name", "New Product")
        price = params.get("price", 0.0)
        cost = params.get("cost", 0.0)
        
        # 1. Category (find or create general)
        cat = db.query(Category).filter(Category.name == "General").first()
        if not cat:
            cat = Category(name="General", description="General products")
            db.add(cat)
            db.commit()
            db.refresh(cat)
            
        # 2. Product
        sku = f"SKU-{random.randint(10000, 99999)}"
        product = Product(
            sku=sku,
            name=name,
            price=price,
            cost=cost,
            category_id=cat.id
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # 3. Warehouse (find or create main)
        wh = db.query(Warehouse).filter(Warehouse.name == "Main Warehouse").first()
        if not wh:
            wh = Warehouse(name="Main Warehouse", location="Headquarters")
            db.add(wh)
            db.commit()
            db.refresh(wh)
            
        # 4. Stock entry (default 50 items)
        stock = Stock(
            product_id=product.id,
            warehouse_id=wh.id,
            quantity=50
        )
        db.add(stock)
        db.commit()
        
        return {
            "intent": "add_product",
            "parameters": {"name": name, "price": price, "cost": cost},
            "response_text": f"I have added {name} to the inventory with a price of {price} rupees."
        }
        
    elif intent == "add_lead":
        name = params.get("name", "New Lead")
        company = params.get("company", "")
        email = params.get("email", "")
        phone = params.get("phone", "")
        
        lead = Lead(
            name=name,
            company=company,
            email=email,
            phone=phone,
            status=LeadStatus.NEW
        )
        db.add(lead)
        db.commit()
        
        return {
            "intent": "add_lead",
            "parameters": {"name": name, "company": company, "email": email, "phone": phone},
            "response_text": f"Lead for {name} has been added to the CRM."
        }
        
    elif intent == "add_transaction":
        t_type = params.get("type", "Income")
        amount = params.get("amount", 0.0)
        desc = params.get("description", "Voice Transaction")
        
        tx = Transaction(
            type=TransactionType.INCOME if t_type.lower() == "income" else TransactionType.EXPENSE,
            amount=amount,
            description=desc,
            transaction_date=date.today()
        )
        db.add(tx)
        db.commit()
        
        return {
            "intent": "add_transaction",
            "parameters": {"type": t_type, "amount": amount, "description": desc},
            "response_text": f"Recorded {t_type.lower()} of {amount} rupees for {desc}."
        }
        
    elif intent == "add_employee":
        dept = params.get("department", "Operations")
        desig = params.get("designation", "Staff")
        salary = params.get("salary", 25000.0)
        name = params.get("name", f"Employee {random.randint(100, 999)}")
        
        # 1. Create a User first
        email = f"{name.lower().replace(' ', '.') or 'emp'}@company.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=name,
                role=UserRole.EMPLOYEE,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        # 2. Create Employee profile
        existing_emp = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not existing_emp:
            emp = Employee(
                user_id=user.id,
                department=dept,
                designation=desig,
                joining_date=date.today(),
                salary=salary
            )
            db.add(emp)
            db.commit()
            
        return {
            "intent": "add_employee",
            "parameters": {"name": name, "department": dept, "designation": desig, "salary": salary},
            "response_text": f"Added employee {name} in {dept} department as {desig}."
        }
        
    elif intent == "create_order":
        cust_name = params.get("customer_name", "Walk-in Customer")
        email = params.get("email", "")
        amount = params.get("amount", 0.0)
        
        # 1. Customer
        cust = db.query(Customer).filter(Customer.name == cust_name).first()
        if not cust:
            cust = Customer(
                name=cust_name,
                email=email if email else f"{cust_name.lower().replace(' ', '')}@example.com"
            )
            db.add(cust)
            db.commit()
            db.refresh(cust)
            
        # 2. Order
        order = Order(
            customer_id=cust.id,
            status=OrderStatus.PENDING,
            total_amount=amount
        )
        db.add(order)
        db.commit()
        
        return {
            "intent": "create_order",
            "parameters": {"customer_name": cust_name, "amount": amount},
            "response_text": f"Created order for {cust_name} with amount {amount} rupees."
        }
        
    else:
        return {
            "intent": "unknown",
            "parameters": {},
            "response_text": f"I heard you say: '{cmd}'. Try saying: 'go to sales', 'add product Laptop with price 50000', or 'add transaction income of 20000'."
        }

def parse_command_locally(text: str) -> dict:
    text_lower = text.lower()
    
    # Navigation
    nav_match = re.search(r'\b(?:go to|navigate to|open|show|display)\s+(dashboard|inventory|sales|crm|finance|hr|human resources|settings)\b', text_lower)
    if nav_match:
        page = nav_match.group(1)
        if page == "human resources":
            page = "hr"
        return {"intent": "navigate", "parameters": {"page": page}}
        
    # Add Product
    prod_match = re.search(r'\b(?:add|create)\s+product\s+(.*?)\s+(?:with\s+)?price\s*[:\s]*\$?(\d+)(?:\s+and\s+cost\s*[:\s]*\$?(\d+))?', text_lower)
    if prod_match:
        name = prod_match.group(1).title()
        price = float(prod_match.group(2))
        cost = float(prod_match.group(3)) if prod_match.group(3) else price * 0.8
        return {"intent": "add_product", "parameters": {"name": name, "price": price, "cost": cost}}
        
    # Add Transaction
    tx_match = re.search(r'\b(?:add\s+transaction|record)\s+(income|expense)\s+(?:of\s+)?(\d+)(?:\s+for\s+(.*))?\b', text_lower)
    if not tx_match:
        tx_match = re.search(r'\badd\s+(income|expense)\s+(\d+)(?:\s+for\s+(.*))?\b', text_lower)
    if tx_match:
        t_type = tx_match.group(1).capitalize()
        amount = float(tx_match.group(2))
        desc = tx_match.group(3).strip().capitalize() if tx_match.group(3) else f"Voice {t_type}"
        return {"intent": "add_transaction", "parameters": {"type": t_type, "amount": amount, "description": desc}}
        
    # Add Lead
    lead_match = re.search(r'\badd\s+lead\s+([a-zA-Z\s]+?)(?:\s+from\s+company\s+(.*?))?(?:\s+email\s+(\S+))?(?:\s+phone\s+(\S+))?$', text_lower)
    if lead_match:
        name = lead_match.group(1).strip().title()
        company = lead_match.group(2).strip().title() if lead_match.group(2) else "General"
        email = lead_match.group(3).strip() if lead_match.group(3) else ""
        phone = lead_match.group(4).strip() if lead_match.group(4) else ""
        return {"intent": "add_lead", "parameters": {"name": name, "company": company, "email": email, "phone": phone}}
        
    # Add Employee
    emp_match = re.search(r'\badd\s+employee\s+([a-zA-Z\s]+?)\s+in\s+(.*?)\s+(?:department|dept)\s+as\s+(.*?)\s+with\s+salary\s*[:\s]*(\d+)', text_lower)
    if emp_match:
        name = emp_match.group(1).strip().title()
        dept = emp_match.group(2).strip().title()
        desig = emp_match.group(3).strip().title()
        salary = float(emp_match.group(4))
        return {"intent": "add_employee", "parameters": {"name": name, "department": dept, "designation": desig, "salary": salary}}
        
    # Create Order
    order_match = re.search(r'\b(?:create|add)\s+order\s+for\s+([a-zA-Z\s]+?)(?:\s+email\s+(\S+))?\s+(?:with\s+)?amount\s*[:\s]*(\d+)', text_lower)
    if order_match:
        name = order_match.group(1).strip().title()
        email = order_match.group(2).strip() if order_match.group(2) else ""
        amount = float(order_match.group(3))
        return {"intent": "create_order", "parameters": {"customer_name": name, "email": email, "amount": amount}}
        
    return {"intent": "unknown", "parameters": {}}

def parse_command_with_openai(text: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = f"""
You are an AI assistant parsing voice commands for an ERP system.
Supported intents:
1. "navigate": Navigation to pages. Page parameter must be one of: "dashboard", "inventory", "sales", "crm", "finance", "hr", "settings".
2. "add_product": Creating a product. Parameters: "name" (str), "price" (float), "cost" (float).
3. "add_lead": Adding a CRM lead. Parameters: "name" (str), "company" (str), "email" (str), "phone" (str).
4. "add_transaction": Adding finance transaction. Parameters: "type" ("Income" or "Expense"), "amount" (float), "description" (str).
5. "add_employee": Adding employee. Parameters: "name" (str), "department" (str), "designation" (str), "salary" (float).
6. "create_order": Creating sales order. Parameters: "customer_name" (str), "email" (str), "amount" (float).

User input: "{text}"

Output JSON only in this format:
{{
  "intent": "intent_name",
  "parameters": {{ ... }}
}}
If not matching any, return:
{{
  "intent": "unknown",
  "parameters": {{}}
}}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    import json
    return json.loads(response.choices[0].message.content)
