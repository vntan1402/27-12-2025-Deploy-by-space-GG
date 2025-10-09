#!/usr/bin/env python3

"""
Test script to reproduce and fix the AttributeError: 'str' object has no attribute 'file_contents'
"""

import asyncio
import sys
import os
import json

# Add the backend directory to sys.path to import our modules
sys.path.insert(0, '/app/backend')

from emergentintegrations.llm.chat import LlmChat, UserMessage

def get_emergent_llm_key():
    """Get Emergent LLM key for AI integrations"""
    return 'sk-emergent-eEe35Fb1b449940199'

def create_test_prompt():
    """Create a simple test prompt for passport extraction"""
    return """You are an AI specialized in structured information extraction from maritime and identity documents.

Extract passport information from this text: "PASSPORT TYPE: P COUNTRY: VNM SURNAME: TRAN GIVEN NAMES: TRONG TOAN SEX: M DATE OF BIRTH: 17 JAN 1987 PLACE OF BIRTH: HAI PHONG NATIONALITY: VIETNAMESE PASSPORT NO: C9329057 DATE OF ISSUE: 17 JAN 1987 DATE OF EXPIRY: 17 JAN 1997"

Return only valid JSON:
{
  "Passport_Number": "C9329057",
  "Surname": "TRAN",
  "Given_Names": "TRONG TOAN",
  "Sex": "M",
  "Date_of_Birth": "1987-01-17",
  "Place_of_Birth": "HAI PHONG",
  "Nationality": "VIETNAMESE",
  "Date_of_Issue": "1987-01-17",
  "Date_of_Expiry": "1997-01-17"
}
"""

async def test_ai_extraction():
    """Test the AI extraction to reproduce the AttributeError"""
    try:
        print("🚀 Testing LlmChat AI extraction...")
        
        # Create chat instance with Emergent key
        emergent_key = get_emergent_llm_key()
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"test_extraction_123456",
            system_message="You are a maritime document analysis expert."
        ).with_model("google", "gemini-2.0-flash-exp")
        
        # Send extraction prompt to AI
        prompt = create_test_prompt()
        print(f"📤 Sending test prompt to Gemini...")
        print(f"📏 Prompt length: {len(prompt)} characters")
        
        # Create UserMessage object for the prompt (FIX APPLIED)
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        print(f"📥 Received AI response type: {type(ai_response)}")
        print(f"🔍 AI response dir: {dir(ai_response)}")
        
        # Test the exact code from server.py to see if it fails
        if ai_response:
            print("🔍 Checking response attributes...")
            print(f"   hasattr(ai_response, 'file_contents'): {hasattr(ai_response, 'file_contents')}")
            print(f"   hasattr(ai_response, 'content'): {hasattr(ai_response, 'content')}")
            print(f"   isinstance(ai_response, str): {isinstance(ai_response, str)}")
            
            # This is the exact logic from server.py lines 10655-10667
            if hasattr(ai_response, 'file_contents'):
                content = ai_response.file_contents.strip()
                print(f"🔍 AI response from file_contents: {len(content)} characters")
            elif hasattr(ai_response, 'content'):
                content = ai_response.content.strip()
                print(f"🔍 AI response from content: {len(content)} characters")
            elif isinstance(ai_response, str):
                content = ai_response.strip()
                print(f"🔍 AI response as string: {len(content)} characters")
            else:
                # Fallback: convert to string
                content = str(ai_response).strip()
                print(f"🔍 AI response converted to string: {len(content)} characters")
            
            print(f"📝 AI response preview: {content[:200]}...")
            
            # Try to parse JSON
            try:
                extracted_data = json.loads(content)
                print("✅ JSON parsing successful!")
                print(f"📋 Extracted fields: {list(extracted_data.keys())}")
                return extracted_data
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON parsing failed: {json_error}")
                print(f"Raw content: {content}")
                return None
                
        else:
            print("❌ No response from AI")
            return None
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_ai_extraction())
    if result:
        print("🎉 Test successful!")
    else:
        print("❌ Test failed!")