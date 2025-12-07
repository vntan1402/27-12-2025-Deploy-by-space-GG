"""
Script to update Document AI Apps Script URL
Usage: python3 scripts/update_document_ai_url.py <NEW_URL>
"""
import sys
from pymongo import MongoClient
from datetime import datetime

def update_document_ai_url(new_url: str):
    """Update Document AI Apps Script URL for company"""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["ship_management"]
    
    # Company ID
    COMPANY_ID = "0a6eaf96-0aaf-4793-89be-65d62cb7953c"
    
    print(f"🔄 Updating Document AI URL...")
    print(f"   Company: {COMPANY_ID}")
    print(f"   New URL: {new_url}\n")
    
    # Update
    result = db.ai_config.update_one(
        {"company": COMPANY_ID},
        {
            "$set": {
                "document_ai.apps_script_url": new_url,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"✅ Đã update thành công!")
        
        # Verify
        doc = db.ai_config.find_one({"company": COMPANY_ID})
        current_url = doc.get('document_ai', {}).get('apps_script_url')
        
        print(f"\n📋 Xác nhận từ Database:")
        print(f"   {current_url}")
        
        if current_url == new_url:
            print(f"\n✅ Verified: URL đã được lưu đúng!")
        else:
            print(f"\n⚠️  Warning: URL trong DB khác với URL vừa nhập!")
    else:
        print("⚠️  Không có thay đổi (có thể URL giống cũ hoặc company không tồn tại)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Thiếu URL!")
        print("\nUsage:")
        print("  python3 scripts/update_document_ai_url.py <NEW_URL>")
        print("\nExample:")
        print('  python3 scripts/update_document_ai_url.py "https://script.google.com/macros/s/ABC123/exec"')
        sys.exit(1)
    
    new_url = sys.argv[1]
    
    if not new_url.startswith("https://"):
        print("⚠️  Warning: URL không bắt đầu bằng https://")
        confirm = input("Tiếp tục? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            sys.exit(0)
    
    update_document_ai_url(new_url)
