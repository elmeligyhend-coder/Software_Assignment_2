from django.db import models
from django.contrib.auth.models import User 
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    def __str__(self):
        return f'{self.user.username} Profile'

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50) 
    type = models.CharField(max_length=10, choices=[('income', 'Income'), ('expense', 'Expense')], default='expense') 
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.DateField()

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200) 
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=100, default='Savings')
    created_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min(int((self.current_amount / self.target_amount) * 100), 100)
        return 0