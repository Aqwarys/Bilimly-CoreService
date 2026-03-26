from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class Tariff(models.Model):
    """Tariff model for subscription plans."""

    title = models.CharField(max_length=128)
    days_count = models.IntegerField()
    is_trial = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Tariff"
        verbose_name_plural = "Tariffs"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} ({self.days_count} days)"


class Subscription(models.Model):
    """User subscription model."""

    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ["-created_at"]

    def clean(self):
        """Validate that user doesn't already have an active subscription."""
        if Subscription.objects.filter(user=self.user).exists():
            # Check if this is a new instance or updating existing
            if not self.pk:
                raise ValidationError("User already has a subscription.")

    def save(self, *args, **kwargs):
        """Override save to automatically calculate deadline."""
        is_new = self.pk is None

        # For new subscriptions, calculate deadline before saving
        if is_new and self.tariff:
            # Set deadline based on tariff days_count
            # We'll use timezone.now() for created_at calculation since it's auto_now_add
            current_time = timezone.now()
            self.deadline = current_time + timezone.timedelta(
                days=self.tariff.days_count
            )

        # Run validation after deadline is set
        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return self.deadline > timezone.now()

    def __str__(self):
        return f"{self.user.username} - {self.tariff.title}"


def user_has_active_subscription(user):
    """
    Helper function to check if user has an active subscription.

    Args:
        user: User instance

    Returns:
        bool: True if user has active subscription, False otherwise
    """
    try:
        subscription = Subscription.objects.get(user=user)
        return subscription.is_active
    except Subscription.DoesNotExist:
        return False
