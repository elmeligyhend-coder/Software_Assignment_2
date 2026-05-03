from django.contrib import admin, messages
from .models import Transaction, Category, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_custom')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'category', 'date_time')
    list_filter = ('transaction_type', 'category', 'date_time')
    search_fields = ('description', 'note')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        budget = Budget.objects.filter(user=obj.user, category=obj.category).first()
        if budget and budget.current_spending > budget.limit_amount:
            messages.warning(
                request, 
                f"ALERT: You have exceeded the budget for {obj.category.name}! "
                f"Current: {budget.current_spending} | Limit: {budget.limit_amount}"
            )

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'limit_amount', 'current_spending')
    list_filter = ('user', 'category')