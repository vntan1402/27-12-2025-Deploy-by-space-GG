#!/usr/bin/env python3
"""
Check Survey Reports in database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_survey_reports():
    """Check all survey reports in database"""
    try:
        # Get MongoDB URL from environment
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client.ship_management
        
        print("🔗 Connected to MongoDB")
        
        # Count survey reports
        count = await db.survey_reports.count_documents({})
        print(f"\n📊 Total Survey Reports: {count}")
        
        if count > 0:
            # Get all survey reports
            reports = await db.survey_reports.find({}).to_list(length=None)
            
            print("\n📋 Survey Reports in database:")
            print("=" * 80)
            for i, report in enumerate(reports, 1):
                print(f"\n{i}. Report ID: {report.get('id', 'N/A')}")
                print(f"   Name: {report.get('survey_report_name', 'N/A')}")
                print(f"   No.: {report.get('survey_report_no', 'N/A')}")
                print(f"   Ship ID: {report.get('ship_id', 'N/A')}")
                print(f"   Issued Date: {report.get('issued_date', 'N/A')}")
                print(f"   Status: {report.get('status', 'N/A')}")
        else:
            print("\n✅ No Survey Reports found in database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    print("=" * 80)
    print("🔍 CHECK SURVEY REPORTS IN DATABASE")
    print("=" * 80)
    
    asyncio.run(check_survey_reports())
    
    print("\n" + "=" * 80)
