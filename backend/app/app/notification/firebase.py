from pyfcm import FCMNotification
from app.core.config import settings

push_service = FCMNotification(api_key=settings.FIREBASE_API_KEY)
