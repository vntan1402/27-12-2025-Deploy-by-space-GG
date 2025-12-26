"""Test timing for Certificate FAST PATH"""
import asyncio
import time
import base64
import os
import sys
sys.path.insert(0, '/app/backend')

from app.db.mongodb import mongo_db

async def test_timing():
    # Connect to DB
    await mongo_db.connect()
    
    # Find a test PDF with text layer
    test_file = "/app/backend/tests/test_files/sample_cert.pdf"
    
    # Create a simple test file if not exists
    if not os.path.exists(test_file):
        os.makedirs("/app/backend/tests/test_files", exist_ok=True)
        # Create a simple PDF-like content for testing
        print("❌ No test file found. Please upload a real PDF for timing test.")
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
    
    # Test 3: AI Text Correction (if needed)
    if quality["needs_correction"]:
        from app.utils.text_layer_correction import correct_text_layer_with_ai
        
        # Get AI config
        ai_config = await mongo_db.find_one("ai_configs", {})
        
        start = time.time()
        correction = await correct_text_layer_with_ai(
            text_check["text_content"], "test.pdf", ai_config
        )
        t3 = time.time() - start
        print(f"3️⃣ correct_text_layer_with_ai: {t3:.2f}s")
    else:
        print(f"3️⃣ AI Text Correction: SKIPPED (quality good)")
        t3 = 0
    
    # Test 4: Extract fields with Gemini
    from app.utils.ship_certificate_ai import extract_ship_certificate_fields_from_summary
    from app.utils.pdf_text_extractor import format_text_layer_summary
    
    summary_text = format_text_layer_summary(
        text_check["text_content"], "test.pdf", 
        text_check.get("page_count", 1), text_check.get("char_count", 0)
    )
    
    ai_config = await mongo_db.find_one("ai_configs", {})
    
    start = time.time()
    extracted = await extract_ship_certificate_fields_from_summary(summary_text, "test.pdf", ai_config)
    t4 = time.time() - start
    print(f"4️⃣ extract_fields (Gemini): {t4:.2f}s")
    print(f"   Extracted: {list(extracted.keys()) if extracted else 'None'}")
    
    # Test 5: Google Drive upload (simulated - need real config)
    print(f"5️⃣ Google Drive Upload: ~10-30s (depends on file size and network)")
    
    print("\n" + "=" * 60)
    print(f"📊 TOTAL ANALYSIS TIME (without GDrive): {t1 + t2 + t3 + t4:.2f}s")
    print("\n💡 Bottleneck Analysis:")
    times = [("quick_check", t1), ("detect_quality", t2), ("ai_correction", t3), ("gemini_extract", t4)]
    times.sort(key=lambda x: x[1], reverse=True)
    for name, t in times:
        pct = (t / (t1 + t2 + t3 + t4)) * 100 if (t1 + t2 + t3 + t4) > 0 else 0
        print(f"   {name}: {t:.2f}s ({pct:.1f}%)")

if __name__ == "__main__":
    asyncio.run(test_timing())
