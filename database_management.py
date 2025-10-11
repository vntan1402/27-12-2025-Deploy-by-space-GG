#!/usr/bin/env python3
"""
Database Management Utility

This script provides various database management functions:
1. View crew data statistics
2. Clear all crew data
3. Clear specific crew records
4. View file linking status
"""

import os
import sys
import asyncio
from pymongo import MongoClient
from datetime import datetime
import json

# Add the backend directory to sys.path
sys.path.append('/app/backend')

class DatabaseManager:
    def __init__(self):
        # Get MongoDB URL from backend .env
        self.mongo_url = "mongodb://localhost:27017/ship_management"
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            print(f"🔗 Connecting to MongoDB: {self.mongo_url}")
            self.client = MongoClient(self.mongo_url)
            self.db = self.client.ship_management
            
            # Test connection
            self.db.list_collection_names()
            print("✅ Connected to MongoDB successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {str(e)}")
            return False
    
    def view_crew_statistics(self):
        """View crew data statistics"""
        try:
            print("\n📊 CREW DATA STATISTICS")
            print("=" * 40)
            
            crew_collection = self.db.crew_members
            total_crew = crew_collection.count_documents({})
            
            print(f"Total crew members: {total_crew}")
            
            if total_crew > 0:
                # Count by company
                pipeline = [
                    {"$group": {"_id": "$company_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                by_company = list(crew_collection.aggregate(pipeline))
                
                print(f"Crew by company:")
                for item in by_company:
                    company_id = item["_id"]
                    count = item["count"]
                    print(f"  Company {company_id}: {count} crew members")
                
                # Count with file IDs
                with_passport_files = crew_collection.count_documents({"passport_file_id": {"$exists": True, "$ne": None}})
                with_summary_files = crew_collection.count_documents({"summary_file_id": {"$exists": True, "$ne": None}})
                
                print(f"Crew with passport files: {with_passport_files}")
                print(f"Crew with summary files: {with_summary_files}")
                
                # Recent crew
                print(f"\nRecent crew members:")
                recent_crew = crew_collection.find({}).sort("created_at", -1).limit(5)
                for crew in recent_crew:
                    created_at = crew.get("created_at", "Unknown")
                    name = crew.get("full_name", "Unknown")
                    passport = crew.get("passport", "No passport")
                    passport_file = "📄" if crew.get("passport_file_id") else "❌"
                    summary_file = "📋" if crew.get("summary_file_id") else "❌"
                    print(f"  {name} ({passport}) - {passport_file}{summary_file} - {created_at}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error viewing statistics: {str(e)}")
            return False
    
    def clear_all_crew_data(self, force=False):
        """Clear all crew data"""
        try:
            crew_collection = self.db.crew_members
            crew_count = crew_collection.count_documents({})
            
            if crew_count == 0:
                print("✅ No crew members found - database is already clean")
                return True
            
            if not force:
                print(f"⚠️  WARNING: This will DELETE ALL {crew_count} crew members!")
                print("⚠️  This action CANNOT be undone!")
                
                confirmation = input("Are you sure you want to proceed? Type 'DELETE ALL' to confirm: ")
                
                if confirmation != 'DELETE ALL':
                    print("❌ Operation cancelled")
                    return False
            
            # Delete all crew members
            print(f"🗑️ Deleting all {crew_count} crew members...")
            result = crew_collection.delete_many({})
            
            print(f"✅ Successfully deleted {result.deleted_count} crew members")
            
            # Log the operation
            audit_collection = self.db.audit_logs
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "action": "CLEAR_ALL_CREW_DATA",
                "user": "database_manager",
                "details": {
                    "deleted_count": result.deleted_count,
                    "operation_time": datetime.utcnow().isoformat()
                }
            }
            audit_collection.insert_one(audit_entry)
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing crew data: {str(e)}")
            return False
    
    def view_crew_details(self, limit=10):
        """View detailed crew information"""
        try:
            print(f"\n👥 CREW DETAILS (Latest {limit})")
            print("=" * 60)
            
            crew_collection = self.db.crew_members
            crew_members = crew_collection.find({}).sort("created_at", -1).limit(limit)
            
            for i, crew in enumerate(crew_members, 1):
                print(f"\n{i}. {crew.get('full_name', 'Unknown Name')}")
                print(f"   ID: {crew.get('id', 'No ID')}")
                print(f"   Passport: {crew.get('passport', 'No passport')}")
                print(f"   Company: {crew.get('company_id', 'No company')}")
                print(f"   Created: {crew.get('created_at', 'Unknown')}")
                
                # File IDs
                passport_file_id = crew.get('passport_file_id')
                summary_file_id = crew.get('summary_file_id')
                
                if passport_file_id or summary_file_id:
                    print(f"   Files:")
                    if passport_file_id:
                        print(f"     📄 Passport: {passport_file_id}")
                    if summary_file_id:
                        print(f"     📋 Summary: {summary_file_id}")
                else:
                    print(f"   Files: No files linked")
            
            return True
            
        except Exception as e:
            print(f"❌ Error viewing crew details: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print("🔗 Database connection closed")

def main():
    """Main function"""
    print("🗄️  DATABASE MANAGEMENT UTILITY")
    print("=" * 50)
    
    db_manager = DatabaseManager()
    
    if not db_manager.connect():
        return False
    
    try:
        while True:
            print("\nSelect an option:")
            print("1. View crew statistics")
            print("2. View crew details")
            print("3. Clear all crew data")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                db_manager.view_crew_statistics()
            elif choice == "2":
                db_manager.view_crew_details()
            elif choice == "3":
                db_manager.clear_all_crew_data()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    finally:
        db_manager.close()
    
    return True

if __name__ == "__main__":
    main()