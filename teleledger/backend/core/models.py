import uuid
from django.db import models


class Profile(models.Model):
    telegram_id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or str(self.telegram_id)


class Transaction(models.Model):
    INCOME, EXPENSE = "income", "expense"
    TYPE_CHOICES = [(INCOME, "Income"), (EXPENSE, "Expense")]
    CASH, ONLINE = "cash", "online"
    METHOD_CHOICES = [(CASH, "Cash"), (ONLINE, "Online")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, to_field="telegram_id", db_column="telegram_id",
                                 on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    category = models.CharField(max_length=50)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Collection(models.Model):
    TO_GIVE, TO_RECEIVE = "to_give", "to_receive"
    TYPE_CHOICES = [(TO_GIVE, "To Give"), (TO_RECEIVE, "To Receive")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, to_field="telegram_id", db_column="telegram_id",
                                 on_delete=models.CASCADE, related_name="collections")
    person_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    due_date = models.DateTimeField(null=True, blank=True)
    is_settled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-due_date"]


class Reminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, to_field="telegram_id", db_column="telegram_id",
                                 on_delete=models.CASCADE, related_name="reminders")
    note_content = models.TextField()
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["remind_at"]
