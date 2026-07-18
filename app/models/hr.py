from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base_class import Base

class LeaveType(str, enum.Enum):
    SICK = "Sick"
    CASUAL = "Casual"
    EARNED = "Earned"
    UNPAID = "Unpaid"

class LeaveStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    department = Column(String, index=True)
    designation = Column(String)
    joining_date = Column(Date)
    salary = Column(Float)

    user = relationship("User")
    leaves = relationship("Leave", back_populates="employee")

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    leave_type = Column(Enum(LeaveType))
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(String)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)

    employee = relationship("Employee", back_populates="leaves")
