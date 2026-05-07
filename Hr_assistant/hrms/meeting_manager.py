"""
meeting_manager.py
───────────────────
MeetingManager — MySQL-backed version.

Original methods preserved (same signatures):
    schedule_meeting(req: MeetingCreate)
    get_meetings(employee_id)
    cancel_meeting(req: MeetingCancelRequest)

New methods:
    get_upcoming_meetings()
    add_participant(meeting_id, emp_id, rsvp)
    get_participants(meeting_id)
"""

from typing import List, Dict
from .schemas import MeetingCreate, MeetingCancelRequest
from .db_connection import db_cursor


class MeetingManager:

    # ── original methods ──────────────────────────────────────────────────────

    def schedule_meeting(self, req: MeetingCreate) -> str:
        """
        Schedule a new meeting.
        Raises ValueError on datetime conflict for the same employee
        (enforced by UNIQUE KEY uq_emp_meeting_dt in the DB).
        """
        emp_id = int(req.emp_id)
        organised_by = int(req.organised_by) if req.organised_by else emp_id
        location = req.location or "Online"

        try:
            with db_cursor() as cur:
                cur.execute(
                    """INSERT INTO meetings
                       (emp_id, meeting_dt, topic, location, status, organised_by)
                       VALUES (%s, %s, %s, %s, 'scheduled', %s)""",
                    (emp_id, req.meeting_dt, req.topic, location, organised_by)
                )
                meeting_id = cur.lastrowid
        except Exception as e:
            if "Duplicate entry" in str(e) or "uq_emp_meeting_dt" in str(e):
                raise ValueError(
                    f"Conflict: employee {emp_id} already has a meeting "
                    f"at {req.meeting_dt}."
                )
            raise

        return (
            f"Meeting #{meeting_id} scheduled for employee {emp_id} "
            f"on {req.meeting_dt} about '{req.topic}'."
        )

    def get_meetings(self, employee_id: int) -> List[Dict]:
        """Return all meetings for an employee, sorted by date ascending."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT meeting_id, meeting_dt, topic, location, status
                   FROM meetings
                   WHERE emp_id = %s
                   ORDER BY meeting_dt ASC""",
                (employee_id,)
            )
            return cur.fetchall()

    def cancel_meeting(self, req: MeetingCancelRequest) -> str:
        """
        Cancel a meeting by employee + datetime (+ optional topic match).
        Sets status = 'cancelled' instead of deleting (keeps audit trail).
        """
        emp_id = int(req.emp_id)
        dt_str = req.meeting_dt

        with db_cursor() as cur:
            if req.topic:
                cur.execute(
                    """UPDATE meetings SET status = 'cancelled'
                       WHERE emp_id = %s AND meeting_dt = %s AND topic = %s
                         AND status = 'scheduled'""",
                    (emp_id, dt_str, req.topic)
                )
            else:
                cur.execute(
                    """UPDATE meetings SET status = 'cancelled'
                       WHERE emp_id = %s AND meeting_dt = %s
                         AND status = 'scheduled'""",
                    (emp_id, dt_str)
                )
            affected = cur.rowcount

        if affected == 0:
            raise ValueError(
                f"No scheduled meeting found for employee {emp_id} "
                f"at {dt_str}"
                + (f" about '{req.topic}'" if req.topic else "") + "."
            )
        return (
            f"Meeting cancelled for employee {emp_id} on {dt_str}"
            + (f" about '{req.topic}'" if req.topic else "") + "."
        )

    def get_upcoming_meetings(self, limit: int = 20) -> List[Dict]:
        """Return next N upcoming scheduled meetings across all employees."""
        with db_cursor() as cur:
            cur.execute(
                "SELECT * FROM v_upcoming_meetings LIMIT %s",
                (limit,)
            )
            return cur.fetchall()

    def add_participant(
        self, meeting_id: int, emp_id: int, rsvp: str = "no_response"
    ) -> str:
        """Add an employee as a participant to a meeting."""
        valid_rsvp = {"accepted", "declined", "tentative", "no_response"}
        if rsvp not in valid_rsvp:
            raise ValueError(f"rsvp must be one of {valid_rsvp}")

        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO meeting_participants (meeting_id, emp_id, rsvp)
                   VALUES (%s, %s, %s)
                   ON DUPLICATE KEY UPDATE rsvp = VALUES(rsvp)""",
                (meeting_id, emp_id, rsvp)
            )
        return f"Employee {emp_id} added to meeting #{meeting_id} (RSVP: {rsvp})."

    def get_participants(self, meeting_id: int) -> List[Dict]:
        """Return all participants and their RSVP for a meeting."""
        with db_cursor() as cur:
            cur.execute(
                """SELECT mp.emp_id,
                          CONCAT(e.first_name,' ',e.last_name) AS name,
                          mp.rsvp
                   FROM meeting_participants mp
                   JOIN employees e ON mp.emp_id = e.employee_id
                   WHERE mp.meeting_id = %s
                   ORDER BY mp.rsvp, e.first_name""",
                (meeting_id,)
            )
            return cur.fetchall()

    def complete_meeting(self, meeting_id: int) -> str:
        """Mark a meeting as completed."""
        with db_cursor() as cur:
            cur.execute(
                "UPDATE meetings SET status='completed' WHERE meeting_id=%s",
                (meeting_id,)
            )
            if cur.rowcount == 0:
                raise ValueError(f"Meeting #{meeting_id} not found.")
        return f"Meeting #{meeting_id} marked as completed."


if __name__ == "__main__":
    from datetime import datetime
    mm = MeetingManager()

    print("Upcoming:", mm.get_upcoming_meetings(5))
    print("Meetings for emp 1:", mm.get_meetings(1))
    print("Participants of meeting 1:", mm.get_participants(1))
