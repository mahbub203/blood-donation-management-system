from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from core.models import District, Upazila, BloodGroup
from donors.models import DonorProfile
from blood_requests.models import RequesterProfile
from hospitals.models import HospitalOrganization

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Phone'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class DonorRegistrationForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    # Donor Profile fields
    blood_group = forms.ModelChoiceField(queryset=BloodGroup.objects.all(), empty_label="-- Select Blood Group --", widget=forms.Select(attrs={'class': 'form-select'}))
    gender = forms.ChoiceField(choices=DonorProfile.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    district = forms.ModelChoiceField(queryset=District.objects.all(), empty_label="-- Select District --", widget=forms.Select(attrs={'class': 'form-select', 'data-upazila-target': 'id_upazila'}))
    upazila = forms.ModelChoiceField(queryset=Upazila.objects.all(), required=False, empty_label="-- Select Upazila --", widget=forms.Select(attrs={'class': 'form-select'}))
    full_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street, Area, Village'}))
    last_donation_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), help_text="Leave blank if you have never donated blood")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class RequesterRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    district = forms.ModelChoiceField(queryset=District.objects.all(), empty_label="-- Select District --", widget=forms.Select(attrs={'class': 'form-select', 'data-upazila-target': 'req_id_upazila'}))
    upazila = forms.ModelChoiceField(queryset=Upazila.objects.all(), required=False, empty_label="-- Select Upazila --", widget=forms.Select(attrs={'class': 'form-select', 'id': 'req_id_upazila'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class HospitalRegistrationForm(forms.ModelForm):
    org_name = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Apollo Hospital Blood Bank'}))
    org_type = forms.ChoiceField(choices=HospitalOrganization.OrgType.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    license_number = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DGHS License or Govt Registration No.'}))
    contact_person = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dr. Name or Lab In-charge'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hospital@domain.com'}))
    username = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    district = forms.ModelChoiceField(queryset=District.objects.all(), empty_label="-- Select District --", widget=forms.Select(attrs={'class': 'form-select', 'data-upazila-target': 'hosp_id_upazila'}))
    upazila = forms.ModelChoiceField(queryset=Upazila.objects.all(), required=False, empty_label="-- Select Upazila --", widget=forms.Select(attrs={'class': 'form-select', 'id': 'hosp_id_upazila'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Hospital address, ward, or blood transfusion unit'}))

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data
