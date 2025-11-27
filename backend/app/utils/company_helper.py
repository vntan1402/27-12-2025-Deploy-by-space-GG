"""
Company helper utilities
"""
import logging
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

async def resolve_company_id(current_user) -> str:
    """
    Resolve company name to UUID
    
    Logic:
    - If current_user.company already looks like UUID (has '-' and len > 10) → Return as-is
    - Else: Lookup in companies collection by name_vn, name_en, or name
    - Return company UUID
    
    Args:
        current_user: User object with company attribute
        
    Returns:
        str: Company UUID
        
    Raises:
        Exception: If company not found
    """
    try:
        company_identifier = current_user.company
        
        # Check if already a UUID (contains '-' and reasonable length)
        if '-' in company_identifier and len(company_identifier) > 10:
            logger.info(f"Company identifier appears to be UUID: {company_identifier}")
            return company_identifier
        
        # Otherwise, lookup by name
        logger.info(f"Resolving company name to UUID: {company_identifier}")
        
        # Try to find by name_vn, name_en, or name
        company = await mongo_db.find_one("companies", {
            "$or": [
                {"name_vn": company_identifier},
                {"name_en": company_identifier},
                {"name": company_identifier}
            ]
        })
        
        if not company:
            logger.error(f"Company not found: {company_identifier}")
            raise Exception(f"Company not found: {company_identifier}")
        
        company_id = company.get("id")
        logger.info(f"Resolved company '{company_identifier}' to UUID: {company_id}")
        
        return company_id
        
    except Exception as e:
        logger.error(f"Error resolving company ID: {e}")
        raise
