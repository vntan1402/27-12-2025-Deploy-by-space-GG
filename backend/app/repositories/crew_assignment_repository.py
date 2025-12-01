"""Repository for crew assignment history operations"""
import logging
from typing import List, Optional
from datetime import datetime

from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)


class CrewAssignmentRepository:
    """Handle database operations for crew assignment history"""
    
    collection_name = "crew_assignment_history"
    
    @staticmethod
    async def create(assignment_data: dict) -> dict:
        """
        Create new crew assignment history record
        
        Args:
            assignment_data: Dict with assignment fields
            
        Returns:
            Created assignment record
        """
        try:
            result = await mongo_db.database[CrewAssignmentRepository.collection_name].insert_one(
                assignment_data
            )
            
            if result.inserted_id:
                logger.info(f"✅ Created assignment history: {assignment_data['id']}")
                return assignment_data
            else:
                logger.error("❌ Failed to create assignment history")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating assignment history: {e}")
            raise
    
    @staticmethod
    async def find_by_id(assignment_id: str) -> Optional[dict]:
        """
        Find assignment history by ID
        
        Args:
            assignment_id: Assignment UUID
            
        Returns:
            Assignment record or None
        """
        try:
            assignment = await mongo_db.find_one(
                CrewAssignmentRepository.collection_name,
                {"id": assignment_id},
                {"_id": 0}
            )
            return assignment
        except Exception as e:
            logger.error(f"❌ Error finding assignment {assignment_id}: {e}")
            return None
    
    @staticmethod
    async def find_by_crew_id(
        crew_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[dict]:
        """
        Find all assignment history for a crew member
        
        Args:
            crew_id: Crew UUID
            limit: Max records to return
            skip: Number of records to skip
            
        Returns:
            List of assignment records, sorted by action_date descending
        """
        try:
            assignments = await mongo_db.find(
                CrewAssignmentRepository.collection_name,
                {"crew_id": crew_id},
                {"_id": 0},
                sort=[("action_date", -1)],
                limit=limit,
                skip=skip
            )
            return assignments
        except Exception as e:
            logger.error(f"❌ Error finding assignments for crew {crew_id}: {e}")
            return []
    
    @staticmethod
    async def find_by_company(
        company_id: str,
        action_type: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[dict]:
        """
        Find assignment history for a company
        
        Args:
            company_id: Company UUID
            action_type: Optional filter by action type
            limit: Max records to return
            skip: Number of records to skip
            
        Returns:
            List of assignment records
        """
        try:
            query = {"company_id": company_id}
            if action_type:
                query["action_type"] = action_type
            
            assignments = await mongo_db.find(
                CrewAssignmentRepository.collection_name,
                query,
                {"_id": 0},
                sort=[("created_at", -1)],
                limit=limit,
                skip=skip
            )
            return assignments
        except Exception as e:
            logger.error(f"❌ Error finding assignments for company {company_id}: {e}")
            return []
    
    @staticmethod
    async def count_by_crew(crew_id: str) -> int:
        """
        Count assignment history records for a crew member
        
        Args:
            crew_id: Crew UUID
            
        Returns:
            Count of records
        """
        try:
            count = await mongo_db.count(
                CrewAssignmentRepository.collection_name,
                {"crew_id": crew_id}
            )
            return count
        except Exception as e:
            logger.error(f"❌ Error counting assignments for crew {crew_id}: {e}")
            return 0
    
    @staticmethod
    async def get_latest_assignment(crew_id: str) -> Optional[dict]:
        """
        Get the most recent assignment for a crew member
        
        Args:
            crew_id: Crew UUID
            
        Returns:
            Latest assignment record or None
        """
        try:
            assignments = await CrewAssignmentRepository.find_by_crew_id(
                crew_id,
                limit=1,
                skip=0
            )
            
            if assignments:
                return assignments[0]
            return None
        except Exception as e:
            logger.error(f"❌ Error getting latest assignment for crew {crew_id}: {e}")
            return None
    
    @staticmethod
    async def delete(assignment_id: str) -> bool:
        """
        Delete assignment history record (rarely used)
        
        Args:
            assignment_id: Assignment UUID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await mongo_db.delete_one(
                CrewAssignmentRepository.collection_name,
                {"id": assignment_id}
            )
            
            if result:
                logger.info(f"✅ Deleted assignment history: {assignment_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting assignment {assignment_id}: {e}")
            return False
