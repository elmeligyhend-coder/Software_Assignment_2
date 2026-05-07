from django.urls import path
from . import views


urlpatterns = [
    path("",views.main,name="main"),
    path("login/",views.login_view,name="login"),
    path("signup/",views.signup_view,name="signup"),
    path("dashboard/",views.dashboard_view,name="dashboard"),
    path("transactions/",views.transactions_view,name="transactions"),
    path("transactions/update/<int:id>/", views.update_transaction, name="update_transaction"),
    path("transactions/delete/<int:id>/", views.delete_transaction, name="delete_transaction"),
    path("budgets/",views.budgets_view,name="budgets"),
    path("goals/",views.goals_view,name="goals"),
    path("reports/",views.reports_view,name="reports"),
    path("profile/",views.profile,name="profile"),
    path('logout/', views.logout_view, name='logout'),
]
