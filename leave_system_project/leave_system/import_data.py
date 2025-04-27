import pandas as pd
from django.contrib.auth.models import User, Group
from leave_system.models import Specialty, Service, Department, EmployeeType, EmployeePosition, Employee, LeaveType, PublicHoliday, HeaderText

def import_specialties(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        Specialty.objects.get_or_create(
            name=row['name'],
            short_name=row['short_name']
        )
    print("Specialties imported successfully.")

def import_services(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        Service.objects.get_or_create(
            name=row['name']
        )
    print("Services imported successfully.")

def import_departments(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        service = Service.objects.get(name=row['service_name'])
        head = Employee.objects.get(sch_email=row['head_email']) if row['head_email'] else None
        Department.objects.get_or_create(
            name=row['name'],
            service=service,
            defaults={'head': head}
        )
    print("Departments imported successfully.")

def import_employee_types(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        EmployeeType.objects.get_or_create(
            name=row['name']
        )
    print("Employee Types imported successfully.")

def import_employee_positions(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        EmployeePosition.objects.get_or_create(
            name=row['name']
        )
    print("Employee Positions imported successfully.")

def import_employees(file_path):
    df = pd.read_excel(file_path)
    employee_group = Group.objects.get(name='Employee')
    for _, row in df.iterrows():
        user, _ = User.objects.get_or_create(
            username=row['sch_email'],
            email=row['sch_email'],
            defaults={'password': User.objects.make_random_password()}
        )
        user.groups.add(employee_group)
        specialty = Specialty.objects.get(name=row['specialty_name'])
        current_service = Service.objects.get(name=row['current_service_name'])
        department = Department.objects.get(name=row['department_name'])
        employee_type = EmployeeType.objects.get(name=row['employee_type_name'])
        position = EmployeePosition.objects.get(name=row['position_name'])
        Employee.objects.get_or_create(
            user=user,
            name_in_accusative=row['name_in_accusative'],
            surname_in_accusative=row['surname_in_accusative'],
            father_name_in_genitive=row['father_name_in_genitive'],
            specialty=specialty,
            current_service=current_service,
            department=department,
            employee_type=employee_type,
            role_description=row['role_description'],
            notification_recipients=row['notification_recipients'],
            regular_leave_days=row['regular_leave_days'],
            carryover_leave_days=row['carryover_leave_days'],
            gender=row['gender'],
            sch_email=row['sch_email'],
            personal_email=row['personal_email'],
            position=position,
            is_active=row['is_active'],
            phone=row['phone']
        )
    print("Employees imported successfully.")

def import_leave_types(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        LeaveType.objects.get_or_create(
            name=row['name'],
            short_name=row['short_name'],
            subject_text=row['subject_text'],
            decision_text=row['decision_text']
        )
    print("Leave Types imported successfully.")

def import_public_holidays(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        year = row['year'] if not pd.isna(row['year']) else None
        PublicHoliday.objects.get_or_create(
            name=row['name'],
            day=row['day'],
            month=row['month'],
            year=year,
            is_fixed=row['is_fixed']
        )
    print("Public Holidays imported successfully.")

def import_header_texts(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        HeaderText.objects.get_or_create(
            text=row['text'],
            is_active=row['is_active']
        )
    print("Header Texts imported successfully.")

def import_all_data():
    try:
        import_specialties('data/specialties.xlsx')
        import_services('data/services.xlsx')
        import_departments('data/departments.xlsx')
        import_employee_types('data/employee_types.xlsx')
        import_employee_positions('data/employee_positions.xlsx')
        import_employees('data/employees.xlsx')
        import_leave_types('data/leave_types.xlsx')
        import_public_holidays('data/public_holidays.xlsx')
        import_header_texts('data/header_texts.xlsx')
    except Exception as e:
        print(f"Error during import: {str(e)}")

if __name__ == "__main__":
    import_all_data()