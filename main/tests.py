from django.test import TestCase
from django.contrib.auth.models import User
from .models import Transaction, Category

class TransactionTestCase(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username='abdullah', password='123')
        self.category = Category.objects.create(name='Food')

    def test_add_transaction(self):
        
        t = Transaction.objects.create(
            user=self.user,
            amount=150.00,
            transaction_type='EX',
            category=self.category
        )
        self.assertEqual(t.amount, 150.00)
        self.assertEqual(t.transaction_type, 'EX')