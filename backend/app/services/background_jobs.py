"""
Background Jobs
Scheduled tasks for notifications and cleanup
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class BackgroundJobs:
    """Manager for background jobs"""
    
    def __init__(self):
        self.running = False
        self.session_check_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start all background jobs"""
        if self.running:
            logger.warning("Background jobs already running")
            return
        
        self.running = True
        logger.info("Starting background jobs...")
        
        # Start session reminder check (every 5 minutes)
        self.session_check_task = asyncio.create_task(
            self._session_reminder_loop()
        )
        
        # Start cleanup job (every 24 hours)
        self.cleanup_task = asyncio.create_task(
            self._cleanup_loop()
        )
        
        logger.info("Background jobs started")
    
    async def stop(self):
        """Stop all background jobs"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping background jobs...")
        
        # Cancel tasks
        if self.session_check_task:
            self.session_check_task.cancel()
            try:
                await self.session_check_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Background jobs stopped")
    
    async def _session_reminder_loop(self):
        """Check for upcoming sessions every 5 minutes"""
        while self.running:
            try:
                await self._check_session_reminders()
                await asyncio.sleep(300)  # 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session reminder loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _cleanup_loop(self):
        """Clean up old notifications every 24 hours"""
        while self.running:
            try:
                await self._cleanup_old_notifications()
                await asyncio.sleep(86400)  # 24 hours
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _check_session_reminders(self):
        """Check for upcoming sessions and create reminders"""
        db = SessionLocal()
        try:
            service = NotificationService(db)
            count = service.check_upcoming_sessions()
            
            if count > 0:
                logger.info(f"Created {count} session reminders")
        except Exception as e:
            logger.error(f"Error checking session reminders: {e}")
        finally:
            db.close()
    
    async def _cleanup_old_notifications(self):
        """Delete old notifications"""
        db = SessionLocal()
        try:
            service = NotificationService(db)
            count = service.delete_old_notifications()
            
            if count > 0:
                logger.info(f"Deleted {count} old notifications")
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
        finally:
            db.close()


# Global instance
background_jobs = BackgroundJobs()
