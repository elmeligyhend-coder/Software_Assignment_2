from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login , authenticate , logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Sum

from .models import Profile, Transaction
from .transaction_factory import TransactionFactory


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
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
    return render(request,'main/dashboard.html', {'recent_transactions': recent_transactions})

@login_required(login_url='login')
def transactions_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    income_agg = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))
    expense_agg = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))
    total_income = income_agg.get('total') or Decimal('0')
    total_expenses = expense_agg.get('total') or Decimal('0')
    errors = []
    form_data = {
        'transaction_type': '',
        'amount': '',
        'category': '',
        'name': '',
        'description': '',
        'note': '',
        'date': '',
    }
    show_add_form = False

    if request.method == 'POST':
        show_add_form = True
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'transaction_type': request.POST.get('transaction_type', '').strip(),
            'amount': request.POST.get('amount', '').strip(),
            'category': request.POST.get('category', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'note': request.POST.get('note', '').strip(),
            'date': request.POST.get('date', '').strip(),
        }

        if not form_data['name']:
            errors.append('Please enter a transaction name.')

        if form_data['transaction_type'] not in ['income', 'expense']:
            errors.append('Please select a valid transaction type.')

        if not form_data['amount']:
            errors.append('Amount is required.')
        else:
            try:
                amount_value = Decimal(form_data['amount'])
                if amount_value <= 0:
                    errors.append('Amount must be greater than zero.')
            except InvalidOperation:
                errors.append('Enter a valid numeric amount.')

        if not form_data['category']:
            errors.append('Please select a category.')


        if not form_data['date']:
            errors.append('Date and time are required.')
        else:
            transaction_date = parse_datetime(form_data['date'])
            if transaction_date is None:
                errors.append('Enter a valid date and time.')

        if not errors:
            transaction = TransactionFactory.create_transaction(
                form_data['transaction_type'],
                request.user,
                amount_value,
                form_data['category'],
                form_data.get('name', ''),
                form_data['description'],
                form_data['note'],
                transaction_date if form_data['date'] else timezone.now(),
            )
            transaction.save()
            messages.success(request, 'Transaction added successfully.')
            return redirect('transactions')

    return render(
        request,
        'main/transactions.html',
        {
            'transactions': transactions,
            'errors': errors,
            'form_data': form_data,
            'show_add_form': show_add_form,
            'total_income': total_income,
            'total_expenses': total_expenses,
        },
    )


@login_required(login_url='login')
def delete_transaction(request, id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for delete.')
        return redirect('transactions')

    try:
        txn = Transaction.objects.get(id=id, user=request.user)
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('transactions')

    txn.delete()
    messages.success(request, 'Transaction deleted.')
    return redirect('transactions')


@login_required(login_url='login')
def update_transaction(request, id):
    try:
        txn = Transaction.objects.get(id=id, user=request.user)
    except Transaction.DoesNotExist:
        messages.error(request, 'Transaction not found.')
        return redirect('transactions')

    if request.method != 'POST':
        messages.error(request, 'Invalid request method for update.')
        return redirect('transactions')

    name = request.POST.get('name', '').strip()
    transaction_type = request.POST.get('transaction_type', '').strip()
    amount = request.POST.get('amount', '').strip()
    category = request.POST.get('category', '').strip()
    description = request.POST.get('description', '').strip()
    note = request.POST.get('note', '').strip()
    date_str = request.POST.get('date', '').strip()

    errors = []
    if transaction_type not in ['income', 'expense']:
        errors.append('Please select a valid transaction type.')

    try:
        amount_value = Decimal(amount)
        if amount_value <= 0:
            errors.append('Amount must be greater than zero.')
    except Exception:
        errors.append('Enter a valid numeric amount.')

    if not name:
        errors.append('Please enter a name.')
    if not category:
        errors.append('Please select a category.')

    transaction_date = None
    if date_str:
        transaction_date = parse_datetime(date_str)
        if transaction_date is None:
            errors.append('Enter a valid date and time.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('transactions')

    txn.transaction_type = transaction_type
    txn.amount = amount_value
    txn.category = category
    txn.name = name
    txn.description = description
    txn.note = note
    if transaction_date:
        txn.date = transaction_date
    txn.save()
    messages.success(request, 'Transaction updated.')
    return redirect('transactions')

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
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
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