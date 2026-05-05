from .models import Budget, Category, Goal  

class GoalRepository:
    """
    طبقة الـ Data Access للأهداف
    Methods بتطابق الأسهم بين GoalRepository والـ Database في الـ SD
    """

    @staticmethod
    def saveGoal(goal: Goal) -> Goal:
        """
        يطابق السهم: saveGoal(goal:Goal) من GoalService إلى GoalRepository في الـ SD
        بعده: INSERT Goal(...) للـ Database
        بيرجع: goal:Goal
        """
        goal.save()
        return goal

    @staticmethod
    def updateGoal(goal_id: int, amount) -> Goal:
        """
        يطابق السهم: updateGoal(goalId:int, amount:decimal) في الـ SD - Track Progress section
        بعده: UPDATE Goal(...) للـ Database
        بيرجع: goal:Goal
        """
        goal = Goal.objects.get(id=goal_id)
        goal.saved_amount = amount
        goal.save()
        return goal

    @staticmethod
    def getGoalById(goal_id: int):
        try:
            return Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            return None

    @staticmethod
    def getGoalsByUser(user) -> list:
        """
        جلب كل الأهداف الخاصة بـ User معين
        بُتستخدم في displayGoalsListWithProgress() في الـ SD
        """
        return list(Goal.objects.filter(user=user))



class BudgetRepository:
    """
    طبقة الـ Data Access - بتتعامل مع قاعدة البيانات مباشرة
    Methods بتطابق الأسهم بين BudgetRepository والـ Database في الـ SD
    """

    @staticmethod
    def saveBudget(budget: Budget) -> Budget:
        """
        يطابق السهم: saveBudget(budget:Budget) في الـ SD
        بعده INSERT/UPDATE Budget(...) للـ Database
        """
        budget.save()
        return budget

    @staticmethod
    def getBudgetById(budget_id: int):
        try:
            return Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist:
            return None

    @staticmethod
    def getBudgetsByUser(user) -> list:
        """
        جلب كل الميزانيات الخاصة بـ User معين
        بُتستخدم في displayUpdatedBudgets() في الـ SD
        """
        return list(Budget.objects.filter(user=user).select_related('category'))

    @staticmethod
    def checkExistingBudget(category_id: int, period, user) -> bool:
        """
        يطابق السهم: checkExistingBudget(categoryId:int, period:Date) في الـ SD
        بيرجع True لو في ميزانية موجودة لنفس الفئة في نفس الـ period
        """
        return Budget.objects.filter(
            user=user,
            category_id=category_id,
            period=period
        ).exists()

    @staticmethod
    def getCategoryById(category_id: int):
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None