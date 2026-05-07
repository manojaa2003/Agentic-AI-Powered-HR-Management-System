"""
leave_manager.py
─────────────────
LeaveManager — MySQL-backed version.

Original methods preserved (same signatures):
    get_leave_balance(employee_id)
    apply_leave(req: LeaveApplyRequest)
    get_leave_history(employee_id)

New methods:
    get_all_leave_types()
    get_pending_requests(manager_id)
    approve_leave(request_id, approver_id, comments)
    reject_leave(request_id, approver_id, comments)
"""

from typing import List, Dict, Optional
from .schemas import LeaveApplyRequest
from .db_connection import db_cursor


class LeaveManager:

    # ── original methods ──────────────────────────────────────────────────────

    def get_leave_balance(self, employee_id: int, leave_type_id: int = 1) -> str:
        """
        Return remaining leave balance for an employee.
        Default leave_type_id=1 (Casual Leave) to match original 'generic balance'.
        """
        with db_cursor() as cur:
            cur.execute(
                """SELECT lt.type_name,
                          lb.total_days,
                          lb.used_days,
                          ROUND(lb.total_days - lb.used_days, 1) AS remaining
                   FROM leave_balances lb
                   JOIN leave_types lt ON lb.leave_type_id = lt.leave_type_id
                   WHERE lb.employee_id = %s
                     AND lb.leave_type_id = %s
                     AND lb.year = YEAR(CURDATE())""",
                (employee_id, leave_type_id)
            )
            row = cur.fetchone()

        if not row:
            return f"No leave balance record found for employee {employee_id}."
        return (
            f"Employee {employee_id} | {row['type_name']} | "
            f"Total: {row['total_days']} | Used: {row['used_days']} | "
            f"Remaining: {row['remaining']} days."
        )

    def apply_leave(self, req: LeaveApplyRequest) -> str:
        """
        Apply for leave on the given dates.
        Checks balance, inserts into leave_requests, and deducts used_days.
        """
        employee_id = int(req.emp_id)
        leave_type_id = req.leave_type_id
        requested_days = len(req.leave_dates)
        reason = req.reason or "Personal"

        # 1. check balance
        with db_cursor() as cur:
            cur.execute(
                """SELECT ROUND(total_days - used_days, 1) AS remaining
                   FROM leave_balances
                   WHERE employee_id = %s
                     AND leave_type_id = %s
                     AND year = YEAR(CURDATE())""",
                (employee_id, leave_type_id)
            )
            row = cur.fetchone()

        if not row:
            return f"No leave balance record found for employee {employee_id}."

        available = float(row["remaining"])
        if available < requested_days:
            return (
                f"Insufficient balance: requested {requested_days}, "
                f"available {available}."
            )

        # 2. insert leave request
        start_date = min(req.leave_dates)
        end_date = max(req.leave_dates)

        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO leave_requests
                   (employee_id, leave_type_id, start_date, end_date,
                    total_days, status, reason)
                   VALUES (%s, %s, %s, %s, %s, 'pending', %s)""",
                (employee_id, leave_type_id, start_date, end_date,
                 requested_days, reason)
            )
            request_id = cur.lastrowid

        return (
            f"Leave request #{request_id} submitted for {requested_days} day(s) "
            f"({start_date} to {end_date}). Status: pending."
        )

    def get_leave_history(self, employee_id: int) -> str:
        """Return all past leave requests for an employee."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT lr.request_id, lt.type_name, lr.start_date,
                          lr.end_date, lr.total_days, lr.status
                   FROM leave_requests lr
                   JOIN leave_types lt ON lr.leave_type_id = lt.leave_type_id
                   WHERE lr.employee_id = %s
                   ORDER BY lr.start_date DESC""",
                (employee_id,)
            )
            rows = cur.fetchall()

        if not rows:
            return f"No leave history found for employee {employee_id}."

        lines = [f"Leave history for employee {employee_id}:"]
        for r in rows:
            lines.append(
                f"  #{r['request_id']} | {r['type_name']} | "
                f"{r['start_date']} → {r['end_date']} "
                f"({r['total_days']} day(s)) | {r['status']}"
            )
        return "\n".join(lines)

    # ── bonus methods ─────────────────────────────────────────────────────────

    def get_all_leave_types(self) -> List[Dict]:
        """Return all leave types from leave_types table."""
        with db_cursor() as cur:
            cur.execute("SELECT * FROM leave_types ORDER BY leave_type_id")
            return cur.fetchall()

    def get_all_balances(self, employee_id: int) -> List[Dict]:
        """Return all leave type balances for an employee for current year."""
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM v_leave_summary WHERE employee_id = %s AND year = YEAR(CURDATE())",
                (employee_id,)
            )
            return cur.fetchall()

    def get_pending_requests(self, manager_id: int) -> List[Dict]:
        """Return all pending leave requests for employees under a manager."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT lr.request_id, lr.employee_id,
                          CONCAT(e.first_name,' ',e.last_name) AS employee_name,
                          lt.type_name, lr.start_date, lr.end_date,
                          lr.total_days, lr.reason, lr.applied_on
                   FROM leave_requests lr
                   JOIN employees e  ON lr.employee_id  = e.employee_id
                   JOIN leave_types lt ON lr.leave_type_id = lt.leave_type_id
                   WHERE e.manager_id = %s AND lr.status = 'pending'
                   ORDER BY lr.applied_on""",
                (manager_id,)
            )
            return cur.fetchall()

    def approve_leave(
        self, request_id: int, approver_id: int, comments: str = "Approved."
    ) -> str:
        """Approve a leave request and deduct balance."""
        with db_cursor() as cur:
            # get request details
            cur.execute(
                "SELECT employee_id, leave_type_id, total_days, status FROM leave_requests WHERE request_id = %s",
                (request_id,)
            )
            req = cur.fetchone()

        if not req:
            raise ValueError(f"Request #{request_id} not found.")
        if req["status"] != "pending":
            return f"Request #{request_id} is already '{req['status']}'."

        with db_cursor() as cur:
            # update request status
            cur.execute(
                "UPDATE leave_requests SET status='approved' WHERE request_id = %s",
                (request_id,)
            )
            # insert approval record
            cur.execute(
                """INSERT INTO leave_approvals (request_id, approver_id, action, comments)
                   VALUES (%s, %s, 'approved', %s)""",
                (request_id, approver_id, comments)
            )
            # deduct from balance
            cur.execute(
                """UPDATE leave_balances
                   SET used_days = used_days + %s
                   WHERE employee_id = %s AND leave_type_id = %s
                     AND year = YEAR(CURDATE())""",
                (req["total_days"], req["employee_id"], req["leave_type_id"])
            )
        return f"Request #{request_id} approved. {req['total_days']} day(s) deducted."

    def reject_leave(
        self, request_id: int, approver_id: int, comments: str = "Rejected."
    ) -> str:
        """Reject a pending leave request."""
        with db_cursor() as cur:
            cur.execute(
                "SELECT status FROM leave_requests WHERE request_id = %s",
                (request_id,)
            )
            row = cur.fetchone()

        if not row:
            raise ValueError(f"Request #{request_id} not found.")
        if row["status"] != "pending":
            return f"Request #{request_id} is already '{row['status']}'."

        with db_cursor() as cur:
            cur.execute(
                "UPDATE leave_requests SET status='rejected' WHERE request_id = %s",
                (request_id,)
            )
            cur.execute(
                """INSERT INTO leave_approvals (request_id, approver_id, action, comments)
                   VALUES (%s, %s, 'rejected', %s)""",
                (request_id, approver_id, comments)
            )
        return f"Request #{request_id} rejected."


if __name__ == "__main__":
    from datetime import date
    lm = LeaveManager()

    print(lm.get_leave_balance(10))
    print(lm.get_leave_history(10))
    print("Types:", lm.get_all_leave_types())
    print("All balances:", lm.get_all_balances(10))
    print("Pending for manager 3:", lm.get_pending_requests(3))
