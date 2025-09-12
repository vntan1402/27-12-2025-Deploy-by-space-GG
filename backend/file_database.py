import os
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class FileDatabase:
    def __init__(self, data_path: str = "/app/backend/data"):
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)
        
        # Initialize data files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize JSON files with empty data structures"""
        default_data = {
            'users.json': [],
            'ships.json': [],
            'certificates.json': [],
            'company_settings.json': {},
            'ai_analyses.json': []
        }
        
        for filename, default_content in default_data.items():
            file_path = os.path.join(self.data_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(default_content, f, default=str)

    def _load_data(self, collection: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        file_path = os.path.join(self.data_path, f'{collection}.json')
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {collection}: {e}")
            return []

    def _save_data(self, collection: str, data: List[Dict[str, Any]]):
        """Save data to JSON file"""
        file_path = os.path.join(self.data_path, f'{collection}.json')
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error saving {collection}: {e}")

    def _load_single_data(self, filename: str) -> Dict[str, Any]:
        """Load single document data (like company_settings)"""
        file_path = os.path.join(self.data_path, filename)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}

    def _save_single_data(self, filename: str, data: Dict[str, Any]):
        """Save single document data"""
        file_path = os.path.join(self.data_path, filename)
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")

    # Users collection methods
    def find_user(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a user by query"""
        users = self._load_data('users')
        for user in users:
            match = True
            for key, value in query.items():
                if key == '$or':
                    or_match = False
                    for or_condition in value:
                        if all(user.get(k) == v for k, v in or_condition.items()):
                            or_match = True
                            break
                    if not or_match:
                        match = False
                        break
                elif user.get(key) != value:
                    match = False
                    break
            if match:
                return user
        return None

    def find_all_users(self) -> List[Dict[str, Any]]:
        """Find all users"""
        return self._load_data('users')

    def insert_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new user"""
        users = self._load_data('users')
        if 'id' not in user_data:
            user_data['id'] = str(uuid.uuid4())
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.now(timezone.utc).isoformat()
        
        users.append(user_data)
        self._save_data('users', users)
        return user_data

    def update_users(self, query: Dict[str, Any], update_data: Dict[str, Any]):
        """Update users matching query"""
        users = self._load_data('users')
        updated = False
        
        for user in users:
            if query.get('id') and user.get('id') in query['id'].get('$in', []):
                user.update(update_data)
                updated = True
        
        if updated:
            self._save_data('users', users)

    # Ships collection methods
    def find_all_ships(self) -> List[Dict[str, Any]]:
        """Find all ships"""
        return self._load_data('ships')

    def find_ship(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a ship by query"""
        ships = self._load_data('ships')
        for ship in ships:
            if all(ship.get(k) == v for k, v in query.items()):
                return ship
        return None

    def insert_ship(self, ship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new ship"""
        ships = self._load_data('ships')
        if 'id' not in ship_data:
            ship_data['id'] = str(uuid.uuid4())
        if 'created_at' not in ship_data:
            ship_data['created_at'] = datetime.now(timezone.utc).isoformat()
        
        ships.append(ship_data)
        self._save_data('ships', ships)
        return ship_data

    # Certificates collection methods
    def find_certificates(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find certificates by query"""
        certificates = self._load_data('certificates')
        result = []
        for cert in certificates:
            if all(cert.get(k) == v for k, v in query.items()):
                result.append(cert)
        return result

    def insert_certificate(self, cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new certificate"""
        certificates = self._load_data('certificates')
        if 'id' not in cert_data:
            cert_data['id'] = str(uuid.uuid4())
        if 'created_at' not in cert_data:
            cert_data['created_at'] = datetime.now(timezone.utc).isoformat()
        
        certificates.append(cert_data)
        self._save_data('certificates', certificates)
        return cert_data

    # AI Analyses collection methods
    def insert_ai_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert AI analysis result"""
        analyses = self._load_data('ai_analyses')
        if 'id' not in analysis_data:
            analysis_data['id'] = str(uuid.uuid4())
        
        analyses.append(analysis_data)
        self._save_data('ai_analyses', analyses)
        return analysis_data

    # Company Settings methods
    def get_company_settings(self) -> Dict[str, Any]:
        """Get company settings"""
        return self._load_single_data('company_settings.json')

    def update_company_settings(self, settings_data: Dict[str, Any]):
        """Update company settings"""
        self._save_single_data('company_settings.json', settings_data)

    # AI Configuration methods
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return self._load_single_data('ai_config.json')

    def update_ai_config(self, config_data: Dict[str, Any]):
        """Update AI provider configuration"""
        self._save_single_data('ai_config.json', config_data)

    # Company Management methods
    def find_all_companies(self) -> List[Dict[str, Any]]:
        """Find all companies"""
        return self._load_data('companies')

    def find_company(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single company by query"""
        companies = self._load_data('companies')
        for company in companies:
            if all(company.get(k) == v for k, v in query.items()):
                return company
        return None

    def insert_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new company"""
        companies = self._load_data('companies')
        companies.append(company_data)
        self._save_data('companies', companies)
        return company_data

    def update_company(self, query: Dict[str, Any], update_data: Dict[str, Any]):
        """Update a company"""
        companies = self._load_data('companies')
        for i, company in enumerate(companies):
            if all(company.get(k) == v for k, v in query.items()):
                companies[i] = update_data
                break
        self._save_data('companies', companies)

    def delete_company(self, query: Dict[str, Any]):
        """Delete a company"""
        companies = self._load_data('companies')
        companies = [company for company in companies if not all(company.get(k) == v for k, v in query.items())]
        self._save_data('companies', companies)

# Global database instance
file_db = FileDatabase()