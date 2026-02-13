#!/usr/bin/env python3
"""
Debug script for the traffic light classification issue
Run from backend directory: python debug_classification.py
"""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_text_classification():
    """Test text classification with the exact input from your logs"""
    
    print("=" * 60)
    print("🔍 DEBUGGING TEXT CLASSIFICATION")
    print("=" * 60)
    
    title = "Traffic Light is broken"
    description = "The light is broken which is causing accidents left,right,center. Please help fix.It has been broken by 6pm yesterday"
    
    print(f"\n📝 Input:")
    print(f"   Title: {title}")
    print(f"   Description: {description}")
    
    # Step 1: Test Ollama connection
    print("\n" + "=" * 60)
    print("STEP 1: Testing Ollama Connection")
    print("=" * 60)
    
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        
        if resp.status_code == 200:
            print("✅ Ollama is running")
            models = resp.json().get("models", [])
            print(f"   Available models: {[m['name'] for m in models]}")
        else:
            print(f"❌ Ollama returned status {resp.status_code}")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ CRITICAL: Cannot connect to Ollama")
        print("   Solution: Run 'ollama serve' in another terminal")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 2: Test intent extraction
    print("\n" + "=" * 60)
    print("STEP 2: Testing Intent Extraction")
    print("=" * 60)
    
    try:
        from ml.intent_extractor import extract_intent_or_invalid
        
        print("Calling extract_intent_or_invalid()...")
        intent = extract_intent_or_invalid(title, description)
        
        print(f"\n📤 Result: '{intent}'")
        
        if intent is None:
            print("❌ CRITICAL: Intent extraction returned None")
            print("   This means Ollama API call failed")
            return
        elif intent.upper() == "INVALID":
            print("⚠️  WARNING: Input classified as INVALID")
            print("   This is wrong - traffic light is a valid civic issue")
            return
        else:
            print("✅ Intent extracted successfully")
            
    except ImportError as e:
        print(f"❌ Cannot import intent_extractor: {e}")
        print("   Make sure intent_extractor.py exists in backend/ml/")
        return
    except Exception as e:
        print(f"❌ Error during intent extraction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test text routing
    print("\n" + "=" * 60)
    print("STEP 3: Testing Text Router")
    print("=" * 60)
    
    try:
        from ml.text_router import route_issue
        
        print("Calling route_issue()...")
        result = route_issue(title, description)
        
        print(f"\n📤 Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Department: {result.get('department')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Reason: {result.get('reason')}")
        
        if result.get('status') == 'ROUTED':
            print(f"\n✅ Text routing successful")
            print(f"   Routed to: {result['department']}")
        elif result.get('status') == 'OUT_OF_SCOPE':
            print(f"\n⚠️  Text routing uncertain")
            print(f"   Reason: {result['reason']}")
        else:
            print(f"\n❌ Text routing failed: {result.get('status')}")
            
    except ImportError as e:
        print(f"❌ Cannot import text_router: {e}")
        print("   Make sure text_router.py exists in backend/ml/")
        return
    except Exception as e:
        print(f"❌ Error during text routing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test hybrid classification
    print("\n" + "=" * 60)
    print("STEP 4: Testing Hybrid Classification")
    print("=" * 60)
    
    try:
        from ml.hybrid_classifier import hybrid_classify
        
        # Simulate the image result from your logs
        image_department = "Public Works Department"
        image_confidence = 0.648
        
        print(f"Image result: {image_department} (confidence: {image_confidence})")
        print(f"Text input: '{title}' / '{description[:50]}...'")
        print("\nCalling hybrid_classify()...")
        
        result = hybrid_classify(
            image_department=image_department,
            image_confidence=image_confidence,
            title=title,
            description=description,
            image_threshold=0.45
        )
        
        print(f"\n📤 Result:")
        print(f"   Method: {result.get('method')}")
        print(f"   Final Department: {result.get('final_department')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Reason: {result.get('reason')}")
        
        # Check if method is IMAGE_ONLY
        if result.get('method') == 'IMAGE_ONLY':
            print(f"\n⚠️  WARNING: Hybrid classifier used IMAGE_ONLY")
            print(f"   This means text classification didn't work properly")
            print(f"   Checking text_result...")
            
            if 'text_result' in result:
                text_result = result['text_result']
                print(f"   Text status: {text_result.get('status')}")
                print(f"   Text reason: {text_result.get('reason')}")
        
        print("\n" + "=" * 60)
        print("EXPECTED vs ACTUAL")
        print("=" * 60)
        print(f"Expected department: Traffic Department")
        print(f"Actual department: {result.get('final_department')}")
        
        if result.get('final_department') == 'Traffic Department':
            print("✅ CORRECT!")
        else:
            print("❌ WRONG!")
            
    except ImportError as e:
        print(f"❌ Cannot import hybrid_classifier: {e}")
        return
    except Exception as e:
        print(f"❌ Error during hybrid classification: {e}")
        import traceback
        traceback.print_exc()
        return


def test_department_mapping():
    """Check if the department mapping is correct"""
    
    print("\n" + "=" * 60)
    print("🔍 DEBUGGING DEPARTMENT MAPPING")
    print("=" * 60)
    
    try:
        from ml.text_router import DEPARTMENTS, DEPT_NAME_MAPPING
        
        print("\nDepartment Definitions:")
        for idx, desc in DEPARTMENTS.items():
            mapped_name = DEPT_NAME_MAPPING[idx]
            print(f"   {idx}: {desc}")
            print(f"      → Maps to: {mapped_name}")
        
        print("\n⚠️  IMPORTANT NOTE:")
        print("   Traffic Department issues should map to 'Traffic Department'")
        print("   Garbage/waste issues should map to 'Sanitation Department'")
        
    except ImportError as e:
        print(f"❌ Cannot import text_router: {e}")


if __name__ == "__main__":
    print("\n🚀 Starting Classification Debug\n")
    
    # First check department mapping
    test_department_mapping()
    
    # Then test classification
    test_text_classification()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG COMPLETE")
    print("=" * 60)
    print("\nIf you see 'IMAGE_ONLY' method, the text classification isn't working.")
    print("Common causes:")
    print("1. Ollama not running → Run 'ollama serve'")
    print("2. Model not pulled → Run 'ollama pull qwen2.5:1.5b-instruct'")
    print("3. Intent extraction timing out → Check Ollama logs")
    print("4. Import errors → Check all 3 new .py files exist in ml/")