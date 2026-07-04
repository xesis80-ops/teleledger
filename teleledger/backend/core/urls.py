from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet, CollectionViewSet, ReminderViewSet, DashboardView

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("collections", CollectionViewSet, basename="collection")
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]
