#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from .forms import RegisterForm, LeaveRequestForm, LeaveIntervalForm
from .models import Employee, LeaveRequest, Department

def setup_groups():
    employee_group, _ = Group.objects.get_or_create(name='Employee')
    leave_officer_group, _ = Group.objects.get_or_create(name='LeaveOfficer')
    admin_group, _ = Group.objects.get_or_create(name='Administrator')
    department_head_group, _ = Group.objects.get_or_create(name='DepartmentHeads')

    content_type = ContentType.objects.get_for_model(LeaveRequest)
    employee_permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=['add_leaverequest', 'view_leaverequest']
    )
    leave_officer_permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=['change_leaverequest', 'delete_leaverequest']
    )
    department_head_permissions = Permission.objects.filter(
        content_type=content_type,
        codename='view_leaverequest'
    )

    employee_group.permissions.set(employee_permissions)
    leave_officer_group.permissions.set(employee_permissions | leave_officer_permissions)
    department_head_group.permissions.set(department_head_permissions)
    admin_group.permissions.set(Permission.objects.all())


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('create_leave_request')
    else:
        form = RegisterForm()
    return render(request, 'leave_system/register.html', {'form': form})

    

@login_required
def create_leave_request(request):
    employee = Employee.objects.get(user=request.user)
    if request.method == 'POST':
        leave_form = LeaveRequestForm(request.POST)
        interval_form = LeaveIntervalForm(request.POST)
        if leave_form.is_valid() and interval_form.is_valid():
            leave_request = leave_form.save(commit=False)
            leave_request.employee = employee
            leave_request.save()
            interval = interval_form.save(commit=False)
            interval.leave_request = leave_request
            interval.save()
            return redirect('view_leave_requests')
    else:
        leave_form = LeaveRequestForm()
        interval_form = LeaveIntervalForm()
    return render(request, 'leave_system/create_leave_request.html', {
        'leave_form': leave_form,
        'interval_form': interval_form,
    })



@login_required
def view_leave_requests(request):
    employee = Employee.objects.get(user=request.user)
    leave_requests = LeaveRequest.objects.filter(employee=employee)
    return render(request, 'leave_system/view_leave_requests.html', {'leave_requests': leave_requests})

def is_admin(user):
    return user.groups.filter(name='Administrator').exists()

@user_passes_test(is_admin)
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        user = User.objects.get(id=user_id)
        user.groups.clear()
        group = Group.objects.get(name=role)
        user.groups.add(group)
        return redirect('manage_users')

    users = User.objects.all()
    groups = Group.objects.all()
    return render(request, 'leave_system/manage_users.html', {'users': users, 'groups': groups})

def is_leave_officer_or_admin(user):
    return user.groups.filter(name__in=['LeaveOfficer', 'Administrator']).exists()

@user_passes_test(is_leave_officer_or_admin)
def manage_department_heads(request):
    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        new_head_id = request.POST.get('new_head_id')
        department = Department.objects.get(id=department_id)
        new_head = Employee.objects.get(id=new_head_id)
        department.head = new_head
        department.save()
        return redirect('manage_department_heads')

    departments = Department.objects.all()
    employees = Employee.objects.filter(is_active=True)
    return render(request, 'leave_system/manage_department_heads.html', {
        'departments': departments,
        'employees': employees,
    })

def is_department_head(user):
    return user.groups.filter(name='DepartmentHeads').exists()

@user_passes_test(is_department_head)
def view_subordinate_leaves(request):
    employee = Employee.objects.get(user=request.user)
    departments = Department.objects.filter(head=employee)
    subordinates = Employee.objects.filter(department__in=departments)
    leave_requests = LeaveRequest.objects.filter(employee__in=subordinates)

    return render(request, 'leave_system/view_subordinate_leaves.html', {
        'leave_requests': leave_requests,
        'departments': departments,
    })

@user_passes_test(is_leave_officer_or_admin)
def preview_decision_pdf(request, leave_request_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)
    if request.method == 'POST':
        leave_request.status = 'APPROVED'
        leave_request.processed_by = Employee.objects.get(user=request.user)
        leave_request.protocol_number = request.POST.get('protocol_number')
        leave_request.kedasy_protocol_number = request.POST.get('kedasy_protocol_number')
        leave_request.final_signatory = request.POST.get('final_signatory')
        leave_request.custom_decision_text = request.POST.get('custom_decision_text')
        leave_request.save()
        leave_request.generate_decision_pdf()
        return redirect('view_leave_requests')
    return render(request, 'leave_system/preview_decision_pdf.html', {'leave_request': leave_request})