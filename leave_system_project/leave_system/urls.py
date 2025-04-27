from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('create/', views.create_leave_request, name='create_leave_request'),
    path('view/', views.view_leave_requests, name='view_leave_requests'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-department-heads/', views.manage_department_heads, name='manage_department_heads'),
    path('view-subordinate-leaves/', views.view_subordinate_leaves, name='view_subordinate_leaves'),
    path('preview-decision/<int:leave_request_id>/', views.preview_decision_pdf, name='preview_decision_pdf'),
]
