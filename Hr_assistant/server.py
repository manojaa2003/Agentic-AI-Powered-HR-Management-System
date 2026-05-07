from mcp.server.fastmcp import FastMCP
from hrms.employee_manager import EmployeeManager
from hrms.leave_manager import LeaveManager
from hrms.meeting_manager import MeetingManager
from hrms.ticket_manager import TicketManager
from hrms.schemas import EmployeeCreate

mcp = FastMCP("Hr_assistant")
employee_manager = EmployeeManager()
leave_manager = LeaveManager()
meeting_manager = MeetingManager()
ticket_manager = TicketManager()

# tools,resources(knowledge),prompts

@mcp.tool()
def add_employee(emp_name,manager_id,email):
    '''
    Add a new employee to HRMS system
    :param emp_name:
    :param manager_id:
    :param email:
    :return:
    '''
    emp = EmployeeCreate(
        emp_id= str(employee_manager.get_next_emp_id()),
        name=emp_name,
        manager_id=manager_id,
        email= email,
    )
    employee_manager.add_employee(emp)
    return f"Employee:{emp_name} added successfully"

@mcp.tool()
def get_employee_details(name):
    '''
    get employee details by name
    :param name:
    :return:employee_id and manager_id
    '''
    matches = employee_manager.search_employee_by_name(name)

    if len(matches) == 0:
        raise ValueError(f"No employee found Matching:{name}")

    emp_id = matches[0]["employee_id"]

    emp = employee_manager.get_employee_details(emp_id)

    return {
        "employee_id": emp["employee_id"],
        "manager_id": emp["manager_id"],
        "name": f"{emp['first_name']} {emp['last_name']}"
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")

