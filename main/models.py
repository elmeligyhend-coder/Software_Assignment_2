from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        default="expense",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.DateField()

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField()