"""
ticket_manager.py
──────────────────
TicketManager — MySQL-backed version.

Original methods preserved (same signatures):
    create_ticket(req: TicketCreate)
    update_ticket_status(req: TicketStatusUpdate, ticket_id)
    list_tickets(employee_id, status)

New bonus methods:
    get_ticket(ticket_id)
    add_comment(ticket_id, author_id, comment)
    get_comments(ticket_id)
    assign_ticket(ticket_id, assignee_id)
"""

from typing import List, Dict, Optional
from .schemas import TicketCreate, TicketStatusUpdate
from .db_connection import db_cursor


class TicketManager:

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_next_ticket_id(self) -> str:
        """Generate next ticket ID in format T0001, T0002 …"""
        with db_cursor() as cur:
            cur.execute(
                "SELECT ticket_id FROM tickets ORDER BY ticket_id DESC LIMIT 1"
            )
            row = cur.fetchone()
        if not row:
            return "T0001"
        last_num = int(row["ticket_id"][1:])
        return f"T{last_num + 1:04d}"

    # ── original methods ──────────────────────────────────────────────────────

    def create_ticket(self, req: TicketCreate) -> str:
        """
        Create a new IT/HR ticket.
        ticket_id is auto-generated in T0001 format.
        """
        ticket_id = self._get_next_ticket_id()
        emp_id = int(req.emp_id)
        category = req.category or "IT Request"
        priority = req.priority or "Medium"

        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO tickets
                   (ticket_id, emp_id, category, item, reason,
                    priority, status)
                   VALUES (%s, %s, %s, %s, %s, %s, 'Open')""",
                (ticket_id, emp_id, category, req.item, req.reason, priority)
            )
        return f"Ticket {ticket_id} created for employee {emp_id}."

    def update_ticket_status(
        self, req: TicketStatusUpdate, ticket_id: str
    ) -> str:
        """Update the status of an existing ticket."""
        resolved_at = "NOW()" if req.status == "Closed" else "NULL"

        with db_cursor() as cur:
            cur.execute(
                f"""UPDATE tickets
                    SET status = %s,
                        resolved_at = {resolved_at}
                    WHERE ticket_id = %s""",
                (req.status, ticket_id)
            )
            if cur.rowcount == 0:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
        return f"Ticket {ticket_id} status updated to '{req.status}'."

    def list_tickets(
        self,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """
        List tickets, optionally filtered by employee and/or status.
        Returns list of ticket dicts.
        """
        sql = "SELECT * FROM tickets WHERE 1=1"
        params = []

        if employee_id:
            sql += " AND emp_id = %s"
            params.append(employee_id)
        if status:
            sql += " AND status = %s"
            params.append(status)

        sql += " ORDER BY FIELD(priority,'Critical','High','Medium','Low'), created_at DESC"

        with db_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    # ── bonus methods ─────────────────────────────────────────────────────────

    def get_ticket(self, ticket_id: str) -> Dict:
        """Return full details of a single ticket."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT t.*,
                          CONCAT(e.first_name,' ',e.last_name) AS raised_by_name,
                          CONCAT(a.first_name,' ',a.last_name) AS assigned_to_name
                   FROM tickets t
                   JOIN employees e ON t.emp_id = e.employee_id
                   LEFT JOIN employees a ON t.assigned_to = a.employee_id
                   WHERE t.ticket_id = %s""",
                (ticket_id,)
            )
            row = cur.fetchone()
        if not row:
            raise ValueError(f"Ticket '{ticket_id}' not found.")
        return row

    def add_comment(
        self, ticket_id: str, author_id: int, comment: str
    ) -> str:
        """Add a comment/reply to a ticket thread."""
        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO ticket_comments (ticket_id, author_id, comment)
                   VALUES (%s, %s, %s)""",
                (ticket_id, author_id, comment)
            )
        return f"Comment added to ticket {ticket_id}."

    def get_comments(self, ticket_id: str) -> List[Dict]:
        """Return all comments for a ticket in chronological order."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT tc.comment_id,
                          CONCAT(e.first_name,' ',e.last_name) AS author,
                          tc.comment, tc.created_at
                   FROM ticket_comments tc
                   JOIN employees e ON tc.author_id = e.employee_id
                   WHERE tc.ticket_id = %s
                   ORDER BY tc.created_at ASC""",
                (ticket_id,)
            )
            return cur.fetchall()

    def assign_ticket(self, ticket_id: str, assignee_id: int) -> str:
        """Assign a ticket to an HR/admin employee."""
        with db_cursor() as cur:
            cur.execute(
                """UPDATE tickets SET assigned_to = %s, status = 'In Progress'
                   WHERE ticket_id = %s""",
                (assignee_id, ticket_id)
            )
            if cur.rowcount == 0:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
        return f"Ticket {ticket_id} assigned to employee {assignee_id}."

    def get_summary(self) -> List[Dict]:
        """Return ticket count grouped by status and priority."""
        with db_cursor() as cur:
            cur.execute("SELECT * FROM v_ticket_summary")
            return cur.fetchall()


# ── quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    tm = TicketManager()
    print("All open tickets:", tm.list_tickets(status="Open"))
    print("Summary:", tm.get_summary())
    print("Ticket T0001:", tm.get_ticket("T0001"))
    print("Comments T0001:", tm.get_comments("T0001"))
