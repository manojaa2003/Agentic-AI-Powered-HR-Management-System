# HRMS — MySQL Edition

Full HRMS app connected to MySQL (`hr_management` database).

## Project structure

```
hrms_mysql/
├── main.py                  ← run this to test everything
├── requirements.txt
└── hrms/
    ├── db_connection.py     ← set your MySQL password here
    ├── schemas.py
    ├── employee_manager.py
    ├── leave_manager.py
    ├── meeting_manager.py
    └── ticket_manager.py
```

## Setup (3 steps)

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. Load the database**  
In MySQL Workbench: `File → Open SQL Script → hr_management_full.sql → Run`  
Or terminal:
```
mysql -u root -p < hr_management_full.sql
```

**3. Set your password**  
Open `hrms/db_connection.py` and change:
```python
"password": "your_password_here",
```

Then run `main.py` in PyCharm.

## Quick usage

```python
from hrms.employee_manager import EmployeeManager
from hrms.leave_manager import LeaveManager
from hrms.meeting_manager import MeetingManager
from hrms.ticket_manager import TicketManager

em = EmployeeManager()
lm = LeaveManager()
mm = MeetingManager()
tm = TicketManager()

# employee
print(em.get_employee_details(1))
print(em.get_direct_reports(3))
print(em.search_employee_by_name("Rahul"))

# leave
print(lm.get_leave_balance(10))
print(lm.get_leave_history(10))
print(lm.get_pending_requests(3))
lm.approve_leave(request_id=1, approver_id=3)

# meetings
print(mm.get_upcoming_meetings())
print(mm.get_meetings(employee_id=5))

# tickets
print(tm.list_tickets(status="Open"))
print(tm.get_ticket("T0001"))
tm.add_comment("T0001", author_id=11, comment="Working on this.")
```
