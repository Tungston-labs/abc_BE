import secrets

from django.conf import settings

from rest_framework.permissions import (
    BasePermission
)


class IsSignalServer(
    BasePermission
):

    message = (
        "Invalid signal server credentials."
    )

    def has_permission(
        self,
        request,
        view
    ):

        provided_key = request.headers.get(
            "X-Signal-API-Key"
        )

        expected_key = getattr(
            settings,
            "SIGNAL_SYNC_API_KEY",
            None
        )

        if not provided_key:
            return False

        if not expected_key:
            return False

        return secrets.compare_digest(
            provided_key,
            expected_key
        )