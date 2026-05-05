import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Transaction, Category, Budget

# --- Main Views ---

def main(request):
    """الصفحة التعريفية للموقع"""
    return render(request, 'main/index.html')

# --- Authentication Views ---

def signup_view(request):
    """تسجيل مستخدم جديد وتحويله لأدمن تلقائياً"""
    if request.method == 'POST':
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists!")
            return render(request, 'main/signup.html')

        # إنشاء المستخدم (استخدام الإيميل كـ username)
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = full_name
        
        # تفعيل صلاحيات الأدمن (is_staff و is_superuser)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        login(request, user)
        messages.success(request, f"Welcome {full_name}! Your admin account is ready.")
        return redirect('dashboard')
    
    return render(request, 'main/signup.html')

def login_view(request):
    """تسجيل الدخول"""
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

def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    return redirect('login')

# --- Dashboard & Financial Views ---

@login_required
def dashboard_view(request):
    """لوحة التحكم الرئيسية لـ BudgetWise"""
    return render(request, 'main/dashboard.html')

@login_required
def transactions_view(request):
    """عرض وإضافة العمليات المالية"""
    if request.method == "POST":
        amount_str = request.POST.get('amount')
        t_type = request.POST.get('type')
        cat_id = request.POST.get('category')
        
        try:
            amount = decimal.Decimal(amount_str)
            
            # إنشاء العملية وربطها بالمستخدم الحالي
            transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type=t_type,
                category_id=cat_id,
                description=request.POST.get('description', ''),
                note=request.POST.get('note', '')
            )

            # تحديث الميزانية (Budget) في حالة المصروفات
            if t_type == 'EX':
                try:
                    budget = Budget.objects.get(user=request.user, category_id=cat_id)
                    budget.current_spending += amount
                    budget.save()

                    if budget.current_spending > budget.limit_amount:
                        messages.warning(request, f"Warning: You have exceeded your budget for {budget.category.name}!")
                except Budget.DoesNotExist:
                    pass
            
            messages.success(request, "Transaction added successfully!")
            
        except (decimal.InvalidOperation, TypeError):
            messages.error(request, "Invalid amount entered.")

        return redirect('transactions')

    # جلب العمليات الخاصة بالمستخدم فقط
    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date_time')
    categories = Category.objects.all()
    
    return render(request, 'main/transactions.html', {
        'transactions': user_transactions, 
        'categories': categories
    })

@login_required
def budgets_view(request):
    """عرض ميزانيات المستخدم"""
    user_budgets = Budget.objects.filter(user=request.user)
    return render(request, 'main/budgets.html', {'budgets': user_budgets})

@login_required
def goals_view(request):
    return render(request, 'main/goals.html')

@login_required
def reports_view(request):
    return render(request, 'main/reports.html')

# --- Profile View ---

@login_required
def profile_view(request):
    """تحديث بيانات الملف الشخصي"""
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        
        # تحديث بيانات جدول الـ User الأساسي
        user = request.user
        user.first_name = first_name
        user.email = email
        user.save()
        
        # تحديث بيانات جدول الـ Profile الإضافي
        user_profile.phone = phone
        if dob: 
            user_profile.date_of_birth = dob
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
        
    return render(request, 'main/profile.html', {'profile': user_profile})