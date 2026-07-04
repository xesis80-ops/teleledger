from decimal import Decimal

from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Transaction, Collection, Reminder
from .serializers import TransactionSerializer, CollectionSerializer, ReminderSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(profile=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user)


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(profile=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user)

    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        """Marks a collection as settled and logs the matching ledger transaction."""
        collection = self.get_object()
        if collection.is_settled:
            return Response({"detail": "Already settled."}, status=status.HTTP_400_BAD_REQUEST)

        collection.is_settled = True
        collection.save(update_fields=["is_settled"])

        # to_receive settling => income; to_give settling => expense
        tx_type = Transaction.INCOME if collection.type == Collection.TO_RECEIVE else Transaction.EXPENSE
        Transaction.objects.create(
            profile=request.user,
            amount=collection.amount,
            type=tx_type,
            method=Transaction.CASH,
            category="Collections",
            notes=f"Settled with {collection.person_name}",
        )
        return Response(CollectionSerializer(collection).data)


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer

    def get_queryset(self):
        return Reminder.objects.filter(profile=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user)


class DashboardView(APIView):
    """Returns the three live balance metrics required by the PRD."""

    def get(self, request):
        qs = Transaction.objects.filter(profile=request.user)

        def net(method=None):
            filtered = qs.filter(method=method) if method else qs
            income = filtered.filter(type=Transaction.INCOME).aggregate(s=Sum("amount"))["s"] or Decimal("0")
            expense = filtered.filter(type=Transaction.EXPENSE).aggregate(s=Sum("amount"))["s"] or Decimal("0")
            return income - expense

        cash_balance = net(Transaction.CASH)
        online_balance = net(Transaction.ONLINE)

        return Response({
            "cash_balance": cash_balance,
            "online_balance": online_balance,
            "net_balance": cash_balance + online_balance,
            "recent_transactions": TransactionSerializer(qs[:10], many=True).data,
        })
