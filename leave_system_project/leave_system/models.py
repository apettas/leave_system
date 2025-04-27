from django.db import models
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from weasyprint import HTML
import os
from django.conf import settings

class Specialty(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=255)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    head = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')

    def save(self, *args, **kwargs):
        old_department = Department.objects.get(id=self.id) if self.id else None
        old_head = old_department.head if old_department else None

        super().save(*args, **kwargs)

        # Ενημέρωση ομάδας DepartmentHeads
        department_head_group = Group.objects.get(name='DepartmentHeads')

        # Αν υπάρχει παλιός προϊστάμενος και δεν είναι πια προϊστάμενος σε κανένα τμήμα, αφαιρούμε τον ρόλο
        if old_head and old_head != self.head:
            other_departments = Department.objects.filter(head=old_head).exclude(id=self.id)
            if not other_departments.exists():
                old_head.user.groups.remove(department_head_group)

        # Αν υπάρχει νέος προϊστάμενος, προσθέτουμε τον ρόλο
        if self.head and self.head.user:
            self.head.user.groups.add(department_head_group)

    def __str__(self):
        return self.name

class EmployeeType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class EmployeePosition(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name_in_accusative = models.CharField(max_length=255)
    surname_in_accusative = models.CharField(max_length=255)
    father_name_in_genitive = models.CharField(max_length=255)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    current_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.SET_NULL, null=True)
    role_description = models.TextField(null=True, blank=True)
    notification_recipients = models.TextField(null=True, blank=True)
    regular_leave_days = models.IntegerField(default=24)
    carryover_leave_days = models.IntegerField(default=0)
    gender = models.CharField(max_length=50)
    sch_email = models.EmailField(unique=True, null=True, blank=True)
    personal_email = models.EmailField(unique=True, null=True, blank=True)
    position = models.ForeignKey(EmployeePosition, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name_in_accusative', 'surname_in_accusative', 'father_name_in_genitive'],
                name='unique_employee'
            )
        ]

    def full_name(self):
        return f"{self.name_in_accusative} {self.surname_in_accusative}"

    def __str__(self):
        return self.full_name()

class LeaveType(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50)
    subject_text = models.CharField(max_length=255)
    decision_text = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PublicHoliday(models.Model):
    name = models.CharField(max_length=100)
    day = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField(null=True, blank=True)
    is_fixed = models.BooleanField(default=False)

    def __str__(self):
        if self.is_fixed:
            return f"{self.name} ({self.day}/{self.month})"
        return f"{self.name} ({self.day}/{self.month}/{self.year})"

    def get_date_for_year(self, target_year):
        if self.is_fixed:
            return datetime(target_year, self.month, self.day).date()
        if self.year == target_year:
            return datetime(self.year, self.month, self.day).date()
        return None

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Υπό Επεξεργασία'),
        ('APPROVED', 'Εγκρίθηκε'),
        ('REJECTED', 'Απορρίφθηκε'),
        ('ISSUED', 'Εκδόθηκε'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(null=True, blank=True)
    protocol_number = models.CharField(max_length=50, null=True, blank=True)
    kedasy_protocol_number = models.CharField(max_length=50, null=True, blank=True)
    final_signatory = models.CharField(max_length=255, null=True, blank=True)
    custom_decision_text = models.TextField(null=True, blank=True)
    decision_pdf = models.FileField(upload_to='decisions/', null=True, blank=True)
    header_text = models.TextField(null=True, blank=True)
    processed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_leaves')
    processed_by_name = models.CharField(max_length=255, null=True, blank=True)
    processed_by_phone = models.CharField(max_length=20, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            active_header = HeaderText.objects.filter(is_active=True).first()
            self.header_text = active_header.text if active_header else "ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ ΥΠΟΥΡΓΕΙΟ ΠΑΙΔΕΙΑΣ"
        super().save(*args, **kwargs)

    def calculate_total_working_days(self):
        total_days = 0
        for interval in self.intervals.all():
            total_days += interval.calculate_working_days()
        return total_days

    def generate_decision_pdf(self):
        if self.processed_by:
            self.processed_by_name = self.processed_by.full_name()
            self.processed_by_phone = self.processed_by.phone
        context = {
            'leave_request': self,
            'employee': self.employee,
            'leave_type': self.leave_type,
            'intervals': self.intervals.all(),
            'service': self.employee.current_service,
            'protocol_number': self.protocol_number,
            'kedasy_protocol_number': self.kedasy_protocol_number,
            'final_signatory': self.final_signatory,
            'custom_text': self.custom_decision_text or '',
            'date': datetime.now().strftime('%d/%m/%Y'),
            'static_url': 'file://' + settings.STATICFILES_DIRS[0] + '/'
        }
        html_content = render_to_string('leave_system/decision_template.html', context)
        pdf_file = f"decision_{(self.employee.sch_email or 'no_email')}_{self.created_at.strftime('%Y%m%d')}.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'decisions', pdf_file)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        HTML(string=html_content).write_pdf(pdf_path)
        self.decision_pdf.name = os.path.join('decisions', pdf_file)
        self.status = 'ISSUED'
        self.save()

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - {self.created_at}"

class LeaveInterval(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='intervals')
    start_date = models.DateField()
    end_date = models.DateField()

    def calculate_working_days(self):
        current_date = self.start_date
        working_days = 0
        year = self.start_date.year
        public_holidays = PublicHoliday.objects.all()
        holiday_dates = set()
        for holiday in public_holidays:
            holiday_date = holiday.get_date_for_year(year)
            if holiday_date and self.start_date <= holiday_date <= self.end_date:
                holiday_dates.add(holiday_date)

        while current_date <= self.end_date:
            if current_date.weekday() not in [5, 6] and current_date not in holiday_dates:
                working_days += 1
            current_date += timedelta(days=1)
        return working_days

    def __str__(self):
        return f"{self.start_date} - {self.end_date}"

class HeaderText(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            HeaderText.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Header ({self.created_at})"
    