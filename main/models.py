"""Database models for the main budgeting application.

This module defines the application's primary Django models: `Profile`,
`Transaction`, `Budget`, and `Goal`. Models include convenience properties
used by templates and views.
"""

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """User profile information attached to a Django `User`.

    Attributes
    ----------
    user : User
        One-to-one link to the Django `User` instance.
    phone : str
        Optional phone number string.
    date_of_birth : date
        Optional date of birth.
    budget_alert_threshold : int
        Percentage threshold used to trigger budget alerts (0-100).
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    budget_alert_threshold = models.PositiveIntegerField(default=90)

    def __str__(self):
        """Return a human-readable representation of the profile.

        Returns the username followed by the word "Profile".
        """
        return f"{self.user.username} Profile"


class Transaction(models.Model):
    """A financial transaction record.

    Attributes
    ----------
    user : User
        Owner of the transaction.
    amount : Decimal
        Monetary amount for the transaction. This field uses a
        deferred-loading database implementation; the query is executed
        the first time the value is accessed. Use `help_text` and
        `verbose_name` on the field to surface human-friendly text in
        admin pages and documentation.
    category : str
        Category name for grouping transactions (e.g., "Food", "Rent").
    type : str
        Either 'income' or 'expense'.
    name : str
        Optional short title for the transaction.
    description : str
        Optional long description.
    note : str
        Optional internal note.
    date : datetime
        Timestamp when the transaction was created.
    """

    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount",
        help_text="Transaction amount in the account's currency (e.g., USD).",
    )
    category = models.CharField(max_length=50)
    type = models.CharField(
        max_length=10,
        choices=[("income", "Income"), ("expense", "Expense")],
        default="expense",
    )
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a readable description of the transaction.

        Example: "Expense 12.50 - Food (alice@example.com)".
        """
        return f"{self.get_type_display()} {self.amount} - {self.category} ({self.user.username})"

    @property
    def transaction_type(self):
        """Alias property for template compatibility.

        Some templates expect `transaction.transaction_type` while the
        database field is named `type`. This property returns the same
        value as the `type` field.
        """
        return self.type


class Budget(models.Model):
    """A budget tied to a user and category.

    Attributes
    ----------
    user : User
        Owner of the budget.
    category : str
        Budget category name.
    amount_limit : Decimal
        The maximum allowed spending for the budget period.
    period : date
        The date representing the budgeting period (e.g., month start).
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.DateField()

    def __str__(self):
        """Human-readable representation of a budget record."""
        return f"Budget {self.category}: {self.amount_limit} for {self.user.username} ({self.period})"


class Goal(models.Model):
    """A saving or financial goal for a user.

    Attributes
    ----------
    user : User
        Owner of the goal.
    title : str
        A short title for the goal.
    target_amount : Decimal
        The target amount to reach.
    current_amount : Decimal
        Current saved amount toward the target.
    deadline : date
        Optional target date to reach the goal.
    category : str
        Category for the goal (defaults to 'Savings').
    created_at : datetime
        Timestamp when the goal was created.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=100, default="Savings")
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """Return a short description for the goal."""
        return f"{self.title} - {self.user.username}"

    @property
    def progress_percentage(self):
        """Calculate and return the goal progress as an integer percentage.

        The value is clamped to 100 and returns 0 if `target_amount` is
        zero or not set.
        """
        if self.target_amount > 0:
            return min(int((self.current_amount / self.target_amount) * 100), 100)
        return 0
