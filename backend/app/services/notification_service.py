"""
Notification Service
Handles creation, retrieval, and management of user notifications
"""
from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.notification import Notification
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.user import User


class NotificationService:
    """Service for managing notifications"""
    
    # Notification types
    TYPE_PLAN_GENERATED = "plan_generated"
    TYPE_SESSION_REMINDER = "session_reminder"
    TYPE_SYSTEM_ALERT = "system_alert"
    
    # Constants
    REMINDER_MINUTES_BEFORE = 30
    RETENTION_DAYS = 30
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_plan_generated_notification(
        self,
        user_id: int,
        plan: StudyPlan
    ) -> Notification:
        """
        Create notification for plan generation
        
        Args:
            user_id: User ID
            plan: Generated study plan
            
        Returns:
            Created notification
        """
        # Calculate total hours from sessions
        total_hours = 0
        for session in plan.sessions:
            from datetime import datetime, date
            duration = (
                datetime.combine(date.today(), session.end_time) -
                datetime.combine(date.today(), session.start_time)
            ).total_seconds() / 3600
            total_hours += duration
        
        message = (
            f"Votre plan d'étude pour la semaine du "
            f"{plan.week_start.strftime('%d/%m/%Y')} a été généré avec succès. "
            f"Total: {total_hours:.1f} heures."
        )
        
        notification = Notification(
            user_id=user_id,
            notification_type=self.TYPE_PLAN_GENERATED,
            message=message,
            read=False
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def create_session_reminder(
        self,
        user_id: int,
        session: StudySession
    ) -> Optional[Notification]:
        """
        Create reminder for upcoming session
        
        Args:
            user_id: User ID
            session: Study session
            
        Returns:
            Created notification or None if duplicate
        """
        # Check for duplicate reminder
        existing = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.notification_type == self.TYPE_SESSION_REMINDER,
                Notification.message.contains(f"session #{session.id}")
            )
        ).first()
        
        if existing:
            return None  # Duplicate prevention
        
        # Create reminder message
        message = (
            f"Rappel: Session de {session.subject.name} "
            f"dans {self.REMINDER_MINUTES_BEFORE} minutes "
            f"({session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}). "
            f"Type: {session.task_type} [session #{session.id}]"
        )
        
        notification = Notification(
            user_id=user_id,
            notification_type=self.TYPE_SESSION_REMINDER,
            message=message,
            read=False
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get user notifications
        
        Args:
            user_id: User ID
            unread_only: Filter for unread notifications only
            limit: Maximum number of notifications
            
        Returns:
            List of notifications
        """
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return notifications
    
    def mark_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """
        Mark notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security)
            
        Returns:
            Updated notification or None if not found
        """
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if not notification:
            return None
        
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all user notifications as read
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications updated
        """
        count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        ).update({"read": True})
        
        self.db.commit()
        return count
    
    def delete_old_notifications(self) -> int:
        """
        Delete notifications older than retention period
        
        Returns:
            Number of notifications deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_DAYS)
        
        count = self.db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return count
    
    def check_upcoming_sessions(self) -> int:
        """
        Check for upcoming sessions and create reminders
        Background job to run every 5 minutes
        
        Returns:
            Number of reminders created
        """
        now = datetime.now()
        current_day = now.strftime('%A')  # Monday, Tuesday, etc.
        current_time = now.time()
        
        # Calculate reminder time window
        reminder_time = (now + timedelta(minutes=self.REMINDER_MINUTES_BEFORE)).time()
        
        # Find sessions starting in the next 5-35 minutes
        # (30 min before ± 5 min window)
        min_time = (now + timedelta(minutes=self.REMINDER_MINUTES_BEFORE - 5)).time()
        max_time = (now + timedelta(minutes=self.REMINDER_MINUTES_BEFORE + 5)).time()
        
        # Query sessions for today that start in the reminder window
        sessions = self.db.query(StudySession).join(
            StudyPlan
        ).filter(
            and_(
                StudySession.day == current_day,
                StudySession.start_time >= min_time,
                StudySession.start_time <= max_time,
                StudyPlan.status == 'generated'  # Only active plans
            )
        ).all()
        
        reminders_created = 0
        
        for session in sessions:
            # Create reminder
            reminder = self.create_session_reminder(
                session.study_plan.user_id,
                session
            )
            
            if reminder:
                reminders_created += 1
        
        return reminders_created
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications
        
        Args:
            user_id: User ID
            
        Returns:
            Number of unread notifications
        """
        count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        ).count()
        
        return count


# Import timezone for datetime operations
from datetime import timezone
