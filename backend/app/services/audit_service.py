"""
Audit Service for tracking administrative changes and entity history

This service provides methods for:
- Logging create, update, delete operations
- Retrieving entity history with pagination
- Exporting audit logs

Requirements: 16.1-16.7
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import json
import csv
from io import StringIO

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Service for audit logging and change history tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_create(
        self, 
        entity_type: str, 
        entity_id: int, 
        data: Dict[str, Any], 
        user_id: int,
        description: Optional[str] = None
    ) -> AuditLog:
        """
        Log entity creation operation.
        
        Requirements: 16.1
        
        Args:
            entity_type: Type of entity (e.g., 'university', 'course', 'program')
            entity_id: ID of the created entity
            data: Entity data after creation
            user_id: ID of the user who performed the operation
            description: Optional human-readable description
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            operation='create',
            before_value=None,
            after_value=self._serialize_data(data),
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            description=description or f"Created {entity_type} with ID {entity_id}"
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    async def log_update(
        self, 
        entity_type: str, 
        entity_id: int, 
        before: Dict[str, Any], 
        after: Dict[str, Any], 
        user_id: int,
        description: Optional[str] = None
    ) -> AuditLog:
        """
        Log entity update operation with before/after values.
        
        Requirements: 16.1, 16.5
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the updated entity
            before: Entity state before the update
            after: Entity state after the update
            user_id: ID of the user who performed the operation
            description: Optional human-readable description
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            operation='update',
            before_value=self._serialize_data(before),
            after_value=self._serialize_data(after),
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            description=description or f"Updated {entity_type} with ID {entity_id}"
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    async def log_delete(
        self, 
        entity_type: str, 
        entity_id: int, 
        data: Dict[str, Any], 
        user_id: int,
        description: Optional[str] = None
    ) -> AuditLog:
        """
        Log entity deletion operation.
        
        Requirements: 16.1, 16.7
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the deleted entity
            data: Entity state before deletion
            user_id: ID of the user who performed the operation
            description: Optional human-readable description
            
        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            operation='delete',
            before_value=self._serialize_data(data),
            after_value=None,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            description=description or f"Deleted {entity_type} with ID {entity_id}"
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        return audit_log
    
    async def get_entity_history(
        self, 
        entity_type: str, 
        entity_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Get change history for a specific entity with pagination.
        
        Requirements: 16.2, 16.4
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            page: Page number (1-indexed)
            page_size: Number of records per page
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = self.db.query(AuditLog).filter(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(desc(AuditLog.timestamp))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        audit_logs = query.offset(offset).limit(page_size).all()
        
        return audit_logs, total_count
    
    async def get_audit_logs(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Get filtered and paginated audit logs.
        
        Requirements: 16.3
        
        Args:
            filters: Optional filters including:
                - entity_type: Filter by entity type
                - entity_id: Filter by entity ID
                - operation: Filter by operation type ('create', 'update', 'delete')
                - user_id: Filter by user who performed the operation
                - start_date: Filter by timestamp start date
                - end_date: Filter by timestamp end date
            page: Page number (1-indexed)
            page_size: Number of records per page
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        query = self.db.query(AuditLog)
        
        # Apply filters
        if filters:
            if 'entity_type' in filters and filters['entity_type']:
                query = query.filter(AuditLog.entity_type == filters['entity_type'])
            
            if 'entity_id' in filters and filters['entity_id']:
                query = query.filter(AuditLog.entity_id == filters['entity_id'])
            
            if 'operation' in filters and filters['operation']:
                query = query.filter(AuditLog.operation == filters['operation'])
            
            if 'user_id' in filters and filters['user_id']:
                query = query.filter(AuditLog.user_id == filters['user_id'])
            
            if 'start_date' in filters and filters['start_date']:
                query = query.filter(AuditLog.timestamp >= filters['start_date'])
            
            if 'end_date' in filters and filters['end_date']:
                query = query.filter(AuditLog.timestamp <= filters['end_date'])
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(desc(AuditLog.timestamp))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        audit_logs = query.offset(offset).limit(page_size).all()
        
        return audit_logs, total_count
    
    async def export_audit_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        format: str = 'csv'
    ) -> str:
        """
        Export audit logs to CSV or JSON format.
        
        Requirements: 16.3
        
        Args:
            filters: Optional filters (same as get_audit_logs)
            format: Export format ('csv' or 'json')
            
        Returns:
            String content of the exported data
            
        Raises:
            ValueError: If format is not supported
        """
        # Get all audit logs matching filters (no pagination for export)
        query = self.db.query(AuditLog)
        
        # Apply filters
        if filters:
            if 'entity_type' in filters and filters['entity_type']:
                query = query.filter(AuditLog.entity_type == filters['entity_type'])
            
            if 'entity_id' in filters and filters['entity_id']:
                query = query.filter(AuditLog.entity_id == filters['entity_id'])
            
            if 'operation' in filters and filters['operation']:
                query = query.filter(AuditLog.operation == filters['operation'])
            
            if 'user_id' in filters and filters['user_id']:
                query = query.filter(AuditLog.user_id == filters['user_id'])
            
            if 'start_date' in filters and filters['start_date']:
                query = query.filter(AuditLog.timestamp >= filters['start_date'])
            
            if 'end_date' in filters and filters['end_date']:
                query = query.filter(AuditLog.timestamp <= filters['end_date'])
        
        # Order by timestamp descending
        query = query.order_by(desc(AuditLog.timestamp))
        
        audit_logs = query.all()
        
        if format == 'csv':
            return self._export_to_csv(audit_logs)
        elif format == 'json':
            return self._export_to_json(audit_logs)
        else:
            raise ValueError(f"Unsupported export format: {format}. Use 'csv' or 'json'")
    
    def _export_to_csv(self, audit_logs: List[AuditLog]) -> str:
        """
        Export audit logs to CSV format.
        
        Args:
            audit_logs: List of AuditLog instances
            
        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID',
            'Timestamp',
            'Entity Type',
            'Entity ID',
            'Operation',
            'User ID',
            'Username',
            'Description',
            'Before Value',
            'After Value'
        ])
        
        # Write data rows
        for log in audit_logs:
            username = log.user.name if log.user else 'Unknown'
            
            writer.writerow([
                log.id,
                log.timestamp.isoformat(),
                log.entity_type,
                log.entity_id,
                log.operation,
                log.user_id,
                username,
                log.description or '',
                json.dumps(log.before_value) if log.before_value else '',
                json.dumps(log.after_value) if log.after_value else ''
            ])
        
        return output.getvalue()
    
    def _export_to_json(self, audit_logs: List[AuditLog]) -> str:
        """
        Export audit logs to JSON format.
        
        Args:
            audit_logs: List of AuditLog instances
            
        Returns:
            JSON string
        """
        data = []
        
        for log in audit_logs:
            username = log.user.name if log.user else 'Unknown'
            
            data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'operation': log.operation,
                'user_id': log.user_id,
                'username': username,
                'description': log.description,
                'before_value': log.before_value,
                'after_value': log.after_value
            })
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize entity data for JSON storage.
        Handles datetime and other non-serializable objects.
        
        Args:
            data: Entity data dictionary
            
        Returns:
            Serialized dictionary safe for JSON storage
        """
        serialized = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif hasattr(value, '__dict__'):
                # Skip complex objects that aren't primitives
                serialized[key] = str(value)
            else:
                serialized[key] = value
        
        return serialized
    
    async def get_recent_activities(
        self,
        limit: int = 20,
        entity_types: Optional[List[str]] = None
    ) -> List[AuditLog]:
        """
        Get recent audit log activities for dashboard display.
        
        Requirements: 10.5
        
        Args:
            limit: Maximum number of activities to return
            entity_types: Optional list of entity types to filter by
            
        Returns:
            List of recent AuditLog instances
        """
        query = self.db.query(AuditLog)
        
        if entity_types:
            query = query.filter(AuditLog.entity_type.in_(entity_types))
        
        audit_logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
        
        return audit_logs
    
    async def get_user_activity_count(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Get count of activities performed by a specific user.
        
        Args:
            user_id: ID of the user
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Count of audit log entries
        """
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.count()
    
    async def get_entity_type_statistics(self) -> Dict[str, int]:
        """
        Get statistics of operations by entity type.
        
        Returns:
            Dictionary mapping entity types to operation counts
        """
        from sqlalchemy import func
        
        results = self.db.query(
            AuditLog.entity_type,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.entity_type).all()
        
        return {entity_type: count for entity_type, count in results}
