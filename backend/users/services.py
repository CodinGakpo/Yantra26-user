import math
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import TrustScoreLog


def calculate_deactivation_days(days_since_last_violation, b_min=1, b_max=30, d=30):
    """
    Smoothed inverse penalty window:
    ban_days = b_min + (b_max - b_min) * e^(-(days_since_last_violation / d))
    """
    if days_since_last_violation is None:
        days_since_last_violation = 0

    days_since_last_violation = max(0, days_since_last_violation)

    raw_days = b_min + (b_max - b_min) * math.exp(-(days_since_last_violation / d))
    ban_days = int(math.floor(raw_days))
    return max(b_min, min(b_max, ban_days))


def format_activation_time(dt):
    if not dt:
        return None
    local_dt = timezone.localtime(dt)
    return local_dt.strftime("%H:%M, %d %B %Y")


def raise_if_user_deactivated(user):
    if not user.deactivated_until:
        return
    if user.deactivated_until <= timezone.now():
        return

    raise serializers.ValidationError(
        {
            "code": "ACCOUNT_DEACTIVATED",
            "message": "Account is temporarily deactivated.",
            "deactivated_until": user.deactivated_until,
            "activation_time": format_activation_time(user.deactivated_until),
        }
    )


@transaction.atomic
def apply_trust_score_change(
    *,
    user,
    delta,
    reason,
    report=None,
    appeal_status=TrustScoreLog.APPEAL_NOT_APPEALED,
    admin_id=None,
):
    """
    Single path for trust score updates with immutable audit logs.
    Negative deltas are blocked while user is deactivated.
    """
    if delta < 0 and user.is_temporarily_deactivated:
        return user.trust_score

    next_score = max(0, min(110, user.trust_score + delta))
    applied_delta = next_score - user.trust_score

    if applied_delta == 0:
        return user.trust_score

    user.trust_score = next_score
    user.save(update_fields=["trust_score"])

    TrustScoreLog.objects.create(
        user=user,
        delta=applied_delta,
        reason=reason,
        report=report,
        appeal_status=appeal_status,
        admin_id=admin_id,
    )

    return user.trust_score


def deactivate_user_until(user, *, days):
    until = timezone.now() + timedelta(days=days)
    user.deactivated_until = until
    user.save(update_fields=["deactivated_until"])
    return until
