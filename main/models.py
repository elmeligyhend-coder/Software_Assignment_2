from django.db import models
from django.contrib.auth.models import User 
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    def __str__(self):
        return f'{self.user.username} Profile'

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50) 
    description = models.TextField(blank=True, null=True)

    date = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'categories'

class Budget(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category   = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    period     = models.DateField()
    alert      = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budgets'
        unique_together = ('user', 'category', 'period')

class Goal(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name          = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline      = models.DateField()
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def getProgress(self):
        if self.target_amount == 0:
            return 0.0
        return round(float(self.saved_amount / self.target_amount * 100), 2)

    class Meta:
        db_table = 'goals'