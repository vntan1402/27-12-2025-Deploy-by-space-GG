#!/usr/bin/env python3
"""
Direct AI Test for Docking Date Extraction
Test the AI directly with the PM242308 certificate text to see what it returns
"""

import requests
import json
import os
import sys
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

async def test_ai_direct():
    """Test AI directly with the certificate text"""
    
    print("🤖 DIRECT AI TEST FOR DOCKING DATE EXTRACTION")
    print("=" * 60)
    
    # Authenticate and get certificate text
    login_data = {'username': 'admin1', 'password': '123456', 'remember_me': False}
    response = requests.post('https://vesseldocs.preview.emergentagent.com/api/auth/login', json=login_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Get certificate
    cert_response = requests.get('https://vesseldocs.preview.emergentagent.com/api/certificates?ship_id=vesseldocs', headers=headers)
    certificates = cert_response.json()

    pm242308_cert = None
    for cert in certificates:
        if cert.get('cert_no') == 'PM242308':
            pm242308_cert = cert
            break

    if not pm242308_cert:
        print("❌ PM242308 certificate not found")
        return False

    text_content = pm242308_cert.get('text_content', '')
    if not text_content:
        print("❌ No text content found")
        return False

    print(f"✅ Certificate text loaded ({len(text_content)} characters)")
    
    # Show the relevant section
    lines = text_content.split('\n')
    print("\n📄 Relevant section from certificate:")
    for i, line in enumerate(lines):
        if 'bottom took place on' in line.lower() or 'may 05, 2022' in line.lower():
            print(f"Line {i+1}: {line}")
            # Show context
            if i > 0:
                print(f"Line {i}: {lines[i-1]}")
            if i < len(lines) - 1:
                print(f"Line {i+2}: {lines[i+1]}")
    
    # AI Analysis prompt (same as in the backend)
    docking_analysis_prompt = """
You are a maritime certificate analysis expert specializing in docking date extraction from CSSC (Cargo Ship Safety Construction Certificate) documents.

Please analyze this CSSC certificate and extract ALL docking-related dates with high precision.

**CRITICAL MARITIME TERMINOLOGY:**
"Inspections of the outside of the ship's bottom" = DRY DOCKING
"Bottom inspection" = DRY DOCKING
"Hull inspection in dry dock" = DRY DOCKING
These phrases ALWAYS indicate when the ship was in dry dock for inspection/maintenance.

**PRIMARY EXTRACTION TARGETS (HIGHEST PRIORITY):**
1. **"last two inspections of the outside of the ship's bottom took place on [DATE]"**
   → Extract BOTH dates mentioned (these are the 2 most recent dockings)
2. **"bottom inspected on [DATE]"** or **"bottom inspection [DATE]"**
   → Extract as docking date
3. **"outside of ship's bottom inspected [DATE]"**
   → Extract as docking date
4. **"dry dock [DATE]"** or **"docking survey [DATE]"**
   → Extract as docking date

**EXAMPLE PATTERNS TO MATCH:**
- "last two inspections of the outside of the ship's bottom took place on MAY 05, 2022 and NOVEMBER 01, 2020"
  → Extract: MAY 05, 2022 (Last Docking 1) and NOVEMBER 01, 2020 (Last Docking 2)
- "bottom inspection: 15/03/2021"
  → Extract: 15/03/2021
- "inspected on 2022-05-05"
  → Extract: 2022-05-05

**IMPORTANT: HANDLE MULTI-LINE PATTERNS**
The phrase may be split across lines like:
"last two inspections of the outside of the ship's bottom took place on    and"
"MAY 05, 2022 (R)"

**DATE FORMATS TO RECOGNIZE:**
- "MAY 05, 2022" → 05/05/2022
- "NOVEMBER 01, 2020" → 01/11/2020
- "15/03/2021" → 15/03/2021
- "2022-05-05" → 05/05/2022
- "05.05.2022" → 05/05/2022

**IMPORTANT RULES:** 
- ALWAYS extract dates mentioned with "inspections of the outside of the ship's bottom"
- These are CONFIRMED dry docking dates (confidence: high)
- Extract ALL dates found in bottom inspection contexts
- Ignore certificate issue/valid dates UNLESS they're mentioned in bottom inspection context
- Return dates in chronological order (most recent first)
- Look for dates in the lines immediately following the bottom inspection phrase

Please return a JSON response with:
{
  "docking_dates": [
    {
      "date": "DD/MM/YYYY",
      "context": "Brief description of extraction source (e.g., 'inspections of outside of ship bottom')",
      "confidence": "high"
    }
  ],
  "analysis_notes": "Brief explanation of extraction logic used"
}

Certificate content to analyze:
"""
    
    # Use first 4000 characters (same as backend)
    text_to_analyze = text_content[:4000]
    
    print(f"\n🔍 Analyzing first 4000 characters with AI...")
    
    try:
        # Get Emergent LLM key
        EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
        if not EMERGENT_LLM_KEY:
            print("❌ EMERGENT_LLM_KEY not found")
            return False
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id="test_docking_extraction",
            system_message="You are a maritime document analysis expert. Analyze documents and extract certificate information in JSON format."
        )
        
        # Create enhanced prompt with text content
        enhanced_prompt = f"{docking_analysis_prompt}\n\nDOCUMENT TEXT CONTENT:\n{text_to_analyze}"
        
        # Create user message
        user_message = UserMessage(text=enhanced_prompt)
        
        # Get AI response
        print("🤖 Sending request to AI...")
        response = await chat.send_message(user_message)
        
        # Parse response
        response_text = str(response)
        print(f"\n📤 AI Response:")
        print(response_text)
        
        # Clean up response (remove markdown code blocks if present)
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        
        try:
            parsed_response = json.loads(response_text)
            print(f"\n✅ Parsed JSON Response:")
            print(json.dumps(parsed_response, indent=2))
            
            # Check if it found the expected date
            docking_dates = parsed_response.get('docking_dates', [])
            found_may_05_2022 = False
            
            for date_info in docking_dates:
                date_str = date_info.get('date', '')
                if '05/05/2022' in date_str or 'MAY 05, 2022' in date_str or '2022-05-05' in date_str:
                    found_may_05_2022 = True
                    print(f"✅ SUCCESS: AI found expected date: {date_str}")
                    break
            
            if not found_may_05_2022:
                print(f"❌ AI did not find the expected MAY 05, 2022 date")
                print(f"   Found dates: {[d.get('date') for d in docking_dates]}")
            
            return found_may_05_2022
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {response_text}")
            return False
        
    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return False

def main():
    """Main test function"""
    return asyncio.run(test_ai_direct())

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ AI DIRECT TEST PASSED")
    else:
        print("\n❌ AI DIRECT TEST FAILED")