from .repositories import BudgetRepository, GoalRepository 
from decimal import Decimal, InvalidOperation
from datetime import date
from .models import Budget, Category, Goal  

class BudgetService:
    """
    طبقة الـ Business Logic
    Methods بتطابق الأسهم بين BudgetController و BudgetService في الـ SD
    """

    @staticmethod
    def validateBudget(category_id: int, amount: Decimal, period: date) -> bool:
        """
        يطابق السهم: validateBudget(categoryId:int, amount:decimal, period:Date) في الـ SD
        بيرجع: boolean (true/false)
        """
        if not category_id or not isinstance(category_id, int) or category_id <= 0:
            return False

        try:
            amount_val = Decimal(str(amount))
            if amount_val <= 0:
                return False
        except (InvalidOperation, TypeError):
            return False

        if not period or not isinstance(period, date):
            return False

        return True

    @staticmethod
    def createOrUpdateBudget(category_id: int, amount: Decimal, period: date, alert: bool, user) -> Budget:
        """
        يطابق السهم: createOrUpdateBudget(categoryId:int, amount:decimal, period:Date, alert:boolean)
        بيرجع: budget:Budget كما هو موضح في الـ SD
        بيعمل INSERT لو جديد أو UPDATE لو موجود
        """
        category = BudgetRepository.getCategoryById(category_id)

        existing = Budget.objects.filter(
            user=user,
            category=category,
            period=period
        ).first()

        if existing:
            existing.amount = amount
            existing.alert  = alert
            budget = BudgetRepository.saveBudget(existing)
        else:
            new_budget = Budget(
                user     = user,
                category = category,
                amount   = amount,
                period   = period,
                alert    = alert,
            )
            budget = BudgetRepository.saveBudget(new_budget)

        return budget

    @staticmethod
    def checkExistingBudget(category_id: int, period: date, user) -> bool:
        """
        يطابق السهم: checkExistingBudget(categoryId:int, period:Date) في الـ SD
        alt block [Budget Already Exists]
        """
        return BudgetRepository.checkExistingBudget(category_id, period, user)


class GoalService:
    """
    طبقة الـ Business Logic للأهداف
    Methods بتطابق الأسهم بين GoalController و GoalService في الـ SD
    """

    @staticmethod
    def validateGoal(name: str, target_amount: Decimal, deadline: date) -> bool:
        """
        يطابق السهم: validateGoal(name:String, targetAmount:decimal, deadline:Date): boolean
        من GoalController إلى GoalService في الـ SD
        بيرجع: boolean (true/false)
        """
        if not name or not isinstance(name, str) or len(name.strip()) == 0:
            return False

        try:
            amount_val = Decimal(str(target_amount))
            if amount_val <= 0:
                return False
        except (InvalidOperation, TypeError):
            return False

        if not deadline or not isinstance(deadline, date):
            return False

        if deadline <= date.today():
            return False

        return True

    @staticmethod
    def saveGoal(name: str, target_amount: Decimal, deadline: date, initial_amount: Decimal, user) -> Goal:
        """
        يطابق السهم: saveGoal(name:String, targetAmount:decimal, deadline:Date, initialAmount:decimal): Goal
        من GoalService إلى GoalRepository في الـ SD
        بيرجع: goal:Goal
        """
        new_goal = Goal(
            user          = user,
            name          = name,
            target_amount = target_amount,
            saved_amount  = initial_amount,
            deadline      = deadline,
        )
        return GoalRepository.saveGoal(new_goal)

    @staticmethod
    def updateSavedAmount(goal_id: int, amount: Decimal) -> Goal:
        """
        يطابق السهم: updateSavedAmount(goalId:int, amount:decimal): Goal
        من GoalController إلى GoalService في الـ SD - Track Progress section
        بيرجع: goal:Goal
        """
        goal = GoalRepository.getGoalById(goal_id)
        if goal is None:
            raise ValueError(f"Goal with id {goal_id} not found")

        new_saved = goal.saved_amount + amount
        return GoalRepository.updateGoal(goal_id, new_saved)
