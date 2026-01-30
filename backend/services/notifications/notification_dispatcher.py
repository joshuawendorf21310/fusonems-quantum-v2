import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.notifications import InAppNotification, NotificationPreference, NotificationType, NotificationSeverity
from models.user import User
from services.notifications.notification_service import NotificationService
from services.email.email_transport_service import send_notification_email
from services.communications.comms_router import CommsThread, CommsMessage
from core.config import settings
from utils.logger import logger

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    @staticmethod
    def should_deliver(
        severity: NotificationSeverity,
        notification_type: NotificationType,
        user_pref: Optional[NotificationPreference],
    ) -> bool:
        if not user_pref:
            return True
        
        if severity == NotificationSeverity.CRITICAL and user_pref.critical_override:
            return True
        
        return True

    @staticmethod
    def get_delivery_channels(
        user_pref: Optional[NotificationPreference],
        severity: NotificationSeverity,
    ) -> List[str]:
        if not user_pref:
            return ["in_app", "email"]
        
        if severity == NotificationSeverity.CRITICAL and user_pref.critical_override:
            return ["in_app", "email", "sms"]
        
        channels = []
        if user_pref.in_app_enabled:
            channels.append("in_app")
        if user_pref.email_enabled:
            channels.append("email")
        if user_pref.sms_enabled:
            channels.append("sms")
        
        return channels if channels else ["in_app"]

    @staticmethod
    def dispatch_notification(
        db: Session,
        user_id: int,
        org_id: int,
        notification_type: NotificationType,
        title: str,
        body: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        linked_resource_type: Optional[str] = None,
        linked_resource_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        training_mode: bool = False,
        email_subject: Optional[str] = None,
        email_html_template: Optional[str] = None,
    ) -> InAppNotification:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found for notification dispatch")
            return None

        user_pref = NotificationService.get_or_create_preference(db, user_id, org_id)

        if not NotificationDispatcher.should_deliver(severity, notification_type, user_pref):
            logger.debug(f"Skipping notification {notification_type} for user {user_id} (preferences)")
            return None

        notif = NotificationService.send_notification(
            db,
            user_id=user_id,
            org_id=org_id,
            notification_type=notification_type,
            title=title,
            body=body,
            severity=severity,
            linked_resource_type=linked_resource_type,
            linked_resource_id=linked_resource_id,
            metadata=metadata,
            training_mode=training_mode,
        )

        channels = NotificationDispatcher.get_delivery_channels(user_pref, severity)

        logger.info(f"Notification {notif.id} created for user {user_id}, dispatching to: {channels}")

        NotificationDispatcher._dispatch_to_channels(
            db=db,
            notification=notif,
            user=user,
            channels=channels,
            email_subject=email_subject or title,
            email_html_template=email_html_template or f"<p>{body}</p>",
            training_mode=training_mode,
        )

        return notif

    @staticmethod
    def _dispatch_to_channels(
        db: Session,
        notification: InAppNotification,
        user: User,
        channels: List[str],
        email_subject: str,
        email_html_template: str,
        training_mode: bool = False,
    ) -> None:
        for channel in channels:
            try:
                if channel == "in_app":
                    NotificationDispatcher._deliver_in_app(notification)
                elif channel == "email":
                    NotificationDispatcher._deliver_email(
                        user=user,
                        title=email_subject,
                        html_body=email_html_template,
                        training_mode=training_mode,
                    )
                elif channel == "sms":
                    NotificationDispatcher._deliver_sms(
                        db=db,
                        user=user,
                        body=notification.body,
                        training_mode=training_mode,
                    )
            except Exception as e:
                logger.error(f"Failed to deliver notification {notification.id} via {channel}: {e}")

    @staticmethod
    def _deliver_in_app(notification: InAppNotification) -> None:
        logger.debug(f"In-app notification {notification.id} created (already persisted)")

    @staticmethod
    def _deliver_email(
        user: User,
        title: str,
        html_body: str,
        training_mode: bool = False,
    ) -> None:
        if training_mode:
            logger.info(f"[Training] Email notification to {user.email}: {title}")
            return

        try:
            send_notification_email(
                to=user.email,
                subject=title,
                html_body=html_body,
                reply_to=getattr(settings, "SUPPORT_EMAIL", None) or getattr(settings, "FOUNDER_EMAIL", None) or settings.SMTP_USERNAME,
            )
            logger.info(f"Email notification sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email notification to {user.email}: {e}")

    @staticmethod
    def _deliver_sms(
        db: Session,
        user: User,
        body: str,
        training_mode: bool = False,
    ) -> None:
        if training_mode or not settings.TELNYX_API_KEY:
            logger.info(f"[Training/Disabled] SMS notification to user {user.id}: {body}")
            return

        if not user.phone_number:
            logger.warning(f"User {user.id} has no phone number, skipping SMS")
            return

        try:
            thread = db.query(CommsThread).filter(
                CommsThread.org_id == user.org_id,
                CommsThread.user_id == user.id,
            ).first()

            if not thread:
                logger.warning(f"No CommsThread found for user {user.id}, creating SMS via thread")
                return

            message = CommsMessage(
                thread_id=thread.id,
                org_id=user.org_id,
                direction="outbound",
                channel="sms",
                body=body,
                sent_at=datetime.utcnow(),
            )
            db.add(message)
            db.commit()
            logger.info(f"SMS notification sent to user {user.id}")
        except Exception as e:
            logger.error(f"Failed to send SMS notification to user {user.id}: {e}")
