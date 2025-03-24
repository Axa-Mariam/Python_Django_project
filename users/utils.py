from .models import Notification, Category, Product
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.base import ContentFile
import random
import os
from django.conf import settings 

def create_notification(user, title, message, notification_type='info'):
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        created_at=timezone.now()
    )
    return notification