"""
main.py
────────
Entry point for the HRMS MySQL app.
Run this file in PyCharm to test all four managers.

Before running:
    1. Open hrms/db_connection.py and set your MySQL password.
    2. Make sure hr_management_full.sql is already loaded in MySQL.
    3. Run:  pip install mysql-connector-python pydantic
"""

from datetime import date, datetime

from hrms.db_connection import test_connection
from hrms.employee_manager import EmployeeManager
from hrms.leave_manager import LeaveManager
from hrms.meeting_manager import MeetingManager
from hrms.ticket_manager import TicketManager
from hrms.schemas import (
    EmployeeCreate,
    LeaveApplyRequest,
    MeetingCreate,
    MeetingCancelRequest,
    TicketCreate,
    TicketStatusUpdate,
)


#  SECTION 0 — Connection check

def section_connection():
    print("\n" + "="*55)
    print("  CONNECTION TEST")
    print("="*55)
    print(test_connection())



#  SECTION 1 — Employee Manager

def section_employees():
    print("\n" + "="*55)
    print("  EMPLOYEE MANAGER")
    print("="*55)
    em = EmployeeManager()

    print("\n-- Next available employee ID --")
    print(em.get_next_emp_id())

    print("\n-- Employee details (ID=1) --")
    details = em.get_employee_details(1)
    for k, v in details.items():
        print(f"  {k}: {v}")

    print("\n-- Manager of employee 10 --")
    print(em.get_manager(10))

    print("\n-- Direct reports of manager 3 --")
    reports = em.get_direct_reports(3)
    for r in reports[:5]:
        print(f"  {r['employee_id']}: {r['first_name']} {r['last_name']}")

    print("\n-- Search employees named 'Rahul' --")
    results = em.search_employee_by_name("Rahul")
    for r in results:
        print(f"  {r['employee_id']}: {r['first_name']} {r['last_name']}")



#  SECTION 2 — Leave Manager

def section_leaves():
    print("\n" + "="*55)
    print("  LEAVE MANAGER")
    print("="*55)
    lm = LeaveManager()

    print("\n-- Leave balance for employee 10 (Casual Leave) --")
    print(lm.get_leave_balance(10, leave_type_id=1))

    print("\n-- All leave balances for employee 10 --")
    for row in lm.get_all_balances(10):
        print(f"  {row['leave_type']:20s} | Total: {row['total_days']} | "
              f"Used: {row['used_days']} | Remaining: {row['remaining_days']}")

    print("\n-- Leave history for employee 10 --")
    print(lm.get_leave_history(10))

    print("\n-- All leave types --")
    for lt in lm.get_all_leave_types():
        paid = "Paid" if lt["is_paid"] else "Unpaid"
        print(f"  [{lt['leave_type_id']}] {lt['type_name']:25s} {lt['max_days_per_year']} days | {paid}")

    print("\n-- Apply leave for employee 20 (2 days Casual) --")
    req = LeaveApplyRequest(
        emp_id="20",
        leave_dates=[date(2026, 8, 4), date(2026, 8, 5)],
        leave_type_id=1,
        reason="Personal work",
    )
    print(lm.apply_leave(req))

    print("\n-- Pending leave requests for manager 3 --")
    pending = lm.get_pending_requests(3)
    for p in pending[:3]:
        print(f"  #{p['request_id']} | {p['employee_name']} | "
              f"{p['type_name']} | {p['start_date']} → {p['end_date']}")



#  SECTION 3 — Meeting Manager

def section_meetings():
    print("\n" + "="*55)
    print("  MEETING MANAGER")
    print("="*55)
    mm = MeetingManager()

    print("\n-- Upcoming meetings (next 5) --")
    for m in mm.get_upcoming_meetings(5):
        print(f"  #{m['meeting_id']} | {m['meeting_dt']} | {m['topic']} | {m['employee_name']}")

    print("\n-- Meetings for employee 1 --")
    for m in mm.get_meetings(1)[:3]:
        print(f"  #{m['meeting_id']} | {m['meeting_dt']} | {m['topic']} | {m['status']}")

    print("\n-- Participants of meeting 1 --")
    for p in mm.get_participants(1):
        print(f"  {p['name']} — RSVP: {p['rsvp']}")

    print("\n-- Schedule a new meeting --")
    req = MeetingCreate(
        emp_id="5",
        meeting_dt=datetime(2026, 9, 15, 10, 0, 0),
        topic="Q3 Engineering Review",
        location="Conference Room A",
        organised_by="3",
    )
    print(mm.schedule_meeting(req))



#  SECTION 4 — Ticket Manager

def section_tickets():
    print("\n" + "="*55)
    print("  TICKET MANAGER")
    print("="*55)
    tm = TicketManager()

    print("\n-- Ticket summary by status --")
    for row in tm.get_summary():
        print(f"  {row['status']:15s} | Total: {row['total']} | "
              f"Critical: {row['critical']} | High: {row['high']}")

    print("\n-- Open tickets (first 5) --")
    for t in tm.list_tickets(status="Open")[:5]:
        print(f"  {t['ticket_id']} | [{t['priority']}] {t['item']} | emp: {t['emp_id']}")

    print("\n-- Tickets for employee 10 --")
    for t in tm.list_tickets(employee_id=10):
        print(f"  {t['ticket_id']} | {t['item']} | {t['status']}")

    print("\n-- Full details of T0001 --")
    t = tm.get_ticket("T0001")
    print(f"  ID: {t['ticket_id']} | Item: {t['item']} | Status: {t['status']}")
    print(f"  Raised by: {t['raised_by_name']} | Assigned to: {t['assigned_to_name']}")

    print("\n-- Comments on T0001 --")
    for c in tm.get_comments("T0001"):
        print(f"  [{c['created_at']}] {c['author']}: {c['comment']}")

    print("\n-- Create a new ticket --")
    req = TicketCreate(
        emp_id="15",
        item="New laptop",
        reason="Current laptop is 4 years old and slow",
        category="IT Request",
        priority="High",
    )
    print(tm.create_ticket(req))

    print("\n-- Update T0001 to In Progress --")
    upd = TicketStatusUpdate(status="In Progress")
    print(tm.update_ticket_status(upd, "T0001"))



if __name__ == "__main__":
    section_connection()
    section_employees()
    section_leaves()
    section_meetings()
    section_tickets()
    print("\n" + "="*55)
    print("  All sections complete.")
    print("="*55 + "\n")
