from pusher_push_notifications import PushNotifications
from app.core.config import settings

beams_client = PushNotifications(
    instance_id=settings.PUSHER_NOTIFICATION_INSTANCE_ID,
    secret_key=settings.PUSHER_NOTIFICATION_SECRET_KEY,
)