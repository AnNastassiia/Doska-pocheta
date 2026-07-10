from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AnonymousUser

from .models import Employer, ManagerProfile, Notification, Student


def _sidebar_account_context(user) -> dict[str, Any]:
    """Имя и роль в боковой панели (менеджер без is_staff не должен отображаться как студент)."""
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {
            "sidebar_display_name": "",
            "sidebar_role_label": "",
            "sidebar_show_manager_links": False,
        }

    display = (user.get_full_name() or "").strip() or (user.email or "").strip() or user.username

    if user.is_staff or user.is_superuser:
        return {
            "sidebar_display_name": display,
            "sidebar_role_label": "Менеджер / Админ",
            "sidebar_show_manager_links": True,
        }

    try:
        if user.manager_profile.is_active:
            return {
                "sidebar_display_name": display,
                "sidebar_role_label": "Менеджер",
                "sidebar_show_manager_links": True,
            }
    except ManagerProfile.DoesNotExist:
        pass

    try:
        user.employer
        return {
            "sidebar_display_name": display,
            "sidebar_role_label": "Работодатель",
            "sidebar_show_manager_links": False,
        }
    except Employer.DoesNotExist:
        pass

    try:
        user.student
        return {
            "sidebar_display_name": display,
            "sidebar_role_label": "Студент",
            "sidebar_show_manager_links": False,
        }
    except Student.DoesNotExist:
        pass

    return {
        "sidebar_display_name": display,
        "sidebar_role_label": "Пользователь",
        "sidebar_show_manager_links": False,
    }


def notifications_context(request) -> dict[str, Any]:
    """
    - notifications_unread_count: badge count в шапке
    - toast_notifications: список новых уведомлений для Toast (показываем 3)
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        base = {"notifications_unread_count": 0, "toast_notifications": []}
        base.update(_sidebar_account_context(user))
        return base

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

    out = {
        "notifications_unread_count": unread_count,
        "toast_notifications": toast_items,
    }
    out.update(_sidebar_account_context(user))
    return out

