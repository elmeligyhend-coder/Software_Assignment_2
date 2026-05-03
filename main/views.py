from django.shortcuts import render, redirect
from .models import Transaction, Category, Budget
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import decimal


def main(request):
    return render(request, 'main/index.html')

def login_view(request):
    return render(request, 'main/login.html')

def signup_view(request):
    return render(request, 'main/signup.html')

@login_required
def dashboard_view(request):
    return render(request, 'main/dashboard.html')

@login_required
def transactions_view(request):
    if request.method == "POST":

        amount_str = request.POST.get('amount')
        t_type = request.POST.get('type')
        cat_id = request.POST.get('category')
        
        amount = decimal.Decimal(amount_str)


        transaction = Transaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type=t_type,
            category_id=cat_id,
            description=request.POST.get('description', ''),
            note=request.POST.get('note', '')
        )

        if t_type == 'EX':
            try:
                budget = Budget.objects.get(user=request.user, category_id=cat_id)
                budget.current_spending += amount
                budget.save()

                if budget.current_spending > budget.limit_amount:
                    messages.warning(request, f"Warning: You have exceeded your budget for {budget.category.name}!")
            except Budget.DoesNotExist:
                pass

        return redirect('transactions')

    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date_time')
    categories = Category.objects.all()
    
    return render(request, 'main/transactions.html', {
        'transactions': user_transactions, 
        'categories': categories
    })

@login_required
def budgets_view(request):
    user_budgets = Budget.objects.filter(user=request.user)
    return render(request, 'main/budgets.html', {'budgets': user_budgets})

@login_required
def goals_view(request):
    return render(request, 'main/goals.html')

@login_required
def reports_view(request):
    return render(request, 'main/reports.html')

@login_required
def profile_view(request):
    return render(request, 'main/profile.html')