from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from accounts.forms import LoginForm, DonorRegistrationForm, RequesterRegistrationForm, HospitalRegistrationForm
from accounts.models import User
from donors.models import DonorProfile
from blood_requests.models import RequesterProfile
from hospitals.models import HospitalOrganization
from analytics.models import ActivityLog
from notifications.models import Notification


def register(request):
    """
    Unified multi-role registration controller.
    Supports Donor, Requester, and Hospital registration with transaction safety.
    """
    active_tab = request.GET.get('role', 'donor').lower()

    donor_form = DonorRegistrationForm()
    requester_form = RequesterRegistrationForm()
    hospital_form = HospitalRegistrationForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'donor':
            donor_form = DonorRegistrationForm(request.POST)
            active_tab = 'donor'
            if donor_form.is_valid():
                with transaction.atomic():
                    user = donor_form.save(commit=False)
                    user.role = User.Role.DONOR
                    user.set_password(donor_form.cleaned_data['password'])
                    user.is_verified = True
                    user.save()

                    DonorProfile.objects.create(
                        user=user,
                        blood_group=donor_form.cleaned_data['blood_group'],
                        gender=donor_form.cleaned_data['gender'],
                        date_of_birth=donor_form.cleaned_data['date_of_birth'],
                        district=donor_form.cleaned_data['district'],
                        upazila=donor_form.cleaned_data['upazila'],
                        full_address=donor_form.cleaned_data['full_address'],
                        last_donation_date=donor_form.cleaned_data.get('last_donation_date'),
                    )

                    ActivityLog.log(action="DONOR_REGISTERED", user=user, details=f"New donor registered with blood group {donor_form.cleaned_data['blood_group'].name}")
                    Notification.send(
                        user=user,
                        title="Welcome to LifeDrop BD!",
                        message="Your donor profile has been created. Keep your availability status updated.",
                        notification_type=Notification.Type.SYSTEM,
                        link="/donors/dashboard/"
                    )

                messages.success(request, "Registration successful! You may now sign in to your donor account.")
                return redirect('accounts:login')

        elif form_type == 'requester':
            requester_form = RequesterRegistrationForm(request.POST)
            active_tab = 'requester'
            if requester_form.is_valid():
                with transaction.atomic():
                    user = requester_form.save(commit=False)
                    user.role = User.Role.REQUESTER
                    user.set_password(requester_form.cleaned_data['password'])
                    user.is_verified = True
                    user.save()

                    RequesterProfile.objects.create(
                        user=user,
                        district=requester_form.cleaned_data.get('district'),
                        upazila=requester_form.cleaned_data.get('upazila'),
                        address=requester_form.cleaned_data.get('address', ''),
                    )

                    ActivityLog.log(action="REQUESTER_REGISTERED", user=user, details="New blood requester registered.")

                messages.success(request, "Account created! You can now request emergency blood.")
                return redirect('accounts:login')

        elif form_type == 'hospital':
            hospital_form = HospitalRegistrationForm(request.POST)
            active_tab = 'hospital'
            if hospital_form.is_valid():
                with transaction.atomic():
                    user = User.objects.create(
                        username=hospital_form.cleaned_data['username'],
                        email=hospital_form.cleaned_data['email'],
                        first_name=hospital_form.cleaned_data['org_name'][:30],
                        phone_number=hospital_form.cleaned_data['phone'],
                        role=User.Role.HOSPITAL,
                        is_verified=False,  # Requires Admin Approval
                    )
                    user.set_password(hospital_form.cleaned_data['password'])
                    user.save()

                    HospitalOrganization.objects.create(
                        user=user,
                        org_name=hospital_form.cleaned_data['org_name'],
                        org_type=hospital_form.cleaned_data['org_type'],
                        license_number=hospital_form.cleaned_data['license_number'],
                        district=hospital_form.cleaned_data['district'],
                        upazila=hospital_form.cleaned_data.get('upazila'),
                        address=hospital_form.cleaned_data['address'],
                        contact_person=hospital_form.cleaned_data['contact_person'],
                        phone=hospital_form.cleaned_data['phone'],
                        email=hospital_form.cleaned_data['email'],
                        is_verified=False,
                    )

                    ActivityLog.log(action="HOSPITAL_REGISTERED", user=user, details=f"Hospital {hospital_form.cleaned_data['org_name']} submitted verification request.")

                messages.info(request, "Hospital registered! An administrator will review your medical credentials before account activation.")
                return redirect('accounts:login')

    context = {
        'active_tab': active_tab,
        'donor_form': donor_form,
        'requester_form': requester_form,
        'hospital_form': hospital_form,
    }
    return render(request, 'accounts/register.html', context)


def user_login(request):
    """Secure login handling role-specific redirects and validation."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ActivityLog.log(action="USER_LOGIN", user=user, details="User successfully authenticated.")
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please verify credentials.")

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """Terminates session safely."""
    if request.user.is_authenticated:
        ActivityLog.log(action="USER_LOGOUT", user=request.user, details="User signed out.")
        logout(request)
        messages.info(request, "You have been signed out successfully.")
    return redirect('core:home')


@login_required
def dashboard_redirect(request):
    """Central role-based access controller redirecting to specific dashboards."""
    user = request.user
    if user.is_admin_role:
        return redirect('analytics:admin_dashboard')
    elif user.is_donor_role:
        return redirect('donors:dashboard')
    elif user.is_requester_role:
        return redirect('blood_requests:my_requests')
    elif user.is_hospital_role:
        return redirect('hospitals:dashboard')
    return redirect('core:home')


@login_required
def profile_view(request):
    """View and update profile information."""
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if first_name and email:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            if user.is_donor_role and hasattr(user, 'donor_profile'):
                dp = user.donor_profile
                dp.bio = request.POST.get('bio', '').strip()
                dp.full_address = request.POST.get('full_address', '').strip()
                dp.emergency_contact = request.POST.get('emergency_contact', '').strip()
                dp.save()

            ActivityLog.log(action="PROFILE_UPDATED", user=user, details="User updated profile details.")
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile_view')

    return render(request, 'accounts/profile.html', {'user': user})
