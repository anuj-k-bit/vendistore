import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from .database import Base

class AgentAuditLog(Base):
    __tablename__ = "agent_audit_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    tool_name = Column(String(100), nullable=False, index=True)
    target_resource = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False, index=True) # ALLOWED, REJECTED, ESCALATED, EXECUTED, FAILED
    policy_name = Column(String(100), nullable=True)
    policy_reason = Column(Text, nullable=True)
    arguments = Column(JSON, nullable=True)
    execution_result = Column(JSON, nullable=True)
