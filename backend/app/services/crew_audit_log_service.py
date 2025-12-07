"""
Crew Audit Log Service
Business logic for audit logging
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from app.repositories.crew_audit_log_repository import CrewAuditLogRepository


class CrewAuditLogService:
    """Service for crew audit logging"""
    
    def __init__(self, repository: CrewAuditLogRepository):
        self.repository = repository
    
    # Field label mapping for display
    FIELD_LABELS = {
        'full_name': 'Full Name',
        'full_name_en': 'Full Name (EN)',
        'sex': 'Sex',
        'date_of_birth': 'Date of Birth',
        'place_of_birth': 'Place of Birth',
        'place_of_birth_en': 'Place of Birth (EN)',
        'passport': 'Passport',
        'nationality': 'Nationality',
        'rank': 'Rank',
        'seamen_book': 'Seamen Book',
        'status': 'Status',
        'ship_sign_on': 'Ship Sign On',
        'place_sign_on': 'Place Sign On',
        'date_sign_on': 'Date Sign On',
        'place_sign_off': 'Place Sign Off',
        'date_sign_off': 'Date Sign Off',
        'passport_issue_date': 'Passport Issue Date',
        'passport_expiry_date': 'Passport Expiry Date',
        'passport_file_id': 'Passport File',
        'passport_file_name': 'Passport File Name',
    }
    
    def _get_field_label(self, field: str) -> str:
        """Get display label for field"""
        return self.FIELD_LABELS.get(field, field.replace('_', ' ').title())
    
    def _detect_changes(self, old_data: dict, new_data: dict) -> List[dict]:
        """
        Detect changes between old and new data
        
        Args:
            old_data: Original data
            new_data: Updated data
            
        Returns:
            List of change records
        """
        changes = []
        
        # Get all fields that might have changed
        all_fields = set(old_data.keys()) | set(new_data.keys())
        
        # Ignore metadata fields
        ignore_fields = {'_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'id'}
        
        for field in all_fields:
            if field in ignore_fields:
                continue
            
            old_value = old_data.get(field)
            new_value = new_data.get(field)
            
            # Convert datetime to string for comparison
            if isinstance(old_value, datetime):
                old_value = old_value.isoformat() if old_value else None
            if isinstance(new_value, datetime):
                new_value = new_value.isoformat() if new_value else None
            
            # Check if changed
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'field_label': self._get_field_label(field),
                    'old_value': str(old_value) if old_value is not None else None,
                    'new_value': str(new_value) if new_value is not None else None,
                    'value_type': self._get_value_type(new_value)
                })
        
        return changes
    
    def _get_value_type(self, value: Any) -> str:
        """Determine value type"""
        if value is None:
            return 'string'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, datetime):
            return 'date'
        else:
            return 'string'
    
    async def log_crew_create(
        self,
        crew_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log crew creation
        
        Args:
            crew_data: New crew data
            user: User who created (dict with id, username, full_name, company)
            notes: Optional notes
            
        Returns:
            Created log
        """
        # Build changes list (all fields are "new")
        changes = []
        important_fields = ['full_name', 'passport', 'rank', 'status', 'ship_sign_on']
        
        for field in important_fields:
            if field in crew_data and crew_data[field]:
                changes.append({
                    'field': field,
                    'field_label': self._get_field_label(field),
                    'old_value': None,
                    'new_value': str(crew_data[field]),
                    'value_type': self._get_value_type(crew_data[field])
                })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_data.get('id'),
            'entity_name': crew_data.get('full_name'),
            'company_id': user.get('company'),
            'ship_name': crew_data.get('ship_sign_on') or '-',
            'action': 'CREATE',
            'action_category': 'LIFECYCLE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.utcnow(),
            'changes': changes,
            'notes': notes or 'Created new crew member',
            'source': 'WEB_UI'
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_crew_update(
        self,
        crew_id: str,
        old_data: dict,
        new_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log crew update
        
        Args:
            crew_id: Crew ID
            old_data: Original crew data
            new_data: Updated crew data
            user: User who updated
            notes: Optional notes
            
        Returns:
            Created log
        """
        # Detect changes
        changes = self._detect_changes(old_data, new_data)
        
        if not changes:
            # No changes detected, don't create log
            return None
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_id,
            'entity_name': new_data.get('full_name', old_data.get('full_name')),
            'company_id': user.get('company'),
            'ship_name': new_data.get('ship_sign_on') or old_data.get('ship_sign_on') or '-',
            'action': 'UPDATE',
            'action_category': 'DATA_CHANGE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.utcnow(),
            'changes': changes,
            'notes': notes or f'Updated {len(changes)} field(s)',
            'source': 'WEB_UI'
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_crew_delete(
        self,
        crew_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log crew deletion
        
        Args:
            crew_data: Deleted crew data
            user: User who deleted
            notes: Optional notes
            
        Returns:
            Created log
        """
        # Build changes list (all fields are "removed")
        changes = []
        important_fields = ['full_name', 'passport', 'status']
        
        for field in important_fields:
            if field in crew_data and crew_data[field]:
                changes.append({
                    'field': field,
                    'field_label': self._get_field_label(field),
                    'old_value': str(crew_data[field]),
                    'new_value': None,
                    'value_type': self._get_value_type(crew_data[field])
                })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_data.get('id'),
            'entity_name': crew_data.get('full_name'),
            'company_id': user.get('company'),
            'ship_name': crew_data.get('ship_sign_on') or '-',
            'action': 'DELETE',
            'action_category': 'LIFECYCLE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.utcnow(),
            'changes': changes,
            'notes': notes or 'Deleted crew member',
            'source': 'WEB_UI'
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_crew_sign_on(
        self,
        crew_id: str,
        crew_name: str,
        ship_name: str,
        date_sign_on: Optional[datetime],
        place_sign_on: Optional[str],
        user: dict,
        old_ship: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log crew sign on
        
        Args:
            crew_id: Crew ID
            crew_name: Crew name
            ship_name: Ship name signing on to
            date_sign_on: Sign on date
            place_sign_on: Sign on place
            user: User who performed action
            old_ship: Previous ship (if transfer)
            notes: Optional notes
            
        Returns:
            Created log
        """
        changes = [
            {
                'field': 'ship_sign_on',
                'field_label': 'Ship Sign On',
                'old_value': old_ship or '-',
                'new_value': ship_name,
                'value_type': 'string'
            },
            {
                'field': 'status',
                'field_label': 'Status',
                'old_value': 'Standby' if not old_ship else 'Sign on',
                'new_value': 'Sign on',
                'value_type': 'string'
            }
        ]
        
        if date_sign_on:
            changes.append({
                'field': 'date_sign_on',
                'field_label': 'Date Sign On',
                'old_value': None,
                'new_value': date_sign_on.strftime('%Y-%m-%d') if isinstance(date_sign_on, datetime) else str(date_sign_on),
                'value_type': 'date'
            })
        
        if place_sign_on:
            changes.append({
                'field': 'place_sign_on',
                'field_label': 'Place Sign On',
                'old_value': None,
                'new_value': place_sign_on,
                'value_type': 'string'
            })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'SHIP_TRANSFER' if old_ship else 'SIGN_ON',
            'action_category': 'STATUS_CHANGE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.utcnow(),
            'changes': changes,
            'notes': notes or (f'Transferred from {old_ship} to {ship_name}' if old_ship else f'Signed on to {ship_name}'),
            'source': 'WEB_UI'
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_crew_sign_off(
        self,
        crew_id: str,
        crew_name: str,
        ship_name: str,
        date_sign_off: Optional[datetime],
        place_sign_off: Optional[str],
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log crew sign off
        
        Args:
            crew_id: Crew ID
            crew_name: Crew name
            ship_name: Ship name signing off from
            date_sign_off: Sign off date
            place_sign_off: Sign off place
            user: User who performed action
            notes: Optional notes
            
        Returns:
            Created log
        """
        changes = [
            {
                'field': 'ship_sign_on',
                'field_label': 'Ship Sign On',
                'old_value': ship_name,
                'new_value': '-',
                'value_type': 'string'
            },
            {
                'field': 'status',
                'field_label': 'Status',
                'old_value': 'Sign on',
                'new_value': 'Standby',
                'value_type': 'string'
            }
        ]
        
        if date_sign_off:
            changes.append({
                'field': 'date_sign_off',
                'field_label': 'Date Sign Off',
                'old_value': None,
                'new_value': date_sign_off.strftime('%Y-%m-%d') if isinstance(date_sign_off, datetime) else str(date_sign_off),
                'value_type': 'date'
            })
        
        if place_sign_off:
            changes.append({
                'field': 'place_sign_off',
                'field_label': 'Place Sign Off',
                'old_value': None,
                'new_value': place_sign_off,
                'value_type': 'string'
            })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'SIGN_OFF',
            'action_category': 'STATUS_CHANGE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.utcnow(),
            'changes': changes,
            'notes': notes or f'Signed off from {ship_name}',
            'source': 'WEB_UI'
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_bulk_update(
        self,
        crew_updates: List[Dict[str, Any]],
        user: dict,
        notes: Optional[str] = None
    ) -> List[dict]:
        """
        Log bulk update operation
        
        Args:
            crew_updates: List of {crew_id, crew_name, old_data, new_data, ship_name}
            user: User who performed action
            notes: Optional notes
            
        Returns:
            List of created logs
        """
        logs = []
        
        for update in crew_updates:
            changes = self._detect_changes(update['old_data'], update['new_data'])
            
            if not changes:
                continue
            
            log_data = {
                'id': str(uuid4()),
                'entity_type': 'crew',
                'entity_id': update['crew_id'],
                'entity_name': update['crew_name'],
                'company_id': user.get('company'),
                'ship_name': update.get('ship_name', '-'),
                'action': 'BULK_UPDATE',
                'action_category': 'DATA_CHANGE',
                'performed_by': user.get('username'),
                'performed_by_id': user.get('id'),
                'performed_by_name': user.get('full_name'),
                'performed_at': datetime.utcnow(),
                'changes': changes,
                'notes': notes or f'Bulk update - {len(changes)} field(s) changed',
                'source': 'WEB_UI'
            }
            
            log = await self.repository.create_log(log_data)
            logs.append(log)
        
        return logs
