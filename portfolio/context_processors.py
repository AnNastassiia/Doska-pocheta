from __future__ import annotations

from typing import Any

from .models import Notification


def notifications_context(request) -> dict[str, Any]:
    """
    - notifications_unread_count: badge count в шапке
    - toast_notifications: список новых уведомлений для Toast (показываем 3)
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notifications_unread_count": 0, "toast_notifications": []}

    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    toast_qs = (
        Notification.objects.filter(user=user, is_read=False, is_seen=False)
        .order_by("-created_at")[:3]
    )

    toast_items = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "level": n.level,
            "url": n.url,
        }
        for n in toast_qs
    ]

    # Чтобы Toast не всплывал повторно на каждой странице
    if toast_items:
        Notification.objects.filter(id__in=[item["id"] for item in toast_items]).update(is_seen=True)

    return {
        "notifications_unread_count": unread_count,
        "toast_notifications": toast_items,
    }

