from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login , authenticate , logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile  

def main(request):
    return render(request,'main/index.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists!")
            return render(request, 'main/signup.html')

        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = full_name
        user.save()

        login(request, user)

        return redirect('dashboard')
    
    return render(request, 'main/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard') 
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'main/login.html')

@login_required(login_url='login')
def dashboard_view(request):
    return render(request,'main/dashboard.html')

@login_required(login_url='login')
def transactions_view(request):
    return render(request,'main/transactions.html')

@login_required(login_url='login')
def budgets_view(request):
    return render(request,'main/budgets.html')

@login_required(login_url='login')
def goals_view(request):
    return render(request,'main/goals.html')

@login_required(login_url='login')
def reports_view(request):
    return render(request,'main/reports.html')

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        user = request.user
        user.first_name = first_name
        user.email = email
        user.save()
        user_profile.phone = phone
        if dob: 
            user_profile.date_of_birth = dob
        user_profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'main/profile.html')

def logout_view(request):
    logout(request)
    return redirect('login')