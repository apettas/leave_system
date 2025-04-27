from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Υπηρεσιακό Email στο @sch.gr")
    name_in_accusative = forms.CharField(max_length=255, label="Όνομα (αιτιατική)")
    surname_in_accusative = forms.CharField(max_length=255, label="Επώνυμο (αιτιατική)")
    father_name_in_genitive = forms.CharField(max_length=255, label="Πατρώνυμο (γενική)")
    gender = forms.ChoiceField(choices=[('Α', 'Άνδρας'), ('Γ', 'Γυναίκα')], label="Φύλο")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'name_in_accusative', 'surname_in_accusative', 'father_name_in_genitive', 'gender']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@sch.gr'):
            raise forms.ValidationError("Το email πρέπει να είναι της μορφής @sch.gr")
        from .models import Employee  # Εισαγωγή εδώ για αποφυγή κυκλικού import
        if Employee.objects.filter(sch_email=email).exists():
            raise forms.ValidationError("Αυτό το email υπάρχει ήδη.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            from .models import Employee  # Εισαγωγή εδώ για αποφυγή κυκλικού import
            from django.contrib.auth.models import Group
            employee = Employee.objects.create(
                user=user,
                name_in_accusative=self.cleaned_data['name_in_accusative'],
                surname_in_accusative=self.cleaned_data['surname_in_accusative'],
                father_name_in_genitive=self.cleaned_data['father_name_in_genitive'],
                gender=self.cleaned_data['gender'],
                sch_email=self.cleaned_data['email'],
                regular_leave_days=24,
                carryover_leave_days=0,
                is_active=True,
            )
            employee_group = Group.objects.get(name='Employee')
            user.groups.add(employee_group)
        return user

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = None  # Θα το αντικαταστήσουμε μετά
        fields = ['leave_type']
        widgets = {
            'leave_type': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        from .models import LeaveRequest  # Εισαγωγή εδώ για αποφυγή κυκλικού import
        self.Meta.model = LeaveRequest
        super().__init__(*args, **kwargs)

class LeaveIntervalForm(forms.ModelForm):
    class Meta:
        model = None  # Θα το αντικαταστήσουμε μετά
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        from .models import LeaveInterval  # Εισαγωγή εδώ για αποφυγή κυκλικού import
        self.Meta.model = LeaveInterval
        super().__init__(*args, **kwargs)