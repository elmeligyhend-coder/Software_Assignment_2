from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login , authenticate , logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile , Transaction , Budget , Goal
from django.db.models import Sum , F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

def main(request):
    return render(request,'main/index.html')

def signup_view(request):
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

        return redirect('login')
    
    return render(request, 'main/signup.html')

def login_view(request):
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

@login_required
def dashboard_view(request):
    today = timezone.now()
    transactions = Transaction.objects.filter(user=request.user)
    total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    current_balance = total_income - total_expenses
    
    user_goals = Goal.objects.filter(user=request.user)
    total_savings = user_goals.aggregate(Sum('current_amount'))['current_amount__sum'] or 0
    
    recent_transactions = transactions.order_by('-date')[:5]

    user_budgets = Budget.objects.filter(user=request.user)
    budget_summary = []
    for budget in user_budgets:
        spent = transactions.filter(category=budget.category, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        limit = budget.amount_limit  
        percent = (spent / limit * 100) if limit > 0 else 0
        
        budget_summary.append({
            'category': budget.category,
            'limit': limit,
            'spent': spent,
            'percent': min(percent, 100),
        })

    context = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'current_balance': current_balance,
        'total_savings': total_savings,
        'recent_transactions': recent_transactions,
        'budget_summary': budget_summary,
        'user_goals': user_goals,
        'today': today,
    }
    return render(request, 'main/dashboard.html', context)

@login_required
def transactions_view(request):
    filter_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    now = timezone.now()
    if filter_type == 'week':
        start_of_week = now - timedelta(days=now.weekday()) # بداية الأسبوع من يوم الاثنين
        user_transactions = user_transactions.filter(date__gte=start_of_week)
    elif filter_type == 'month':
        user_transactions = user_transactions.filter(date__month=now.month, date__year=now.year)

    elif search_query:
        user_transactions = user_transactions.filter(description__icontains=search_query)
    elif filter_type == 'income':
        user_transactions = user_transactions.filter(type='income')
    elif filter_type == 'expense':
        user_transactions = user_transactions.filter(type='expense')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        description = request.POST.get('description')
        trans_type = 'income' if category == 'Income' else 'expense'
        Transaction.objects.create(
            user=request.user,
            amount=amount,
            category=category,
            description=description,
            type=trans_type
        )
        if trans_type == 'expense':
            total_spent = Transaction.objects.filter(
                user=request.user, 
                category=category,
                type='expense'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            budget = Budget.objects.filter(user=request.user, category=category).first()

            if budget and total_spent > budget.amount_limit:
                messages.warning(request, f"Warning: Budget exceeded for {category}! Spent: {total_spent}, Limit: {budget.amount_limit}")
            else:
                messages.success(request, "Transaction added successfully!")
        else:
            messages.success(request, "Income added successfully!")
        return redirect('transactions')
    all_trans = Transaction.objects.filter(user=request.user)
    total_income = all_trans.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = all_trans.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'transactions': user_transactions, 
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_filter': filter_type, 
    }
    return render(request, 'main/transactions.html', context)
def delete_transaction(request, pk):
    transaction = Transaction.objects.get(id=pk, user=request.user)
    transaction.delete()
    return redirect('transactions')

@login_required
def budgets_view(request):
    now = timezone.now()
    user_budgets = Budget.objects.filter(
        user=request.user, 
        period__month=now.month, 
        period__year=now.year
    )

    if request.method == 'POST':
        category = request.POST.get('category')
        amount_limit = request.POST.get('amount_limit')
        current_period = now.replace(day=1)
        
        Budget.objects.update_or_create(
            user=request.user, 
            category=category,
            period=current_period,
            defaults={'amount_limit': amount_limit}
        )
        messages.success(request, f"Budget for {category} updated for this month!")
        return redirect('budgets')

    budget_data = []
    for budget in user_budgets:
        actual_spent = Transaction.objects.filter(
            user=request.user, 
            category=budget.category, 
            type='expense',
            date__month=budget.period.month,
            date__year=budget.period.year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        progress = (actual_spent / budget.amount_limit * 100) if budget.amount_limit > 0 else 0
        
        budget_data.append({
            'budget': budget,
            'actual_spent': actual_spent,
            'remaining': budget.amount_limit - actual_spent,
            'over_by': actual_spent - budget.amount_limit, 
            'progress': min(progress, 100),
            'is_exceeded': actual_spent > budget.amount_limit
        })

    context = {
        'budget_data': budget_data, 
        'total_budget_limit': sum(item['budget'].amount_limit for item in budget_data),
        'total_actual_spent': sum(item['actual_spent'] for item in budget_data),
        'total_remaining': sum(item['remaining'] for item in budget_data if not item['is_exceeded']),
        'over_budget_count': sum(1 for item in budget_data if item['is_exceeded']),
        'current_month': now,
    }
    return render(request, 'main/budgets.html', context) 

@login_required
def goals_view(request):
    goals_queryset = Goal.objects.filter(user=request.user)
    today = timezone.now().date()
    if request.method == 'POST':
        if 'add_funds' in request.POST:
            goal_id = request.POST.get('goal_id')
            amount = request.POST.get('amount')
            if amount:
                goal = Goal.objects.get(id=goal_id, user=request.user)
                goal.current_amount += Decimal(amount)
                goal.save()
                messages.success(request, f"Successfully added ${amount} to {goal.title}!")
            return redirect('goals')
        elif 'edit_goal' in request.POST:
            goal_id = request.POST.get('goal_id')
            goal = Goal.objects.filter(id=goal_id, user=request.user).first()
            if goal:
                goal.title = request.POST.get('title')
                goal.target_amount = request.POST.get('target_amount')
                goal.save()
                messages.success(request, "Goal updated successfully!")
            return redirect('goals')
        
        elif 'delete_goal' in request.POST:
            goal_id = request.POST.get('goal_id')
            goal = Goal.objects.filter(id=goal_id, user=request.user).first()
            if goal:
                goal.delete()
                messages.success(request, "Goal deleted successfully!")
            return redirect('goals')

        elif 'add_goal' in request.POST:
            title = request.POST.get('title')
            target = request.POST.get('target_amount')
            deadline = request.POST.get('deadline')
            Goal.objects.create(
                user=request.user,
                title=title,
                target_amount=target,
                deadline=deadline
            )
            messages.success(request, "New financial goal created successfully!")
            return redirect('goals')

    total_saved = goals_queryset.aggregate(Sum('current_amount'))['current_amount__sum'] or 0
    total_target = goals_queryset.aggregate(Sum('target_amount'))['target_amount__sum'] or 0
    completed_goals = goals_queryset.filter(current_amount__gte=F('target_amount')).count()
    active_goals = goals_queryset.filter(current_amount__lt=F('target_amount')).count()
    remaining_to_save = total_target - total_saved
    completed_goals = goals_queryset.filter(current_amount__gte=F('target_amount')).count()
    active_goals = goals_queryset.filter(
        current_amount__lt=F('target_amount'),
        deadline__gte= today
    ).count()

    delayed_goals = goals_queryset.filter(
        current_amount__lt=F('target_amount'),
        deadline__lt= today
    ).count()
    goals_data = []
    for goal in goals_queryset:
        goals_data.append({
            'id': goal.id,
            'title': goal.title,
            'current_amount': goal.current_amount,
            'target_amount': goal.target_amount,
            'deadline': goal.deadline,
            'progress': goal.progress_percentage, 
            'is_completed': goal.current_amount >= goal.target_amount
        })

    context = {
        'goals': goals_data,
        'total_saved': total_saved,
        'active_goals': active_goals,
        'delayed_goals': delayed_goals,
        'completed_goals': completed_goals,
        'remaining_to_save': remaining_to_save,
        'today': today
    }
    
    return render(request, 'main/goals.html', context)

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