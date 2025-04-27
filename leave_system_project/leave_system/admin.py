#from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Specialty, Service, Department, EmployeeType, EmployeePosition, Employee, LeaveType, PublicHoliday, LeaveRequest, LeaveInterval, HeaderText

class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name')
    search_fields = ('name',)

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'head')
    list_filter = ('service',)
    search_fields = ('name',)

class EmployeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name_in_accusative', 'surname_in_accusative', 'sch_email', 'is_active')
    list_filter = ('is_active', 'department', 'current_service')
    search_fields = ('name_in_accusative', 'surname_in_accusative', 'sch_email')

class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'subject_text', 'decision_text')
    search_fields = ('name', 'short_name')

class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'day', 'month', 'year', 'is_fixed')
    list_filter = ('is_fixed', 'year')
    search_fields = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'day', 'month', 'year', 'is_fixed')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj or not obj.is_fixed:
            form.base_fields['year'].required = True
        else:
            form.base_fields['year'].required = False
        return form

class LeaveIntervalInline(admin.TabularInline):
    model = LeaveInterval
    extra = 1

class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'created_at', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__name_in_accusative', 'employee__surname_in_accusative')
    inlines = [LeaveIntervalInline]

class HeaderTextAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('text',)

admin.site.register(Specialty, SpecialtyAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(EmployeeType, EmployeeTypeAdmin)
admin.site.register(EmployeePosition, EmployeePositionAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(LeaveType, LeaveTypeAdmin)
admin.site.register(PublicHoliday, PublicHolidayAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(HeaderText, HeaderTextAdmin)