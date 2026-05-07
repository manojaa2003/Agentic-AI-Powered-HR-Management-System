"""
employee_manager.py
────────────────────
EmployeeManager — MySQL-backed version.

Every method that previously read/wrote an in-memory dict now
hits the hr_management database instead.

Original methods preserved (same signatures):
    get_next_emp_id()
    add_employee(emp: EmployeeCreate)
    get_manager(emp_id)
    search_employee_by_name(name_query, n, cutoff)
    get_employee_details(emp_id)
    get_direct_reports(manager_id)
"""

from typing import List, Dict, Optional
from .schemas import EmployeeCreate
from .db_connection import db_cursor


class EmployeeManager:

    # ── helpers ───────────────────────────────────────────────────────────────

    def _employee_exists(self, emp_id: int) -> bool:
        with db_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM employees WHERE employee_id = %s",
                (emp_id,)
            )
            return cur.fetchone() is not None

    # ── original methods ──────────────────────────────────────────────────────

    def get_next_emp_id(self) -> int:
        """
        Return the next available employee_id (MAX + 1).
        The DB uses INT AUTO_INCREMENT, so this is just a preview.
        """
        with db_cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(employee_id), 0) + 1 AS next_id FROM employees")
            row = cur.fetchone()
        return row["next_id"]

    def add_employee(self, emp: EmployeeCreate) -> str:
        """
        Insert a new employee row.
        emp_id in EmployeeCreate maps to employee_id (INT) in the DB.
        Raises ValueError if employee already exists or manager is invalid.
        """
        emp_id = int(emp.emp_id)

        if self._employee_exists(emp_id):
            raise ValueError(f"Employee ID {emp_id} already exists.")

        manager_id = int(emp.manager_id) if emp.manager_id else None
        if manager_id and not self._employee_exists(manager_id):
            raise ValueError(f"Manager ID {manager_id} does not exist.")

        # Split name into first/last (original schema stored a single 'name')
        parts = emp.name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO employees
                   (employee_id, first_name, last_name, email,
                    role_id, department_id, manager_id, hire_date,
                    employment_type, status, salary)
                   VALUES (%s, %s, %s, %s, 25, 1, %s, CURDATE(),
                           'Full-Time', 'active', 0)""",
                (emp_id, first_name, last_name, emp.email, manager_id)
            )
        return f"Employee {emp_id} ({emp.name}) added successfully."

    def get_manager(self, emp_id: int) -> str:
        """Return manager's ID and full name for the given employee."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT
                       e.manager_id,
                       CONCAT(m.first_name,' ',m.last_name) AS manager_name
                   FROM employees e
                   LEFT JOIN employees m ON e.manager_id = m.employee_id
                   WHERE e.employee_id = %s""",
                (emp_id,)
            )
            row = cur.fetchone()

        if not row:
            raise ValueError(f"Employee ID {emp_id} not found.")
        if not row["manager_id"]:
            return "No manager assigned."
        return f"{row['manager_id']}: {row['manager_name']}"

    def search_employee_by_name(
        self, name_query: str, n: int = 5, cutoff: float = 0.6
    ) -> List[Dict]:
        """
        Fuzzy name search using MySQL FULLTEXT index.
        Returns list of matching employee dicts.
        (Original used difflib — DB FULLTEXT is faster and persistent.)
        """
        with db_cursor() as cur:
            cur.execute(
                """SELECT employee_id, first_name, last_name, email,
                          role_id, manager_id
                   FROM employees
                   WHERE MATCH(first_name, last_name)
                         AGAINST (%s IN BOOLEAN MODE)
                   LIMIT %s""",
                (name_query, n)
            )
            rows = cur.fetchall()
        return rows

    def get_employee_details(self, emp_id: int) -> Dict:
        """Return full employee record from v_employee_details view."""
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM v_employee_details WHERE employee_id = %s",
                (emp_id,)
            )
            row = cur.fetchone()
        if not row:
            raise ValueError(f"Employee ID {emp_id} not found.")
        return row

    def get_direct_reports(self, manager_id: int) -> List[Dict]:
        """Return all employees whose manager_id matches."""
        if not self._employee_exists(manager_id):
            raise ValueError(f"Manager ID {manager_id} not found.")
        with db_cursor() as cur:
            cur.execute(
                """SELECT employee_id, first_name, last_name,
                          email, role_id, status
                   FROM employees
                   WHERE manager_id = %s
                   ORDER BY first_name""",
                (manager_id,)
            )
            rows = cur.fetchall()
        return rows

    def list_all_employees(self, status: str = "active") -> List[Dict]:
        """Bonus: list all employees filtered by status."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT employee_id, first_name, last_name,
                          email, role_id, department_id, status
                   FROM employees
                   WHERE status = %s
                   ORDER BY employee_id""",
                (status,)
            )
            return cur.fetchall()

    def update_employee_status(self, emp_id: int, status: str) -> str:
        """Bonus: set active / inactive / on_leave."""
        valid = {"active", "inactive", "on_leave"}
        if status not in valid:
            raise ValueError(f"Status must be one of {valid}")
        with db_cursor() as cur:
            cur.execute(
                "UPDATE employees SET status = %s WHERE employee_id = %s",
                (status, emp_id)
            )
            if cur.rowcount == 0:
                raise ValueError(f"Employee ID {emp_id} not found.")
        return f"Employee {emp_id} status updated to '{status}'."


# ── quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    em = EmployeeManager()
    print("Next ID :", em.get_next_emp_id())
    print("Manager :", em.get_manager(10))
    print("Details :", em.get_employee_details(1))
    print("Reports :", em.get_direct_reports(3))
    print("Search  :", em.search_employee_by_name("Rahul"))
