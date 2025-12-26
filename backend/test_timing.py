"""Test timing for Certificate FAST PATH"""
import asyncio
import time
import os
import sys
sys.path.insert(0, '/app/backend')

os.environ['MONGO_URL'] = 'mongodb://localhost:27017/ship_management'
os.environ['DB_NAME'] = 'ship_management'
os.environ['EMERGENT_LLM_KEY'] = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-eEe35Fb1b449940199')

from app.db.mongodb import mongo_db

async def test_timing():
    # Connect to DB
    await mongo_db.connect()
    
    # Find a test PDF with text layer
    test_file = "/app/backend/tests/test_files/sample_cert.pdf"
    
    if not os.path.exists(test_file):
        print("❌ No test file found")
        return
    
    with open(test_file, 'rb') as f:
        file_content = f.read()
    
    print(f"\n📄 Test file: {test_file} ({len(file_content)} bytes)")
    print("=" * 60)
    
    # Test 1: Quick check text layer
    from app.utils.pdf_text_extractor import quick_check_text_layer
    
    start = time.time()
    text_check = quick_check_text_layer(file_content, "test.pdf")
    t1 = time.time() - start
    print(f"1️⃣ quick_check_text_layer: {t1:.2f}s")
    print(f"   Result: {text_check.get('char_count', 0)} chars, FAST_PATH: {text_check.get('has_sufficient_text', False)}")
    
    if not text_check.get("has_sufficient_text"):
        print("⚠️ File doesn't have enough text for FAST PATH")
        return
    
    # Test 2: Detect OCR quality
    from app.utils.text_layer_correction import detect_ocr_quality
    
    start = time.time()
    quality = detect_ocr_quality(text_check["text_content"])
    t2 = time.time() - start
    print(f"2️⃣ detect_ocr_quality: {t2:.2f}s")
    print(f"   Result: quality={quality['quality_score']}%, needs_correction={quality['needs_correction']}")
    
    # Test 3: Format summary
    from app.utils.pdf_text_extractor import format_text_layer_summary
    
    summary_text = format_text_layer_summary(
        text_check["text_content"], "test.pdf", 
        text_check.get("page_count", 1), text_check.get("char_count", 0)
    )
    print(f"3️⃣ Summary formatted: {len(summary_text)} chars")
    
    # Test 4: Extract fields with Gemini
    from app.utils.ship_certificate_ai import extract_ship_certificate_fields_from_summary
    
    # Create proper ai_config
    ai_config = {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "api_key": os.environ.get('EMERGENT_LLM_KEY')
    }
    
    start = time.time()
    extracted = await extract_ship_certificate_fields_from_summary(summary_text, "test.pdf", ai_config)
    t4 = time.time() - start
    print(f"4️⃣ extract_fields (Gemini): {t4:.2f}s")
    if extracted:
        print(f"   cert_name: {extracted.get('cert_name', 'N/A')}")
        print(f"   cert_no: {extracted.get('cert_no', 'N/A')}")
    
    # Test 5: Simulate GDrive upload timing
    print(f"\n5️⃣ Google Drive Upload: Testing...")
    
    # Get GDrive config
    db = mongo_db.database
    gdrive_config = await db.company_gdrive_config.find_one({})
    
    if gdrive_config:
        from app.utils.gdrive_helper import upload_file_with_parent_category
        
        # Upload a small text file to test timing
        test_content = b"Test timing file"
        
        start = time.time()
        result = await upload_file_with_parent_category(
            gdrive_config, test_content, "timing_test.txt", 
            "TEST_SHIP", "Class & Flag Cert", "Certificates", "text/plain"
        )
        t5 = time.time() - start
        print(f"   GDrive upload (small file): {t5:.2f}s")
        
        # Test with larger file (the PDF)
        start = time.time()
        result = await upload_file_with_parent_category(
            gdrive_config, file_content, "timing_test.pdf", 
            "TEST_SHIP", "Class & Flag Cert", "Certificates", "application/pdf"
        )
        t6 = time.time() - start
        print(f"   GDrive upload (1MB PDF): {t6:.2f}s")
    else:
        print("   ⚠️ No GDrive config found")
        t5 = t6 = 0
    
    print("\n" + "=" * 60)
    total = t1 + t2 + t4 + t5 + t6
    print(f"📊 TOTAL PROCESSING TIME: {total:.2f}s")
    print("\n💡 Bottleneck Analysis:")
    times = [
        ("1. Text extraction", t1), 
        ("2. Quality check", t2), 
        ("4. Gemini extract", t4),
        ("5. GDrive small", t5),
        ("6. GDrive PDF", t6)
    ]
    times.sort(key=lambda x: x[1], reverse=True)
    for name, t in times:
        pct = (t / total) * 100 if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"   {name}: {t:.2f}s ({pct:.1f}%) {bar}")

if __name__ == "__main__":
    asyncio.run(test_timing())
