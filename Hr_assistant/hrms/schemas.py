"""
schemas.py
──────────
Pydantic data models (schemas) for the HRMS app.
Unchanged from the original — these define the shape of data
passed into each manager's methods.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import date, datetime


# ── Employee schemas ──────────────────────────────────────────────────────────

class EmployeeBase(BaseModel):
    emp_id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Full name of the employee")
    manager_id: Optional[str] = Field(None, description="Manager's employee ID, if any")
    email: Optional[str] = Field(None, description="Email address of the employee")

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreate(BaseModel):
    emp_id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Full name of the employee")
    manager_id: Optional[str] = Field(None, description="Manager's employee ID, if any")
    email: Optional[str] = Field(None, description="Email address of the employee")


class EmployeeRead(EmployeeBase):
    hired_date: date = Field(..., description="Date the employee was hired")


# ── Leave schemas ─────────────────────────────────────────────────────────────

class LeaveBalance(BaseModel):
    emp_id: str = Field(..., description="Employee identifier")
    balance: int = Field(..., ge=0, description="Current leave balance")

    model_config = ConfigDict(from_attributes=True)


class LeaveHistoryItem(BaseModel):
    history_id: int = Field(..., description="Auto-incremented history record ID")
    emp_id: str = Field(..., description="Employee identifier")
    leave_date: date = Field(..., description="Date of leave taken")
    request_id: int = Field(..., description="Identifier grouping multi-day leave requests")

    model_config = ConfigDict(from_attributes=True)


class LeaveApplyRequest(BaseModel):
    emp_id: str = Field(..., description="Employee identifier")
    leave_dates: List[date] = Field(..., description="List of leave dates to apply for")
    leave_type_id: int = Field(1, description="Leave type: 1=Casual, 2=Sick, 3=Earned, etc.")
    reason: Optional[str] = Field(None, description="Reason for the leave")


# ── Meeting schemas ───────────────────────────────────────────────────────────

class MeetingBase(BaseModel):
    emp_id: str = Field(..., description="Employee identifier")
    meeting_dt: datetime = Field(..., description="Scheduled date and time of the meeting")
    topic: str = Field(..., description="Topic or subject of the meeting")

    model_config = ConfigDict(from_attributes=True)


class MeetingCreate(MeetingBase):
    location: Optional[str] = Field("Online", description="Meeting location or platform")
    organised_by: Optional[str] = Field(None, description="Organiser's employee ID")


class MeetingRead(MeetingBase):
    meeting_id: int = Field(..., description="Auto-incremented meeting ID")
    location: Optional[str] = None
    status: str = Field("scheduled", description="scheduled / cancelled / completed")


class MeetingCancelRequest(BaseModel):
    emp_id: str = Field(..., description="Employee identifier")
    meeting_dt: datetime = Field(..., description="DateTime of meeting to cancel")
    topic: Optional[str] = Field(None, description="Optional topic to match")


# ── Ticket schemas ────────────────────────────────────────────────────────────

TicketStatus = Literal["Open", "In Progress", "Closed", "Rejected"]


class TicketBase(BaseModel):
    emp_id: str = Field(..., description="Employee identifier")
    item: str = Field(..., description="Requested item name")
    reason: str = Field(..., description="Reason for the request")

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(TicketBase):
    category: Optional[str] = Field("IT Request", description="Ticket category")
    priority: Optional[str] = Field("Medium", description="Low / Medium / High / Critical")


class TicketRead(TicketBase):
    ticket_id: str = Field(..., description="Ticket identifier, e.g. 'T0001'")
    status: TicketStatus = Field(..., description="Current status of the ticket")
    created_at: datetime = Field(..., description="Timestamp when the ticket was created")
    updated_at: datetime = Field(..., description="Timestamp when the ticket was last updated")


class TicketStatusUpdate(BaseModel):
    status: TicketStatus = Field(..., description="New ticket status")
