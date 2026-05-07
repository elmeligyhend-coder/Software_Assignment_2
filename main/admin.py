"""Admin registration for the `main` app models.

Registers the primary models so they are manageable via the Django
admin site.
"""

from django.contrib import admin
from .models import Transaction
from .models import Goal
from .models import Budget
from .models import Profile

admin.site.register(Transaction)
admin.site.register(Goal)
admin.site.register(Budget)
admin.site.register(Profile)
