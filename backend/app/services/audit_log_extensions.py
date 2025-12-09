"""
Audit Log Extensions for Ships, Ship Certificates, Companies, Users
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4


class ShipAuditMixin:
    """Audit log methods for Ships"""
    
    async def log_ship_create(
        self,
        ship_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship creation"""
        ship_name = ship_data.get('name', 'Unknown')
        
        changes = []
        important_fields = [
            ('name', 'Ship Name'),
            ('imo', 'IMO Number'),
            ('flag', 'Flag'),
            ('ship_type', 'Ship Type'),
            ('class_society', 'Class Society'),
            ('gross_tonnage', 'Gross Tonnage'),
            ('built_year', 'Built Year')
        ]
        
        for field, label in important_fields:
            if ship_data.get(field):
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': None,
                    'new_value': str(ship_data[field]),
                    'value_type': 'string'
                })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship',
            'entity_id': ship_data.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'CREATE_SHIP',
            'action_category': 'SHIP',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Created ship {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'ship_id': ship_data.get('id'),
                'imo': ship_data.get('imo')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_ship_update(
        self,
        old_ship: dict,
        new_ship: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship update"""
        changes = []
        
        fields_to_check = [
            ('name', 'Ship Name', 'string'),
            ('imo', 'IMO Number', 'string'),
            ('flag', 'Flag', 'string'),
            ('ship_type', 'Ship Type', 'string'),
            ('class_society', 'Class Society', 'string'),
            ('gross_tonnage', 'Gross Tonnage', 'number'),
            ('deadweight', 'Deadweight', 'number'),
            ('built_year', 'Built Year', 'number'),
            ('delivery_date', 'Delivery Date', 'date'),
            ('last_docking', 'Last Docking', 'date'),
            ('next_docking', 'Next Docking', 'date')
        ]
        
        for field, label, value_type in fields_to_check:
            old_value = old_ship.get(field)
            new_value = new_ship.get(field)
            
            if value_type == 'date':
                old_value = str(old_value) if old_value else None
                new_value = str(new_value) if new_value else None
            
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': str(old_value) if old_value else None,
                    'new_value': str(new_value) if new_value else None,
                    'value_type': value_type
                })
        
        if not changes:
            return None
        
        ship_name = new_ship.get('name', old_ship.get('name', 'Unknown'))
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship',
            'entity_id': new_ship.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'UPDATE_SHIP',
            'action_category': 'SHIP',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated ship {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'ship_id': new_ship.get('id'),
                'imo': new_ship.get('imo')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_ship_delete(
        self,
        ship_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship deletion"""
        ship_name = ship_data.get('name', 'Unknown')
        
        changes = [{
            'field': 'status',
            'field_label': 'Status',
            'old_value': 'Active',
            'new_value': 'Deleted',
            'value_type': 'string'
        }]
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship',
            'entity_id': ship_data.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'DELETE_SHIP',
            'action_category': 'SHIP',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted ship {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'ship_id': ship_data.get('id'),
                'imo': ship_data.get('imo')
            }
        }
        
        return await self.repository.create_log(log_data)


class ShipCertificateAuditMixin:
    """Audit log methods for Ship Certificates"""
    
    async def log_ship_certificate_create(
        self,
        ship_name: str,
        cert_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship certificate creation"""
        cert_name = cert_data.get('cert_name', 'Unknown')
        cert_no = cert_data.get('cert_no', '-')
        
        changes = [
            {
                'field': 'cert_name',
                'field_label': 'Certificate Name',
                'old_value': None,
                'new_value': cert_name,
                'value_type': 'string'
            },
            {
                'field': 'cert_no',
                'field_label': 'Certificate Number',
                'old_value': None,
                'new_value': cert_no,
                'value_type': 'string'
            }
        ]
        
        if cert_data.get('issue_date'):
            changes.append({
                'field': 'issue_date',
                'field_label': 'Issue Date',
                'old_value': None,
                'new_value': str(cert_data['issue_date']),
                'value_type': 'date'
            })
        
        if cert_data.get('valid_date'):
            changes.append({
                'field': 'valid_date',
                'field_label': 'Valid Until',
                'old_value': None,
                'new_value': str(cert_data['valid_date']),
                'value_type': 'date'
            })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship_certificate',
            'entity_id': cert_data.get('ship_id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'CREATE_SHIP_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Added {cert_name} certificate for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': cert_data.get('id'),
                'certificate_name': cert_name,
                'certificate_number': cert_no
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_ship_certificate_update(
        self,
        ship_name: str,
        old_cert: dict,
        new_cert: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship certificate update"""
        changes = []
        
        fields_to_check = [
            ('cert_name', 'Certificate Name', 'string'),
            ('cert_no', 'Certificate Number', 'string'),
            ('issue_date', 'Issue Date', 'date'),
            ('valid_date', 'Valid Until', 'date'),
            ('last_endorse', 'Last Endorsement', 'date'),
            ('issued_by', 'Issued By', 'string'),
            ('cert_type', 'Certificate Type', 'string')
        ]
        
        for field, label, value_type in fields_to_check:
            old_value = old_cert.get(field)
            new_value = new_cert.get(field)
            
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
            return None
        
        cert_name = new_cert.get('cert_name', old_cert.get('cert_name', 'Unknown'))
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship_certificate',
            'entity_id': new_cert.get('ship_id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'UPDATE_SHIP_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated {cert_name} certificate for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': new_cert.get('id'),
                'certificate_name': cert_name
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_ship_certificate_delete(
        self,
        ship_name: str,
        cert_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log ship certificate deletion"""
        cert_name = cert_data.get('cert_name', 'Unknown')
        cert_no = cert_data.get('cert_no', '-')
        
        changes = [{
            'field': 'status',
            'field_label': 'Status',
            'old_value': 'Active',
            'new_value': 'Deleted',
            'value_type': 'string'
        }]
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'ship_certificate',
            'entity_id': cert_data.get('ship_id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': 'DELETE_SHIP_CERTIFICATE',
            'action_category': 'CERTIFICATE',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted {cert_name} certificate (#{cert_no}) for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'certificate_id': cert_data.get('id'),
                'certificate_name': cert_name,
                'certificate_number': cert_no
            }
        }
        
        return await self.repository.create_log(log_data)


class CompanyAuditMixin:
    """Audit log methods for Companies"""
    
    async def log_company_create(
        self,
        company_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log company creation"""
        company_name = company_data.get('name_vn') or company_data.get('name_en', 'Unknown')
        
        changes = []
        important_fields = [
            ('name_vn', 'Company Name (VN)'),
            ('name_en', 'Company Name (EN)'),
            ('code', 'Company Code'),
            ('tax_id', 'Tax ID'),
            ('email', 'Email'),
            ('phone', 'Phone')
        ]
        
        for field, label in important_fields:
            if company_data.get(field):
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': None,
                    'new_value': str(company_data[field]),
                    'value_type': 'string'
                })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'company',
            'entity_id': company_data.get('id'),
            'entity_name': company_name,
            'company_id': company_data.get('id'),
            'ship_name': '-',
            'action': 'CREATE_COMPANY',
            'action_category': 'SYSTEM',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Created company {company_name}',
            'source': 'WEB_UI',
            'metadata': {
                'company_id': company_data.get('id'),
                'company_code': company_data.get('code')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_company_update(
        self,
        old_company: dict,
        new_company: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log company update"""
        changes = []
        
        fields_to_check = [
            ('name_vn', 'Company Name (VN)', 'string'),
            ('name_en', 'Company Name (EN)', 'string'),
            ('code', 'Company Code', 'string'),
            ('tax_id', 'Tax ID', 'string'),
            ('email', 'Email', 'string'),
            ('phone', 'Phone', 'string'),
            ('address_vn', 'Address (VN)', 'string'),
            ('address_en', 'Address (EN)', 'string'),
            ('is_active', 'Status', 'boolean')
        ]
        
        for field, label, value_type in fields_to_check:
            old_value = old_company.get(field)
            new_value = new_company.get(field)
            
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': str(old_value) if old_value is not None else None,
                    'new_value': str(new_value) if new_value is not None else None,
                    'value_type': value_type
                })
        
        if not changes:
            return None
        
        company_name = new_company.get('name_vn') or new_company.get('name_en', 'Unknown')
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'company',
            'entity_id': new_company.get('id'),
            'entity_name': company_name,
            'company_id': new_company.get('id'),
            'ship_name': '-',
            'action': 'UPDATE_COMPANY',
            'action_category': 'SYSTEM',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated company {company_name}',
            'source': 'WEB_UI',
            'metadata': {
                'company_id': new_company.get('id'),
                'company_code': new_company.get('code')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_company_delete(
        self,
        company_data: dict,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log company deletion"""
        company_name = company_data.get('name_vn') or company_data.get('name_en', 'Unknown')
        
        changes = [{
            'field': 'is_active',
            'field_label': 'Status',
            'old_value': 'True',
            'new_value': 'False',
            'value_type': 'boolean'
        }]
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'company',
            'entity_id': company_data.get('id'),
            'entity_name': company_name,
            'company_id': company_data.get('id'),
            'ship_name': '-',
            'action': 'DELETE_COMPANY',
            'action_category': 'SYSTEM',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted company {company_name}',
            'source': 'WEB_UI',
            'metadata': {
                'company_id': company_data.get('id'),
                'company_code': company_data.get('code')
            }
        }
        
        return await self.repository.create_log(log_data)


class UserAuditMixin:
    """Audit log methods for Users"""
    
    async def log_user_create(
        self,
        user_data: dict,
        performed_by_user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log user creation"""
        username = user_data.get('username', 'Unknown')
        full_name = user_data.get('full_name', username)
        
        changes = []
        important_fields = [
            ('username', 'Username'),
            ('email', 'Email'),
            ('full_name', 'Full Name'),
            ('role', 'Role'),
            ('department', 'Department')
        ]
        
        for field, label in important_fields:
            if user_data.get(field):
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': None,
                    'new_value': str(user_data[field]),
                    'value_type': 'string'
                })
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'user',
            'entity_id': user_data.get('id'),
            'entity_name': full_name,
            'company_id': performed_by_user.get('company'),
            'ship_name': '-',
            'action': 'CREATE_USER',
            'action_category': 'SYSTEM',
            'performed_by': performed_by_user.get('username'),
            'performed_by_id': performed_by_user.get('id'),
            'performed_by_name': performed_by_user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Created user {username}',
            'source': 'WEB_UI',
            'metadata': {
                'user_id': user_data.get('id'),
                'username': username,
                'role': user_data.get('role')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_user_update(
        self,
        old_user: dict,
        new_user: dict,
        performed_by_user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log user update (EXCLUDING password changes)"""
        changes = []
        
        fields_to_check = [
            ('username', 'Username', 'string'),
            ('email', 'Email', 'string'),
            ('full_name', 'Full Name', 'string'),
            ('role', 'Role', 'string'),
            ('department', 'Department', 'string'),
            ('is_active', 'Status', 'boolean')
        ]
        
        for field, label, value_type in fields_to_check:
            old_value = old_user.get(field)
            new_value = new_user.get(field)
            
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'field_label': label,
                    'old_value': str(old_value) if old_value is not None else None,
                    'new_value': str(new_value) if new_value is not None else None,
                    'value_type': value_type
                })
        
        if not changes:
            return None
        
        username = new_user.get('username', old_user.get('username', 'Unknown'))
        full_name = new_user.get('full_name', old_user.get('full_name', username))
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'user',
            'entity_id': new_user.get('id'),
            'entity_name': full_name,
            'company_id': performed_by_user.get('company'),
            'ship_name': '-',
            'action': 'UPDATE_USER',
            'action_category': 'SYSTEM',
            'performed_by': performed_by_user.get('username'),
            'performed_by_id': performed_by_user.get('id'),
            'performed_by_name': performed_by_user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated user {username}',
            'source': 'WEB_UI',
            'metadata': {
                'user_id': new_user.get('id'),
                'username': username,
                'role': new_user.get('role')
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_user_delete(
        self,
        user_data: dict,
        performed_by_user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log user deletion/deactivation"""
        username = user_data.get('username', 'Unknown')
        full_name = user_data.get('full_name', username)
        
        changes = [{
            'field': 'is_active',
            'field_label': 'Status',
            'old_value': 'True',
            'new_value': 'False',
            'value_type': 'boolean'
        }]
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': 'user',
            'entity_id': user_data.get('id'),
            'entity_name': full_name,
            'company_id': performed_by_user.get('company'),
            'ship_name': '-',
            'action': 'DELETE_USER',
            'action_category': 'SYSTEM',
            'performed_by': performed_by_user.get('username'),
            'performed_by_id': performed_by_user.get('id'),
            'performed_by_name': performed_by_user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted/deactivated user {username}',
            'source': 'WEB_UI',
            'metadata': {
                'user_id': user_data.get('id'),
                'username': username,
                'role': user_data.get('role')
            }
        }
        
        return await self.repository.create_log(log_data)



class DocumentAuditMixin:
    """Audit log methods for Documents (Approval, Drawings/Manuals, Survey Reports, Other Docs)"""
    
    async def log_document_create(
        self,
        ship_name: str,
        doc_data: dict,
        doc_type: str,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """
        Log document creation
        doc_type: 'approval_document', 'drawing_manual', 'survey_report', 'other_document'
        """
        doc_name = doc_data.get('approval_document_name') or doc_data.get('document_name') or doc_data.get('report_name') or doc_data.get('doc_name', 'Unknown Document')
        doc_no = doc_data.get('approval_document_no') or doc_data.get('document_no') or doc_data.get('report_no') or doc_data.get('doc_no', '-')
        
        changes = [
            {
                'field': 'document_name',
                'field_label': 'Document Name',
                'old_value': None,
                'new_value': doc_name,
                'value_type': 'string'
            },
            {
                'field': 'document_no',
                'field_label': 'Document Number',
                'old_value': None,
                'new_value': doc_no,
                'value_type': 'string'
            }
        ]
        
        # Add issue/valid dates if present
        if doc_data.get('issue_date'):
            changes.append({
                'field': 'issue_date',
                'field_label': 'Issue Date',
                'old_value': None,
                'new_value': str(doc_data['issue_date']),
                'value_type': 'date'
            })
        
        if doc_data.get('valid_date') or doc_data.get('expiry_date'):
            changes.append({
                'field': 'valid_date',
                'field_label': 'Valid Until',
                'old_value': None,
                'new_value': str(doc_data.get('valid_date') or doc_data.get('expiry_date')),
                'value_type': 'date'
            })
        
        # Map doc_type to action
        action_map = {
            'approval_document': 'CREATE_APPROVAL_DOCUMENT',
            'drawing_manual': 'CREATE_DRAWING_MANUAL',
            'survey_report': 'CREATE_SURVEY_REPORT',
            'other_document': 'CREATE_OTHER_DOCUMENT'
        }
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': doc_type,
            'entity_id': doc_data.get('ship_id') or doc_data.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': action_map.get(doc_type, 'CREATE_DOCUMENT'),
            'action_category': 'DOCUMENT',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Added {doc_name} for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'document_id': doc_data.get('id'),
                'document_name': doc_name,
                'document_number': doc_no,
                'document_type': doc_type
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_document_update(
        self,
        ship_name: str,
        old_doc: dict,
        new_doc: dict,
        doc_type: str,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log document update"""
        changes = []
        
        # Check common fields
        fields_to_check = [
            ('approval_document_name', 'Document Name', 'string'),
            ('document_name', 'Document Name', 'string'),
            ('report_name', 'Report Name', 'string'),
            ('doc_name', 'Document Name', 'string'),
            ('approval_document_no', 'Document Number', 'string'),
            ('document_no', 'Document Number', 'string'),
            ('report_no', 'Report Number', 'string'),
            ('doc_no', 'Document Number', 'string'),
            ('issue_date', 'Issue Date', 'date'),
            ('valid_date', 'Valid Until', 'date'),
            ('expiry_date', 'Expiry Date', 'date'),
            ('issued_by', 'Issued By', 'string'),
            ('status', 'Status', 'string')
        ]
        
        for field, label, value_type in fields_to_check:
            if field not in old_doc and field not in new_doc:
                continue
                
            old_value = old_doc.get(field)
            new_value = new_doc.get(field)
            
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
            return None
        
        doc_name = new_doc.get('approval_document_name') or new_doc.get('document_name') or new_doc.get('report_name') or new_doc.get('doc_name', 'Unknown Document')
        
        # Map doc_type to action
        action_map = {
            'approval_document': 'UPDATE_APPROVAL_DOCUMENT',
            'drawing_manual': 'UPDATE_DRAWING_MANUAL',
            'survey_report': 'UPDATE_SURVEY_REPORT',
            'other_document': 'UPDATE_OTHER_DOCUMENT'
        }
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': doc_type,
            'entity_id': new_doc.get('ship_id') or new_doc.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': action_map.get(doc_type, 'UPDATE_DOCUMENT'),
            'action_category': 'DOCUMENT',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Updated {doc_name} for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'document_id': new_doc.get('id'),
                'document_name': doc_name,
                'document_type': doc_type
            }
        }
        
        return await self.repository.create_log(log_data)
    
    async def log_document_delete(
        self,
        ship_name: str,
        doc_data: dict,
        doc_type: str,
        user: dict,
        notes: Optional[str] = None
    ) -> dict:
        """Log document deletion"""
        doc_name = doc_data.get('approval_document_name') or doc_data.get('document_name') or doc_data.get('report_name') or doc_data.get('doc_name', 'Unknown Document')
        doc_no = doc_data.get('approval_document_no') or doc_data.get('document_no') or doc_data.get('report_no') or doc_data.get('doc_no', '-')
        
        changes = [{
            'field': 'status',
            'field_label': 'Status',
            'old_value': 'Active',
            'new_value': 'Deleted',
            'value_type': 'string'
        }]
        
        # Map doc_type to action
        action_map = {
            'approval_document': 'DELETE_APPROVAL_DOCUMENT',
            'drawing_manual': 'DELETE_DRAWING_MANUAL',
            'survey_report': 'DELETE_SURVEY_REPORT',
            'other_document': 'DELETE_OTHER_DOCUMENT'
        }
        
        log_data = {
            'id': str(uuid4()),
            'entity_type': doc_type,
            'entity_id': doc_data.get('ship_id') or doc_data.get('id'),
            'entity_name': ship_name,
            'company_id': user.get('company'),
            'ship_name': ship_name,
            'action': action_map.get(doc_type, 'DELETE_DOCUMENT'),
            'action_category': 'DOCUMENT',
            'performed_by': user.get('username'),
            'performed_by_id': user.get('id'),
            'performed_by_name': user.get('full_name'),
            'performed_at': datetime.now(timezone.utc),
            'changes': changes,
            'notes': notes or f'Deleted {doc_name} (#{doc_no}) for {ship_name}',
            'source': 'WEB_UI',
            'metadata': {
                'document_id': doc_data.get('id'),
                'document_name': doc_name,
                'document_number': doc_no,
                'document_type': doc_type
            }
        }
        
        return await self.repository.create_log(log_data)
