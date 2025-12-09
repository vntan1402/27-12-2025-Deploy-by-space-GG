"""
Crew Audit Log Repository
Database operations for audit logs
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import re


class CrewAuditLogRepository:
    """Repository for crew audit log operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.crew_audit_logs
    
    @staticmethod
    def _add_timezone_to_log(log: dict) -> dict:
        """Add UTC timezone to datetime fields for proper serialization"""
        if log:
            # Add timezone to performed_at
            if 'performed_at' in log and isinstance(log['performed_at'], datetime):
                if log['performed_at'].tzinfo is None:
                    log['performed_at'] = log['performed_at'].replace(tzinfo=timezone.utc)
            
            # Add timezone to created_at
            if 'created_at' in log and isinstance(log['created_at'], datetime):
                if log['created_at'].tzinfo is None:
                    log['created_at'] = log['created_at'].replace(tzinfo=timezone.utc)
            
            # Add timezone to expires_at
            if 'expires_at' in log and isinstance(log['expires_at'], datetime):
                if log['expires_at'].tzinfo is None:
                    log['expires_at'] = log['expires_at'].replace(tzinfo=timezone.utc)
        
        return log
    
    async def create_log(self, log_data: dict) -> dict:
        """
        Create new audit log entry
        
        Args:
            log_data: Log data dictionary
            
        Returns:
            Created log with ID
        """
        # Add timestamps with timezone
        now = datetime.now(timezone.utc)
        log_data['created_at'] = now
        
        # Set expiration date (1 year from now)
        log_data['expires_at'] = now + timedelta(days=365)
        
        # Insert into database
        result = await self.collection.insert_one(log_data)
        
        # Fetch and return created log
        created_log = await self.collection.find_one(
            {'_id': result.inserted_id},
            {'_id': 0}
        )
        
        return self._add_timezone_to_log(created_log)
    
    async def get_logs(
        self,
        company_id: str,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        performed_by: Optional[str] = None,
        ship_name: Optional[str] = None,
        entity_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[dict], int]:
        """
        Get filtered audit logs with pagination
        
        Supports filtering by entity type (crew, certificate, ship, company, user, document)
        If company_id is None, returns logs from all companies (for super admins)
        
        Returns:
            Tuple of (logs list, total count)
        """
        # Build query
        query = {}
        
        # Company filter (None = all companies for super admins)
        if company_id is not None:
            query['company_id'] = company_id
        
        # Entity type filter
        if entity_type:
            query['entity_type'] = entity_type
        
        # Date range filter
        if start_date or end_date:
            query['performed_at'] = {}
            if start_date:
                query['performed_at']['$gte'] = start_date
            if end_date:
                query['performed_at']['$lte'] = end_date
        
        # Action filter
        if action and action != 'all':
            query['action'] = action
        
        # User filter
        if performed_by and performed_by != 'all':
            query['performed_by'] = performed_by
        
        # Ship filter
        if ship_name and ship_name != 'all':
            query['ship_name'] = ship_name
        
        # Entity filter (specific crew)
        if entity_id:
            query['entity_id'] = entity_id
        
        # Search filter (crew name - case insensitive)
        if search:
            query['entity_name'] = {'$regex': re.escape(search), '$options': 'i'}
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get paginated logs (sorted by performed_at descending)
        cursor = self.collection.find(query, {'_id': 0}).sort('performed_at', -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Add timezone to all logs
        logs = [self._add_timezone_to_log(log) for log in logs]
        
        return logs, total
    
    async def get_log_by_id(self, log_id: str, company_id: Optional[str]) -> Optional[dict]:
        """
        Get single log by ID
        
        Args:
            log_id: Log ID
            company_id: Company ID for security check (None = all companies for super admins)
            
        Returns:
            Log dict or None
        """
        query = {'id': log_id}
        if company_id is not None:
            query['company_id'] = company_id
            
        log = await self.collection.find_one(query, {'_id': 0})
        return self._add_timezone_to_log(log)
    
    async def get_logs_by_crew(
        self,
        crew_id: str,
        company_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get all logs for a specific crew member
        
        Args:
            crew_id: Crew ID
            company_id: Company ID
            limit: Max logs to return
            
        Returns:
            List of logs
        """
        cursor = self.collection.find(
            {'entity_id': crew_id, 'company_id': company_id},
            {'_id': 0}
        ).sort('performed_at', -1).limit(limit)
        
        logs = await cursor.to_list(length=limit)
        return [self._add_timezone_to_log(log) for log in logs]
    
    async def get_logs_by_user(
        self,
        username: str,
        company_id: str,
        limit: int = 100
    ) -> List[dict]:
        """
        Get all logs performed by a specific user
        
        Args:
            username: Username
            company_id: Company ID
            limit: Max logs to return
            
        Returns:
            List of logs
        """
        cursor = self.collection.find(
            {'performed_by': username, 'company_id': company_id},
            {'_id': 0}
        ).sort('performed_at', -1).limit(limit)
        
        logs = await cursor.to_list(length=limit)
        return [self._add_timezone_to_log(log) for log in logs]
    
    async def delete_expired_logs(self) -> int:
        """
        Delete logs older than 1 year (manual cleanup)
        TTL index should handle this automatically, but this is for manual trigger
        
        Returns:
            Number of deleted logs
        """
        result = await self.collection.delete_many({
            'expires_at': {'$lt': datetime.utcnow()}
        })
        return result.deleted_count
    
    async def get_unique_users(self, company_id: str) -> List[dict]:
        """
        Get unique users who performed actions
        
        Args:
            company_id: Company ID
            
        Returns:
            List of unique users with {username, name}
        """
        pipeline = [
            {'$match': {'company_id': company_id}},
            {'$group': {
                '_id': '$performed_by',
                'name': {'$first': '$performed_by_name'}
            }},
            {'$project': {
                '_id': 0,
                'username': '$_id',
                'name': '$name'
            }},
            {'$sort': {'name': 1}}
        ]
        
        users = await self.collection.aggregate(pipeline).to_list(None)
        return users
    
    async def get_unique_ships(self, company_id: str) -> List[str]:
        """
        Get unique ship names from logs
        
        Args:
            company_id: Company ID
            
        Returns:
            List of unique ship names
        """
        ships = await self.collection.distinct('ship_name', {
            'company_id': company_id,
            'ship_name': {'$ne': None, '$ne': '-'}
        })
        
        # Sort alphabetically
        ships = sorted([s for s in ships if s])
        return ships
