from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from shared.models import ActivityLog
from django.utils.timezone import now

def get_user_from_instance(instance):
    # Try to get `created_by` or `updated_by`
    return getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)

@receiver(post_save)
def log_create_or_update(sender, instance, created, **kwargs):
    if sender.__name__ == "ActivityLog":
        return  # Prevent self-logging

    user = get_user_from_instance(instance)
    action = "created" if created else "updated"

    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        description=f"{user} {action} {sender.__name__} ({instance})",
    )

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender.__name__ == "ActivityLog":
        return

    user = get_user_from_instance(instance)

    ActivityLog.objects.create(
        user=user,
        action="deleted",
        model_name=sender.__name__,
        object_id=str(instance.pk),
        description=f"{user} deleted {sender.__name__} ({instance})",
    )
