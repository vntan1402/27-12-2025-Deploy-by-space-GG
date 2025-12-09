"""
Crew Audit Log Service
Business logic for audit logging
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
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
            'performed_at': datetime.now(timezone.utc),
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
            'performed_at': datetime.now(timezone.utc),
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
            'performed_at': datetime.now(timezone.utc),
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
        # Determine action type and old status based on old_ship
        is_new_sign_on = not old_ship or old_ship in ['-', '', None]
        old_status = 'Standby' if is_new_sign_on else 'Sign on'
        
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
                'old_value': old_status,
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
        
        # Determine action type based on ship change and status
        if is_new_sign_on:
            # New sign on (from Standby or no previous ship)
            action = 'SIGN_ON'
            default_notes = f'Signed on to {ship_name}'
        elif old_ship != ship_name:
            # Transfer between ships (both were Sign on status)
            action = 'SHIP_TRANSFER'
            default_notes = f'Transferred from {old_ship} to {ship_name}'
        else:
            # Same ship, just updating sign on details (date/place)
            action = 'UPDATE'
            default_notes = f'Updated sign on details for {ship_name}'
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'crew',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': action,
            'action_category': 'STATUS_CHANGE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or default_notes,
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
            'performed_at': datetime.now(timezone.utc),
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
                'performed_at': datetime.now(timezone.utc),
                'changes': changes,
                'notes': notes or f'Bulk update - {len(changes)} field(s) changed',
                'source': 'WEB_UI'
            }
            
            log = await self.repository.create_log(log_data)
            logs.append(log)
        
        return logs

    async def log_certificate_create(
        self,
        crew_id: str,
        crew_name: str,
        cert_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log certificate creation
        
        Args:
            crew_id: Crew member ID
            crew_name: Crew member name
            cert_data: Certificate data
            user: User who performed the action
            notes: Optional notes
        """
        cert_type = cert_data.get('cert_type', 'Unknown')
        cert_number = cert_data.get('cert_number', '-')
        
        changes = [
            {
                'field': 'cert_type',
                'field_label': 'Certificate Type',
                'old_value': None,
                'new_value': cert_type,
                'value_type': 'string'
            },
            {
                'field': 'cert_number',
                'field_label': 'Certificate Number',
                'old_value': None,
                'new_value': cert_number,
                'value_type': 'string'
            }
        ]
        
        # Add issue and expiry dates if present
        if cert_data.get('issue_date'):
            changes.append({
                'field': 'issue_date',
                'field_label': 'Issue Date',
                'old_value': None,
                'new_value': str(cert_data['issue_date']),
                'value_type': 'date'
            })
        
        if cert_data.get('expiry_date'):
            changes.append({
                'field': 'expiry_date',
                'field_label': 'Expiry Date',
                'old_value': None,
                'new_value': str(cert_data['expiry_date']),
                'value_type': 'date'
            })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'certificate',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': cert_data.get('ship_name', '-'),
            'action': 'CREATE_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Added {cert_type} certificate',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': cert_data.get('id'),
                'certificate_type': cert_type,
                'certificate_number': cert_number
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_certificate_update(
        self,
        crew_id: str,
        crew_name: str,
        old_cert: dict,
        new_cert: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log certificate update
        
        Args:
            crew_id: Crew member ID
            crew_name: Crew member name
            old_cert: Old certificate data
            new_cert: New certificate data
            user: User who performed the action
            notes: Optional notes
        """
        changes = []
        
        # Track all changed fields (use actual DB field names)
        fields_to_check = [
            ('cert_name', 'Certificate Type', 'string'),
            ('cert_no', 'Certificate Number', 'string'),
            ('issued_date', 'Issue Date', 'date'),
            ('cert_expiry', 'Expiry Date', 'date'),
            ('issue_place', 'Issue Place', 'string'),
            ('rank', 'Rank', 'string'),
            ('status', 'Status', 'string'),
            ('issued_by', 'Issued By', 'string')
        ]
        
        for field, label, value_type in fields_to_check:
            old_value = old_cert.get(field)
            new_value = new_cert.get(field)
            
            # Convert dates to string for comparison
            if value_type == 'date':
                old_value = str(old_value) if old_value else None
                new_value = str(new_value) if new_value else None
            
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': old_value,
                    'new_value': new_value,
                    'value_type': value_type
                })
        
        if not changes:
            # No actual changes, skip logging
            return None
        
        cert_type = new_cert.get('cert_type', old_cert.get('cert_type', 'Unknown'))
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'certificate',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': new_cert.get('ship_name', old_cert.get('ship_name', '-')),
            'action': 'UPDATE_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated {cert_type} certificate',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': new_cert.get('id'),
                'certificate_type': cert_type
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_certificate_delete(
        self,
        crew_id: str,
        crew_name: str,
        cert_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log certificate deletion
        
        Args:
            crew_id: Crew member ID
            crew_name: Crew member name
            cert_data: Certificate data being deleted
            user: User who performed the action
            notes: Optional notes
        """
        cert_type = cert_data.get('cert_type', 'Unknown')
        cert_number = cert_data.get('cert_number', '-')
        
        changes = [
            {
                'field': 'status',
                'field_label': 'Status',
                'old_value': 'Active',
                'new_value': 'Deleted',
                'value_type': 'string'
            }
        ]
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'certificate',
            'entity_id': crew_id,
            'entity_name': crew_name,
            'company_id': user.get('company'),
            'ship_name': cert_data.get('ship_name', '-'),
            'action': 'DELETE_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted {cert_type} certificate (#{cert_number})',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': cert_data.get('id'),
                'certificate_type': cert_type,
                'certificate_number': cert_number
            }
        }
        
        return await self.repository.create_log(log_data)

