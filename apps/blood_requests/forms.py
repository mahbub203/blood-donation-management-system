from django import forms
from blood_requests.models import BloodRequest
from core.models import District, Upazila, BloodGroup


class BloodRequestForm(forms.ModelForm):
    blood_group = forms.ModelChoiceField(
        queryset=BloodGroup.objects.all(),
        empty_label="-- Select Blood Group --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        empty_label="-- Select District --",
        widget=forms.Select(attrs={'class': 'form-select', 'data-upazila-target': 'req_form_upazila'})
    )
    upazila = forms.ModelChoiceField(
        queryset=Upazila.objects.all(),
        required=False,
        empty_label="-- Select Upazila --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'req_form_upazila'})
    )
    required_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    required_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    class Meta:
        model = BloodRequest
        fields = [
            'patient_name',
            'blood_group',
            'units_needed',
            'hospital_name',
            'hospital_address',
            'district',
            'upazila',
            'required_date',
            'required_time',
            'emergency_level',
            'contact_number',
            'description',
        ]
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient Full Name & Age'}),
            'units_needed': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'hospital_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dhaka Medical College Hospital'}),
            'hospital_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ward, Bed, Cabin or Building'}),
            'emergency_level': forms.Select(attrs={'class': 'form-select'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for transfusion, patient condition, hemoglobin count...'}),
        }
