from django.shortcuts import render

# Create your views here.

def main(request):
    return render(request,'main/index.html')

def login_view(request):
    return render(request,'main/login.html')

def signup_view(request):
    return render(request,'main/signup.html')

def dashboard_view(request):
    return render(request,'main/dashboard.html')

def transactions_view(request):
    return render(request,'main/transactions.html')

def budgets_view(request):
    return render(request,'main/budgets.html')

def goals_view(request):
    return render(request,'main/goals.html')

def reports_view(request):
    return render(request,'main/reports.html')

def profile_view(request):
    return render(request,'main/profile.html')