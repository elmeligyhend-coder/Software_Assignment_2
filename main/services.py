from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.utils import timezone

from .models import Transaction, Goal, Budget, Profile


class UserRepository(ABC):
    @abstractmethod
    def create_user(self, username: str, email: str, password: str, first_name: str = "") -> User:
        pass

    @abstractmethod
    def get_user(self, username: str) -> Optional[User]:
        pass


class TransactionRepository(ABC):
    @abstractmethod
    def create(self, **kwargs) -> Transaction:
        pass

    @abstractmethod
    def update(self, tx: Transaction, **kwargs) -> Transaction:
        pass

    @abstractmethod
    def delete(self, tx: Transaction) -> None:
        pass


class NotificationInterface(ABC):
    @abstractmethod
    def notify(self, user: User, message: str, level: str = "info") -> None:
        pass


class DjangoUserRepository(UserRepository):
    def create_user(self, username: str, email: str, password: str, first_name: str = "") -> User:
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = first_name
        user.save()
        return user

    def get_user(self, username: str) -> Optional[User]:
        return User.objects.filter(username=username).first()


class DjangoTransactionRepository(TransactionRepository):
    def create(self, **kwargs) -> Transaction:
        return Transaction.objects.create(**kwargs)

    def update(self, tx: Transaction, **kwargs) -> Transaction:
        for k, v in kwargs.items():
            setattr(tx, k, v)
        tx.save()
        return tx

    def delete(self, tx: Transaction) -> None:
        tx.delete()


class LoggingNotificationService(NotificationInterface):
    def notify(self, user: User, message: str, level: str = "info") -> None:
        Profile.objects.get_or_create(user=user)


#SRP
class UserService:
    def __init__(self, repo: UserRepository, notifier: NotificationInterface):
        self.repo = repo
        self.notifier = notifier

    def register(self, username: str, email: str, password: str, full_name: str = "") -> User:
        user = self.repo.create_user(username, email, password, first_name=full_name)
        self.notifier.notify(user, "Welcome! Your account has been created.")
        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        return authenticate(username=username, password=password)

    def update_profile(self, user: User, **kwargs) -> User:
        if "email" in kwargs and kwargs["email"]:
            user.email = kwargs["email"]
            user.username = kwargs["email"]
        if "first_name" in kwargs:
            user.first_name = kwargs["first_name"]
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        if "phone" in kwargs:
            profile.phone = kwargs["phone"]
        if "date_of_birth" in kwargs:
            profile.date_of_birth = kwargs["date_of_birth"]
        profile.save()
        return user

    def change_password(self, user: User, new_password: str) -> None:
        user.set_password(new_password)
        user.save()

    def delete_account(self, user: User) -> None:
        username = user.username
        user.delete()

#OCP
class BaseTransaction(ABC):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abstractmethod
    def create(self, repo: TransactionRepository) -> Transaction:
        pass


class IncomeTransaction(BaseTransaction):
    def create(self, repo: TransactionRepository) -> Transaction:
        self.kwargs.setdefault("type", "income")
        return repo.create(**self.kwargs)


class ExpenseTransaction(BaseTransaction):
    def create(self, repo: TransactionRepository) -> Transaction:
        self.kwargs.setdefault("type", "expense")
        return repo.create(**self.kwargs)


class TransactionFactory:
    mapping = {"income": IncomeTransaction, "expense": ExpenseTransaction}

    @classmethod
    def create_transaction(cls, tx_type: str, **kwargs) -> BaseTransaction:
        cls_type = cls.mapping.get(tx_type)
        if not cls_type:
            raise ValueError(f"Unknown transaction type: {tx_type}")
        return cls_type(**kwargs)


class Observer(ABC):
    @abstractmethod
    def update(self, tx: Transaction) -> None:
        pass


class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def register(self, obs: Observer) -> None:
        self._observers.append(obs)

    def unregister(self, obs: Observer) -> None:
        self._observers.remove(obs)

    def notify_all(self, tx: Transaction) -> None:
        for o in self._observers:
            try:
                o.update(tx)
            except Exception:
                pass


class BudgetObserver(Observer):
    def update(self, tx: Transaction) -> None:
        if tx.type == "expense":
            budgets = Budget.objects.filter(user=tx.user, category=tx.category)
            for b in budgets:
                pass


class GoalObserver(Observer):
    def update(self, tx: Transaction) -> None:
        if tx.type == "income":
            goals = Goal.objects.filter(user=tx.user)
            for g in goals.filter(current_amount__lt=F("target_amount"))[:1]:
                g.current_amount += tx.amount
                g.save()
                break


class DashboardObserver(Observer):
    def update(self, tx: Transaction) -> None:
        return


class NotificationObserver(Observer):
    def __init__(self, notifier: NotificationInterface):
        self.notifier = notifier

    def update(self, tx: Transaction) -> None:
        profile, _ = Profile.objects.get_or_create(user=tx.user)
        threshold = getattr(profile, "budget_alert_threshold", 90)
        if tx.type == "expense" and tx.amount and float(tx.amount) > 1000:
            self.notifier.notify(tx.user, f"Large expense recorded: ${tx.amount}", level="warning")


class TransactionService(Subject):
    def __init__(self, repo: TransactionRepository, factory: TransactionFactory, notifier: NotificationInterface):
        super().__init__()
        self.repo = repo
        self.factory = factory
        self.notifier = notifier

    def create_transaction(self, tx_type: str, **kwargs) -> Transaction:
        tx_obj = self.factory.create_transaction(tx_type, **kwargs)
        tx = tx_obj.create(self.repo)
        self.notify_all(tx)
        return tx

    def update_transaction(self, tx: Transaction, **kwargs) -> Transaction:
        tx = self.repo.update(tx, **kwargs)
        self.notify_all(tx)
        return tx

    def delete_transaction(self, tx: Transaction) -> None:
        self.repo.delete(tx)


class ChartStrategy(ABC):
    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class PieChartStrategy(ChartStrategy):
    def generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "pie", "labels": data.get("labels", []), "values": data.get("values", [])}


class BarChartStrategy(ChartStrategy):
    def generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "bar", "labels": data.get("labels", []), "values": data.get("values", [])}


class ReportService:
    def __init__(self, chart_strategy: ChartStrategy = None):
        self.chart_strategy = chart_strategy or PieChartStrategy()

    def generate_expense_report(self, user, start, end) -> Dict[str, Any]:
        transactions = Transaction.objects.filter(user=user, date__date__gte=start, date__date__lte=end)
        expense_qs = (
            transactions.filter(type="expense")
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        labels = [r["category"] for r in expense_qs]
        values = [float(r["total"] or 0) for r in expense_qs]
        chart = self.chart_strategy.generate({"labels": labels, "values": values})
        return {"chart": chart, "labels": labels, "values": values, "rows": list(expense_qs)}


default_user_repo = DjangoUserRepository()
default_tx_repo = DjangoTransactionRepository()
default_notifier = LoggingNotificationService()

default_user_service = UserService(default_user_repo, default_notifier)
default_tx_service = TransactionService(default_tx_repo, TransactionFactory, default_notifier)
default_tx_service.register(BudgetObserver())
default_tx_service.register(NotificationObserver(default_notifier))
default_tx_service.register(DashboardObserver())
default_tx_service.register(GoalObserver())

default_report_service = ReportService()
