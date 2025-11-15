"""
Script to fix ships that have company_id: null
Updates TEST SHIP 001 and BROTHER 36 with correct company_id from AMCSC company
"""
import asyncio
import os
import sys
import logging
from mongodb_database import mongo_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_ships_company_id():
    """Fix ships with null company_id"""
    try:
        # Connect to database
        logger.info("Connecting to MongoDB...")
        await mongo_db.connect()
        
        # Find AMCSC company to get the correct company_id
        logger.info("Finding AMCSC company...")
        amcsc_company = await mongo_db.database.companies.find_one({
            "$or": [
                {"name_en": {"$regex": "AMCSC", "$options": "i"}},
                {"name_vn": {"$regex": "AMCSC", "$options": "i"}}
            ]
        })
        
        if not amcsc_company:
            logger.error("AMCSC company not found!")
            return
        
        company_id = amcsc_company.get('id')
        logger.info(f"Found AMCSC company with ID: {company_id}")
        
        # Find ships with null company_id
        logger.info("Finding ships with null company_id...")
        ships_to_fix = await mongo_db.database.ships.find({
            "$or": [
                {"company_id": None},
                {"company_id": {"$exists": False}}
            ]
        }).to_list(length=None)
        
        logger.info(f"Found {len(ships_to_fix)} ships with null company_id")
        
        # Update each ship
        for ship in ships_to_fix:
            ship_name = ship.get('name', 'Unknown')
            ship_id = ship.get('id')
            
            logger.info(f"Updating ship: {ship_name} (ID: {ship_id})")
            
            result = await mongo_db.database.ships.update_one(
                {"id": ship_id},
                {"$set": {"company_id": company_id}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Successfully updated {ship_name}")
            else:
                logger.warning(f"⚠️ No changes made to {ship_name}")
        
        # Verify the updates
        logger.info("\nVerifying updates...")
        updated_ships = await mongo_db.database.ships.find({
            "name": {"$in": ["TEST SHIP 001", "BROTHER 36"]}
        }).to_list(length=None)
        
        for ship in updated_ships:
            logger.info(f"Ship: {ship.get('name')} - company_id: {ship.get('company_id')}")
        
        logger.info("\n✅ All ships updated successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error fixing ships: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect from database
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(fix_ships_company_id())
