from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Transaction, Budget, Goal
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.template.loader import render_to_string
from django.http import HttpResponse
import datetime, json
from decimal import Decimal
import re
"""Request handlers (views) for the main budgeting application.

Each view is implemented as a function-based Django view. Views return
rendered templates or perform redirects and use Django's messaging
framework to report validation or operation results to the user.
"""


def main(request):
    """Render the public landing page.

    Args:
        request: Django HttpRequest object.

    Returns:
        HttpResponse rendering the index template.
    """
    return render(request, 'main/index.html')


def signup_view(request):
    """Handle new user signups.

    Validates form fields, creates a new `User` instance and logs the
    user in on successful registration. Uses Django messages for errors.
    """
    
    if request.user.is_authenticated:
        return redirect('dashboard')

    

    if request.method == 'POST':
        full_name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms_of_service = request.POST.get('terms_of_service', '')

        if not full_name:
            messages.error(request, "Full name cannot be blank!")

        elif not email:
            messages.error(request, "Email cannot be blank!")
        
        elif len(password) < 8 :
            messages.error(request, "Password cannot be less than 8 chars")
        
        elif password != confirm_password :
            messages.error(request, "Passwords does not match")

        elif not terms_of_service :
            messages.error(request, "You've to accept terms of service and privacy policy.")

        else:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                messages.error(request, "Enter a valid email address (e.g., name@example.com)!")

        if messages.get_messages(request):
            return render(request, 'main/signup.html')

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
    """Authenticate a user and start a session.

    Accepts POST with `email` and `password`. On success redirects to
    the dashboard; otherwise adds an error message and re-renders the
    login form.
    """
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
    """Render the authenticated user's dashboard.

    The dashboard aggregates recent transactions, budgets and goals to
    present an overview of the user's financial state.
    """
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


@login_required(login_url='login')
def transactions_view(request):
    """List, create and update user transactions.

    GET: returns a filtered list of transactions. Supports `type`
    and `search` query params.

    POST: creates a new transaction or updates an existing one when
    `edit_id` is provided. Validation errors are reported via messages
    and redirect back to the transactions page.
    """
    filter_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    now = timezone.now()

    if search_query:
        q = Q(description__icontains=search_query) | Q(category__icontains=search_query) | Q(name__icontains=search_query)
        user_transactions = user_transactions.filter(q)

    if filter_type == 'week':
        start_of_week = now - datetime.timedelta(days=now.weekday())
        user_transactions = user_transactions.filter(date__gte=start_of_week)
    elif filter_type == 'month':
        user_transactions = user_transactions.filter(date__month=now.month, date__year=now.year)
    elif filter_type == 'income':
        user_transactions = user_transactions.filter(type='income')
    elif filter_type == 'expense':
        user_transactions = user_transactions.filter(type='expense')

    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        name = request.POST.get('name', '').strip()
        transaction_type = request.POST.get('transaction_type') or 'expense'
        amount = request.POST.get('amount', '').strip()
        category = request.POST.get('category', '').strip()
        description = request.POST.get('description', '')
        note = request.POST.get('note', '')
        date_str = request.POST.get('date', '').strip()

        errors = False

        if not name:
            messages.error(request, "Name is required.")
            errors = True

        if not amount:
            messages.error(request, "Amount is required.")
            errors = True
        else:
            try:
                amount = float(amount)
            except ValueError:
                messages.error(request, "Amount must be a valid number.")
                errors = True

        if transaction_type not in ['income', 'expense']:
            messages.error(request, "Invalid transaction type.")
            errors = True

        if not category:
            messages.error(request, "Category is required.")
            errors = True

        tx_date = None
        if not date_str:
            messages.error(request, "Date is required.")
            errors = True
        else:
            try:
                tx_date = datetime.datetime.fromisoformat(date_str)
                if timezone.is_naive(tx_date):
                    tx_date = timezone.make_aware(tx_date)
            except Exception:
                messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
                errors = True

        if errors:
            return redirect('transactions')

        if edit_id:
            try:
                tx = Transaction.objects.get(pk=edit_id, user=request.user)
                tx.name = name
                tx.type = transaction_type
                tx.amount = amount
                tx.category = category
                tx.description = description
                tx.note = note
                if tx_date:
                    tx.date = tx_date
                tx.save()
                messages.success(request, 'Transaction updated.')
            except Transaction.DoesNotExist:
                messages.error(request, 'Transaction not found.')
            return redirect('transactions')

        try:
            tx = Transaction.objects.create(
                user=request.user,
                name=name,
                type=transaction_type,
                amount=amount,
                category=category,
                description=description,
                note=note,
                date=tx_date,
            )
            messages.success(request, 'Transaction added successfully!')
        except Exception as e:
            messages.error(request, f'Failed to add transaction: {str(e)}')

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


@login_required(login_url='login')
def delete_transaction(request, pk):
    """Delete a transaction owned by the current user.

    Args:
        request: Django HttpRequest object.
        pk: Primary key of the transaction to delete.

    Returns:
        HttpResponse redirecting to the transaction list.
    """
    transaction = Transaction.objects.get(id=pk, user=request.user)
    transaction.delete()
    return redirect('transactions')


@login_required(login_url='login')
def budgets_view(request):
    """Manage monthly budgets for the current user.

    GET: renders the budgets for the current month.
    POST: creates or updates a budget for a category for the current
    month and shows a confirmation message.
    """
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


@login_required(login_url='login')
def goals_view(request):
    """Create, edit, and add funds to financial goals.

    Supports multiple POST actions identified by keys in the POST data
    (e.g., `add_funds`, `edit_goal`, `delete_goal`, `add_goal`).
    """
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
        deadline__gte=today
    ).count()

    delayed_goals = goals_queryset.filter(
        current_amount__lt=F('target_amount'),
        deadline__lt=today
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


@login_required(login_url='login')
def reports_view(request):
    """Generate financial reports and export them as PDF.

    The view computes aggregates for income, expenses, budgets and
    goals over a date range (default last 30 days) and builds an
    `insights` list with personalized advice. If `export_pdf` is in
    POST, attempts to create a PDF using xhtml2pdf with a WeasyPrint
    fallback.
    """
    from django.db.models import Sum as _Sum

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

    try:
        start = parse_date(start_date) if start_date else (timezone.now() - datetime.timedelta(days=30)).date()
        end = parse_date(end_date) if end_date else timezone.now().date()
    except Exception:
        start = (timezone.now() - datetime.timedelta(days=30)).date()
        end = timezone.now().date()

    transactions = Transaction.objects.filter(user=request.user, date__date__gte=start, date__date__lte=end).order_by('-date')

    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    budget_alert_threshold = getattr(user_profile, 'budget_alert_threshold', 90)

    total_income = transactions.filter(type='income').aggregate(_Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='expense').aggregate(_Sum('amount'))['amount__sum'] or 0

    expense_qs = transactions.filter(type='expense').values('category').annotate(total=_Sum('amount')).order_by('-total')

    palette = ["#ef4444", "#f59e0b", "#6366f1", "#10b981", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"]
    expense_rows = []
    for i, r in enumerate(expense_qs):
        amt = float(r['total'])
        percent = (amt / float(total_expenses) * 100) if total_expenses else 0
        expense_rows.append({
            'category': r['category'],
            'total': round(amt, 2),
            'percent': round(percent, 1),
            'color': palette[i % len(palette)]
        })

    budgets = Budget.objects.filter(user=request.user, period__gte=start.replace(day=1), period__lte=end)

    goals = Goal.objects.filter(user=request.user)
    goals_total_target = goals.aggregate(_Sum('target_amount'))['target_amount__sum'] or 0
    goals_total_saved = goals.aggregate(_Sum('current_amount'))['current_amount__sum'] or 0

    week_labels = []
    income_by_week = []
    expense_by_week = []
    week_start = start - datetime.timedelta(days=start.weekday())
    cur = week_start
    while cur <= end:
        week_end = cur + datetime.timedelta(days=6)
        lbl = f"{cur.strftime('%b %d')}"
        week_labels.append(lbl)
        q_start = cur if cur >= start else start
        q_end = week_end if week_end <= end else end
        week_tx = transactions.filter(date__date__gte=q_start, date__date__lte=q_end)
        income_sum = week_tx.filter(type='income').aggregate(_Sum('amount'))['amount__sum'] or 0
        expense_sum = week_tx.filter(type='expense').aggregate(_Sum('amount'))['amount__sum'] or 0
        income_by_week.append(float(income_sum))
        expense_by_week.append(float(expense_sum))
        cur = week_end + datetime.timedelta(days=1)

    insights = []
    days = (end - start).days + 1
    avg_daily_spend = float(total_expenses) / days if days > 0 else 0

    if expense_rows:
        top = expense_rows[0]
        insights.append({
            'title': f"Top Spending: {top['category']}",
            'text': f"You spent ${top['total']} ({top['percent']}%) on {top['category']} during this period.",
            'severity': 'warning'
        })

    insights.append({
        'title': 'Average Daily Spend',
        'text': f"Average daily expenses: ${avg_daily_spend:.2f} over {days} days.",
        'severity': 'info'
    })

    overages = []
    for b in budgets:
        spent = Transaction.objects.filter(user=request.user, category=b.category, type='expense', date__date__gte=start, date__date__lte=end).aggregate(Sum('amount'))['amount__sum'] or 0
        if spent > b.amount_limit:
            overages.append({'category': b.category, 'spent': float(spent), 'limit': float(b.amount_limit), 'over_by': float(spent - b.amount_limit)})
        else:
            try:
                percent_used = (float(spent) / float(b.amount_limit) * 100) if b.amount_limit else 0
            except Exception:
                percent_used = 0
            if percent_used >= budget_alert_threshold and percent_used < 100:
                insights.append({
                    'title': f"Budget Alert: {b.category}",
                    'text': f"You've used {percent_used:.0f}% (${float(spent):.2f}) of your {b.category} budget limit (${float(b.amount_limit):.2f}). Consider reducing non-essential spending or increasing the budget.",
                    'severity': 'warning'
                })
    if overages:
        insights.append({
            'title': 'Budgets Exceeded',
            'text': f"You exceeded {len(overages)} budget(s): {', '.join(o['category'] for o in overages)}.",
            'severity': 'danger'
        })

    if total_income:
        savings_rate = (float(goals_total_saved) / float(total_income)) * 100
        insights.append({
            'title': 'Savings Rate',
            'text': f"You've saved ${goals_total_saved} across goals — {savings_rate:.1f}% of income in this period.",
            'severity': 'success' if savings_rate >= 20 else 'info'
        })

    delayed_count = Goal.objects.filter(user=request.user, current_amount__lt=F('target_amount'), deadline__lt=timezone.now().date()).count()
    if delayed_count:
        insights.append({
            'title': 'Delayed Goals',
            'text': f"You have {delayed_count} goal(s) behind schedule. Consider reallocating funds.",
            'severity': 'warning'
        })

    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'expense_rows': expense_rows,
        'budgets': budgets,
        'goals': goals,
        'goals_total_target': goals_total_target,
        'goals_total_saved': goals_total_saved,
        'insights': insights,
        'start': start,
        'end': end,
        'expense_labels_json': json.dumps([r['category'] for r in expense_rows]),
        'expense_values_json': json.dumps([r['total'] for r in expense_rows]),
        'colors_json': json.dumps([r['color'] for r in expense_rows]),
        'week_labels_json': json.dumps(week_labels),
        'income_by_week_json': json.dumps(income_by_week),
        'expense_by_week_json': json.dumps(expense_by_week),
        'start_iso': start.isoformat() if hasattr(start, 'isoformat') else str(start),
        'end_iso': end.isoformat() if hasattr(end, 'isoformat') else str(end),
    }

    if request.method == 'POST' and 'export_pdf' in request.POST:
        try:
            import io
            import logging
            from xhtml2pdf import pisa

            html_string = render_to_string('main/report_pdf.html', context, request=request)
            result = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=result)
            if not getattr(pisa_status, 'err', 1):
                pdf_bytes = result.getvalue()
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                filename = f"report_{request.user.username}_{start}_{end}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            else:
                logging.error('xhtml2pdf reported an error while generating PDF')
        except Exception:
            import logging
            logging.exception('xhtml2pdf failed to generate PDF')

        try:
            from weasyprint import HTML, CSS
            html_string = render_to_string('main/report_pdf.html', context, request=request)
            html = HTML(string=html_string)
            css = CSS(string='@page { size: A4; margin: 20mm } body { font-family: "Helvetica", "Arial", sans-serif; }')
            pdf = html.write_pdf(stylesheets=[css])
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"report_{request.user.username}_{start}_{end}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception:
            import logging
            logging.exception('WeasyPrint fallback failed')

        err_msg = 'PDF generation failed on the server. Ensure xhtml2pdf or WeasyPrint is installed and working.'
        messages.error(request, err_msg)
        return HttpResponse(err_msg, status=500, content_type='text/plain')

    return render(request, 'main/reports.html', context)


@login_required(login_url='login')
def profile(request):
    """Display and update the current user's profile.

    Handles updating personal info, changing password, deleting the
    account, and setting the budget alert threshold. Uses Django
    messages to inform the user of success or validation errors.
    """
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user = request.user
        if 'budget_alert_threshold' in request.POST:
            try:
                val = int(request.POST.get('budget_alert_threshold') or user_profile.budget_alert_threshold)
            except (TypeError, ValueError):
                messages.error(request, 'Invalid budget alert threshold value.')
                return redirect('profile')
            val = max(0, min(100, val))
            user_profile.budget_alert_threshold = val
            user_profile.save()
            messages.success(request, f'Budget alert threshold set to {val}%')
            return redirect('profile')
        if 'first_name' in request.POST or 'email' in request.POST:
            first_name = request.POST.get('first_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            dob = request.POST.get('dob')
            email = email.strip() if email else email
            if not email :
                messages.error(request, 'Email cannot be blank')
                return redirect('profile')
            if email and User.objects.filter(username=email).exclude(pk=user.pk).exists():
                messages.error(request, 'Email already in use by another account.')
                return redirect('profile')
            user.first_name = first_name
            user.email = email
            if email:
                user.username = email
            user.save()
            user_profile.phone = phone
            if dob:
                user_profile.date_of_birth = dob
            user_profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        if 'update_password' in request.POST:
            current = request.POST.get('current_password')
            new = request.POST.get('new_password')
            confirm = request.POST.get('new_password_confirm')
            if not current or not new or not confirm:
                messages.error(request, 'Please fill all password fields.')
                return redirect('profile')
            if not user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile')
            if new != confirm:
                messages.error(request, 'New passwords do not match.')
                return redirect('profile')
            if len(new) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return redirect('profile')
            user.set_password(new)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('profile')

        if 'delete_account' in request.POST:
            confirm_pw = request.POST.get('confirm_password')
            if not confirm_pw:
                messages.error(request, 'Please enter your password to confirm account deletion.')
                return redirect('profile')
            if not user.check_password(confirm_pw):
                messages.error(request, 'Password incorrect. Account not deleted.')
                return redirect('profile')
            username = user.username
            try:
                user.delete()
                logout(request)
                messages.success(request, f'Account {username} deleted successfully.')
                return redirect('login')
            except Exception:
                messages.error(request, 'Failed to delete account. Please contact support.')
                return redirect('profile')
    transactions_count = Transaction.objects.filter(user=request.user).count()
    active_goals_count = Goal.objects.filter(user=request.user, current_amount__lt=F('target_amount')).count()
    budgets_count = Budget.objects.filter(user=request.user).count()
    goals_total_saved = Goal.objects.filter(user=request.user).aggregate(Sum('current_amount'))['current_amount__sum'] or 0

    context = {
        'user_profile': user_profile,
        'transactions_count': transactions_count,
        'active_goals_count': active_goals_count,
        'budgets_count': budgets_count,
        'goals_total_saved': goals_total_saved,
    }
    return render(request, 'main/profile.html', context)
    


@login_required(login_url='login')
def logout_view(request):
    """Log out the current user and redirect to the login page."""
    logout(request)
    return redirect('login')
