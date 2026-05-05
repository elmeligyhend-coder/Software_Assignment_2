from django.urls import path
from . import views


urlpatterns = [
    path("",views.main,name="main"),
    path("login/",views.login_view,name="login"),
    path("signup/",views.signup_view,name="signup"),
    path("dashboard/",views.dashboard_view,name="dashboard"),
    path("transactions/",views.transactions_view,name="transactions"),
    path("budgets/",views.budgets_view,name="budgets"),
    path("goals/",views.goals_view,name="goals"),
    path("reports/",views.reports_view,name="reports"),
    path("profile/",views.profile,name="profile"),
    path('logout/', views.logout_view, name='logout'),
    path('api/budgets/', views.BudgetController.as_view(), name='budgets'),
    path('api/budgets/<int:budget_id>/', views.BudgetController.as_view(), name='budget_detail'),
    path('api/goals/', views.GoalController.as_view(), name='goals'),
    path('api/goals/<int:goal_id>/progress/', views.GoalProgressController.as_view(), name='goal_progress'),
]
