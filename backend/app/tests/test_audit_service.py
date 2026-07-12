"""
Unit tests for AuditService

Tests cover:
- Logging create, update, delete operations
- Entity history retrieval with pagination
- Audit log filtering and querying
- Export functionality (CSV and JSON)
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import json

from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.mark.asyncio
class TestAuditService:
    """Test suite for AuditService"""
    
    async def test_log_create(self, db_session: Session, test_user: User):
        """Test logging a create operation"""
        service = AuditService(db_session)
        
        entity_data = {
            "name": "Test University",
            "country": "Germany",
            "city": "Berlin"
        }
        
        audit_log = await service.log_create(
            entity_type="university",
            entity_id=1,
            data=entity_data,
            user_id=test_user.id,
            description="Created test university"
        )
        
        assert audit_log.id is not None
        assert audit_log.entity_type == "university"
        assert audit_log.entity_id == 1
        assert audit_log.operation == "create"
        assert audit_log.before_value is None
        assert audit_log.after_value == entity_data
        assert audit_log.user_id == test_user.id
        assert audit_log.description == "Created test university"
        assert audit_log.timestamp is not None
    
    async def test_log_update(self, db_session: Session, test_user: User):
        """Test logging an update operation with before/after values"""
        service = AuditService(db_session)
        
        before_data = {
            "name": "Old Name",
            "country": "Germany"
        }
        
        after_data = {
            "name": "New Name",
            "country": "Germany"
        }
        
        audit_log = await service.log_update(
            entity_type="university",
            entity_id=1,
            before=before_data,
            after=after_data,
            user_id=test_user.id,
            description="Updated university name"
        )
        
        assert audit_log.operation == "update"
        assert audit_log.before_value == before_data
        assert audit_log.after_value == after_data
        assert audit_log.description == "Updated university name"
    
    async def test_log_delete(self, db_session: Session, test_user: User):
        """Test logging a delete operation"""
        service = AuditService(db_session)
        
        entity_data = {
            "name": "Test University",
            "country": "Germany"
        }
        
        audit_log = await service.log_delete(
            entity_type="university",
            entity_id=1,
            data=entity_data,
            user_id=test_user.id,
            description="Deleted test university"
        )
        
        assert audit_log.operation == "delete"
        assert audit_log.before_value == entity_data
        assert audit_log.after_value is None
        assert audit_log.description == "Deleted test university"
    
    async def test_get_entity_history(self, db_session: Session, test_user: User):
        """Test retrieving entity history with pagination"""
        service = AuditService(db_session)
        
        # Create multiple audit logs for the same entity
        for i in range(5):
            await service.log_update(
                entity_type="course",
                entity_id=100,
                before={"version": i},
                after={"version": i + 1},
                user_id=test_user.id
            )
        
        # Get first page
        logs, total = await service.get_entity_history(
            entity_type="course",
            entity_id=100,
            page=1,
            page_size=3
        )
        
        assert len(logs) == 3
        assert total == 5
        # Logs should be in descending order (most recent first)
        assert logs[0].after_value["version"] > logs[1].after_value["version"]
        
        # Get second page
        logs_page2, _ = await service.get_entity_history(
            entity_type="course",
            entity_id=100,
            page=2,
            page_size=3
        )
        
        assert len(logs_page2) == 2
    
    async def test_get_entity_history_empty(self, db_session: Session):
        """Test retrieving history for entity with no logs"""
        service = AuditService(db_session)
        
        logs, total = await service.get_entity_history(
            entity_type="course",
            entity_id=999,
            page=1,
            page_size=10
        )
        
        assert len(logs) == 0
        assert total == 0
    
    async def test_get_audit_logs_no_filters(self, db_session: Session, test_user: User):
        """Test retrieving all audit logs without filters"""
        service = AuditService(db_session)
        
        # Create logs for different entities
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        logs, total = await service.get_audit_logs(
            page=1,
            page_size=10
        )
        
        assert total == 2
        assert len(logs) == 2
    
    async def test_get_audit_logs_filter_by_entity_type(self, db_session: Session, test_user: User):
        """Test filtering audit logs by entity type"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        logs, total = await service.get_audit_logs(
            filters={"entity_type": "university"},
            page=1,
            page_size=10
        )
        
        assert total == 1
        assert logs[0].entity_type == "university"
    
    async def test_get_audit_logs_filter_by_operation(self, db_session: Session, test_user: User):
        """Test filtering audit logs by operation type"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_update(
            entity_type="university",
            entity_id=1,
            before={"name": "Uni 1"},
            after={"name": "Uni 1 Updated"},
            user_id=test_user.id
        )
        
        await service.log_delete(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1 Updated"},
            user_id=test_user.id
        )
        
        logs, total = await service.get_audit_logs(
            filters={"operation": "update"},
            page=1,
            page_size=10
        )
        
        assert total == 1
        assert logs[0].operation == "update"
    
    async def test_get_audit_logs_filter_by_date_range(self, db_session: Session, test_user: User):
        """Test filtering audit logs by date range"""
        service = AuditService(db_session)
        
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        # Filter with date range that includes the log
        logs, total = await service.get_audit_logs(
            filters={
                "start_date": yesterday,
                "end_date": tomorrow
            },
            page=1,
            page_size=10
        )
        
        assert total == 1
        
        # Filter with date range that excludes the log
        logs_excluded, total_excluded = await service.get_audit_logs(
            filters={
                "start_date": tomorrow,
                "end_date": tomorrow + timedelta(days=1)
            },
            page=1,
            page_size=10
        )
        
        assert total_excluded == 0
    
    async def test_export_to_csv(self, db_session: Session, test_user: User):
        """Test exporting audit logs to CSV format"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Test University"},
            user_id=test_user.id,
            description="Created university"
        )
        
        csv_output = await service.export_audit_logs(format='csv')
        
        assert csv_output is not None
        assert "ID,Timestamp,Entity Type,Entity ID,Operation" in csv_output
        assert "university" in csv_output
        assert "create" in csv_output
        assert "Created university" in csv_output
    
    async def test_export_to_json(self, db_session: Session, test_user: User):
        """Test exporting audit logs to JSON format"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Test Course", "ects": 5},
            user_id=test_user.id,
            description="Created course"
        )
        
        json_output = await service.export_audit_logs(format='json')
        
        assert json_output is not None
        data = json.loads(json_output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["entity_type"] == "course"
        assert data[0]["operation"] == "create"
        assert data[0]["username"] == test_user.name
    
    async def test_export_unsupported_format(self, db_session: Session):
        """Test exporting with unsupported format raises error"""
        service = AuditService(db_session)
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            await service.export_audit_logs(format='xml')
    
    async def test_export_with_filters(self, db_session: Session, test_user: User):
        """Test exporting audit logs with filters applied"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        json_output = await service.export_audit_logs(
            filters={"entity_type": "university"},
            format='json'
        )
        
        data = json.loads(json_output)
        assert len(data) == 1
        assert data[0]["entity_type"] == "university"
    
    async def test_get_recent_activities(self, db_session: Session, test_user: User):
        """Test retrieving recent activities for dashboard"""
        service = AuditService(db_session)
        
        # Create multiple logs
        for i in range(5):
            await service.log_create(
                entity_type="course",
                entity_id=i,
                data={"name": f"Course {i}"},
                user_id=test_user.id
            )
        
        activities = await service.get_recent_activities(limit=3)
        
        assert len(activities) == 3
        # Should be in descending order (most recent first)
        assert activities[0].entity_id > activities[1].entity_id
    
    async def test_get_recent_activities_with_entity_filter(self, db_session: Session, test_user: User):
        """Test retrieving recent activities filtered by entity types"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        activities = await service.get_recent_activities(
            limit=10,
            entity_types=["university"]
        )
        
        assert len(activities) == 1
        assert activities[0].entity_type == "university"
    
    async def test_get_user_activity_count(self, db_session: Session, test_user: User):
        """Test getting activity count for a specific user"""
        service = AuditService(db_session)
        
        # Create logs for test user
        for i in range(3):
            await service.log_create(
                entity_type="course",
                entity_id=i,
                data={"name": f"Course {i}"},
                user_id=test_user.id
            )
        
        count = await service.get_user_activity_count(user_id=test_user.id)
        
        assert count == 3
    
    async def test_get_user_activity_count_with_date_filter(self, db_session: Session, test_user: User):
        """Test getting activity count with date filters"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        count = await service.get_user_activity_count(
            user_id=test_user.id,
            start_date=yesterday,
            end_date=tomorrow
        )
        
        assert count == 1
    
    async def test_get_entity_type_statistics(self, db_session: Session, test_user: User):
        """Test getting statistics grouped by entity type"""
        service = AuditService(db_session)
        
        await service.log_create(
            entity_type="university",
            entity_id=1,
            data={"name": "Uni 1"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="university",
            entity_id=2,
            data={"name": "Uni 2"},
            user_id=test_user.id
        )
        
        await service.log_create(
            entity_type="course",
            entity_id=1,
            data={"name": "Course 1"},
            user_id=test_user.id
        )
        
        stats = await service.get_entity_type_statistics()
        
        assert stats["university"] == 2
        assert stats["course"] == 1
    
    async def test_serialize_data_with_datetime(self, db_session: Session):
        """Test data serialization handles datetime objects"""
        service = AuditService(db_session)
        
        now = datetime.now(timezone.utc)
        data = {
            "name": "Test",
            "created_at": now,
            "count": 42
        }
        
        serialized = service._serialize_data(data)
        
        assert serialized["name"] == "Test"
        assert isinstance(serialized["created_at"], str)
        assert serialized["count"] == 42
