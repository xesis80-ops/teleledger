from rest_framework import serializers
from .models import Transaction, Collection, Reminder


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "amount", "type", "method", "category", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "person_name", "amount", "type", "due_date", "is_settled"]
        read_only_fields = ["id"]


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ["id", "note_content", "remind_at", "is_sent"]
        read_only_fields = ["id", "is_sent"]
