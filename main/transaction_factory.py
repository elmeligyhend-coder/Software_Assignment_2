from decimal import Decimal

from .models import Transaction


class BaseTransaction:
    def __init__(self, user, amount, category, name, description, note, date):
        self.user = user
        self.amount = Decimal(amount)
        self.category = category
        self.name = name
        self.description = description
        self.note = note
        self.date = date

    def create(self):
        raise NotImplementedError("Subclasses must implement create()")


class IncomeTransaction(BaseTransaction):
    TRANSACTION_TYPE = "income"

    def create(self):
        return Transaction(
            user=self.user,
            transaction_type=self.TRANSACTION_TYPE,
            amount=self.amount,
            category=self.category,
            name=self.name,
            description=self.description,
            note=self.note,
            date=self.date,
        )


class ExpenseTransaction(BaseTransaction):
    TRANSACTION_TYPE = "expense"

    def create(self):
        return Transaction(
            user=self.user,
            transaction_type=self.TRANSACTION_TYPE,
            amount=self.amount,
            category=self.category,
            name=self.name,
            description=self.description,
            note=self.note,
            date=self.date,
        )


class TransactionFactory:
    @staticmethod
    def create_transaction(transaction_type, user, amount, category, name, description, note, date):
        if transaction_type == "income":
            return IncomeTransaction(user, amount, category, name, description, note, date).create()
        if transaction_type == "expense":
            return ExpenseTransaction(user, amount, category, name, description, note, date).create()
        raise ValueError("Invalid transaction type")
