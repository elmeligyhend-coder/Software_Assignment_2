from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login , authenticate , logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile  

from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .services import BudgetService, GoalService
from .repositories import BudgetRepository, GoalRepository
from django.utils.decorators import method_decorator

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


@method_decorator(csrf_exempt, name='dispatch')
class GoalController(View):
    """
    يطابق الـ GoalController في الـ SD
    بيستقبل الطلبات من GoalUI ويوجّهها للـ GoalService
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """
        يطابق: clickAddGoal() → displayGoalForm() في الـ SD
        + displayGoalsListWithProgress() بعد إنشاء الهدف
        بيرجع كل الأهداف مع نسبة التقدم (getProgress())
        """
        goals = GoalRepository.getGoalsByUser(request.user)
        data = [
            {
                'id'           : g.id,
                'name'         : g.name,
                'target_amount': str(g.target_amount),
                'saved_amount' : str(g.saved_amount),
                'deadline'     : str(g.deadline),
                'progress'     : g.getProgress(),
            }
            for g in goals
        ]
        return JsonResponse({'goals': data}, status=200)

    def post(self, request):
        """
        يطابق السهم: createGoal(name:String, targetAmount:decimal, deadline:Date, initialAmount:decimal)
        من GoalUI إلى GoalController في الـ SD

        الخطوات بتطابق الـ SD بالترتيب:
        1. submitGoal()     → استقبال البيانات
        2. createGoal()     → استدعاء GoalService
        3. validateGoal()   → التحقق
        4. saveGoal()       → الحفظ
        5. redirectToGoals() → الرد
        """
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            name           = str(body.get('name', '')).strip()
            target_amount  = Decimal(str(body.get('targetAmount', 0)))
            deadline_str   = body.get('deadline', '')
            initial_amount = Decimal(str(body.get('initialAmount', 0)))
            deadline       = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except (ValueError, InvalidOperation, TypeError):
            return JsonResponse({'error': 'Invalid input data'}, status=400)

        # ── validateGoal(name, targetAmount, deadline) ────────────────────────
        is_valid = GoalService.validateGoal(name, target_amount, deadline)
        if not is_valid:
            return JsonResponse(
                {'error': 'Invalid input. Check name, amount, and deadline.'},
                status=422
            )

        # ── saveGoal(name, targetAmount, deadline, initialAmount): Goal ───────
        goal = GoalService.saveGoal(
            name           = name,
            target_amount  = target_amount,
            deadline       = deadline,
            initial_amount = initial_amount,
            user           = request.user,
        )

        # redirectToGoals() + displayGoalsListWithProgress() في الـ SD
        return JsonResponse(
            {
                'message': 'Goal created successfully',
                'goal'   : {
                    'id'           : goal.id,
                    'name'         : goal.name,
                    'target_amount': str(goal.target_amount),
                    'saved_amount' : str(goal.saved_amount),
                    'deadline'     : str(goal.deadline),
                    'progress'     : goal.getProgress(),
                },
            },
            status=201
        )

@method_decorator(csrf_exempt, name='dispatch')
class GoalProgressController(View):
    """
    يطابق الـ Track Progress section في الـ SD US#6
    """
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, goal_id: int):
        """
        يطابق السهم: updateGoalProgress(goalId:int, amount:decimal)
        من GoalUI إلى GoalController في الـ SD - Track Progress section

        الخطوات:
        1. addContribution(goalId, amount)   → من الـ User
        2. updateGoalProgress(goalId, amount) → GoalController
        3. updateSavedAmount(goalId, amount)  → GoalService
        4. updateGoal(goalId, amount)         → GoalRepository
        5. updateProgressBar(goal:Goal)       → GoalUI
        """
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            amount = Decimal(str(body.get('amount', 0)))
            if amount <= 0:
                return JsonResponse({'error': 'Amount must be positive'}, status=400)
        except (InvalidOperation, TypeError):
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        goal = GoalRepository.getGoalById(goal_id)
        if goal is None or goal.user != request.user:
            return JsonResponse({'error': 'Goal not found'}, status=404)

        # ── updateSavedAmount(goalId, amount): Goal ───────────────────────────
        updated_goal = GoalService.updateSavedAmount(goal_id, amount)

        # updateProgressBar(goal:Goal) + displayUpdatedProgress() في الـ SD
        return JsonResponse(
            {
                'message': 'Progress updated successfully',
                'goal'   : {
                    'id'           : updated_goal.id,
                    'name'         : updated_goal.name,
                    'target_amount': str(updated_goal.target_amount),
                    'saved_amount' : str(updated_goal.saved_amount),
                    'deadline'     : str(updated_goal.deadline),
                    'progress'     : updated_goal.getProgress(),
                },
            },
            status=200
        )


@method_decorator(csrf_exempt, name='dispatch')
class BudgetController(View):
    """
    يطابق الـ BudgetController في الـ SD
    بيستقبل الطلبات من BudgetUI ويوجّهها للـ BudgetService
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """
        يطابق: clickNewBudget() / selectBudget(budgetId:int) في الـ SD
        + displayBudgetForm() و displayUpdatedBudgets() الراجعين للـ User
        """
        budgets = BudgetRepository.getBudgetsByUser(request.user)
        data = [
            {
                'id'         : b.id,
                'category_id': b.category.id,
                'category'   : b.category.name,
                'amount'     : str(b.amount),
                'period'     : str(b.period),
                'alert'      : b.alert,
            }
            for b in budgets
        ]
        return JsonResponse({'budgets': data}, status=200)

    def post(self, request):
        """
        يطابق السهم: saveBudget(categoryId:int, amount:decimal, period:Date, alert:boolean)
        من BudgetUI إلى BudgetController في الـ SD

        الخطوات بتطابق الـ SD بالترتيب:
        1. submitBudget()            → استقبال البيانات
        2. validateBudget()          → التحقق
        3. createOrUpdateBudget()    → الحفظ
        4. checkExistingBudget()     → لو conflict
        5. showError() / redirect()  → الرد
        """
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            category_id = int(body.get('categoryId', 0))
            amount      = Decimal(str(body.get('amount', 0)))
            period_str  = body.get('period', '')
            alert       = bool(body.get('alert', False))
            period      = datetime.strptime(period_str, '%Y-%m-%d').date()
        except (ValueError, InvalidOperation, TypeError):
            return JsonResponse({'error': 'Invalid input data'}, status=400)

        # ── validateBudget(categoryId, amount, period) ────────────────────────
        is_valid = BudgetService.validateBudget(category_id, amount, period)
        if not is_valid:
            return JsonResponse(
                {'error': 'Invalid input data. Please check all fields.'},
                status=422
            )

        # ── checkExistingBudget(categoryId, period) ───────────────────────────
        # alt block [Budget Already Exists] في الـ SD
        already_exists = BudgetService.checkExistingBudget(category_id, period, request.user)
        if already_exists:
            # showError(message:String) → "Budget already exists for this category"
            return JsonResponse(
                {'error': 'Budget already exists for this category'},
                status=409
            )

        # ── createOrUpdateBudget(categoryId, amount, period, alert) ──────────
        budget = BudgetService.createOrUpdateBudget(
            category_id = category_id,
            amount      = amount,
            period      = period,
            alert       = alert,
            user        = request.user,
        )

        # redirectToBudgets() + displayUpdatedBudgets() في الـ SD
        return JsonResponse(
            {
                'message': 'Budget saved successfully',
                'budget' : {
                    'id'      : budget.id,
                    'category': budget.category.name,
                    'amount'  : str(budget.amount),
                    'period'  : str(budget.period),
                    'alert'   : budget.alert,
                },
            },
            status=201
        )

    def put(self, request, budget_id=None):
        """
        يطابق: selectBudget(budgetId:int) في الـ SD لتعديل ميزانية موجودة
        """
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            category_id = int(body.get('categoryId', 0))
            amount      = Decimal(str(body.get('amount', 0)))
            period_str  = body.get('period', '')
            alert       = bool(body.get('alert', False))
            period      = datetime.strptime(period_str, '%Y-%m-%d').date()
        except (ValueError, InvalidOperation, TypeError):
            return JsonResponse({'error': 'Invalid input data'}, status=400)

        is_valid = BudgetService.validateBudget(category_id, amount, period)
        if not is_valid:
            return JsonResponse({'error': 'Invalid input data'}, status=422)

        budget = BudgetService.createOrUpdateBudget(
            category_id = category_id,
            amount      = amount,
            period      = period,
            alert       = alert,
            user        = request.user,
        )

        return JsonResponse(
            {
                'message': 'Budget updated successfully',
                'budget' : {
                    'id'      : budget.id,
                    'category': budget.category.name,
                    'amount'  : str(budget.amount),
                    'period'  : str(budget.period),
                    'alert'   : budget.alert,
                },
            },
            status=200
        )


