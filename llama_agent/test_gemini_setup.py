#!/usr/bin/env python3
"""
Test script for Gemini Odoo Agent setup
Tests all components without requiring actual API calls
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing package imports...")
    
    try:
        import google.generativeai as genai
        print("  ✅ google-generativeai")
    except ImportError:
        print("  ❌ google-generativeai - Run: uv pip install google-generativeai --python .venv/bin/python")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✅ python-dotenv")
    except ImportError:
        print("  ❌ python-dotenv - Run: uv pip install python-dotenv --python .venv/bin/python")
        return False
    
    try:
        from rich.console import Console
        print("  ✅ rich")
    except ImportError:
        print("  ❌ rich - Run: uv pip install rich --python .venv/bin/python")
        return False
    
    try:
        from flask import Flask
        print("  ✅ flask")
    except ImportError:
        print("  ❌ flask - Run: uv pip install flask --python .venv/bin/python")
        return False
    
    try:
        from flask_cors import CORS
        print("  ✅ flask-cors")
    except ImportError:
        print("  ❌ flask-cors - Run: uv pip install flask-cors --python .venv/bin/python")
        return False
    
    return True

def test_env_file():
    """Test .env file configuration"""
    print("\n🔧 Testing .env configuration...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("  ❌ .env file not found")
        print("  💡 Copy .env.example to .env and configure it")
        return False
    
    print("  ✅ .env file exists")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("  ⚠️  GEMINI_API_KEY not configured")
        print("  💡 Get your API key from https://aistudio.google.com/app/apikey")
        print("  💡 Then update GEMINI_API_KEY in .env file")
    else:
        print("  ✅ GEMINI_API_KEY configured")
    
    addons_path = Path(os.getenv('ODOO_ADDONS_PATH', './test_modules'))
    if not addons_path.exists():
        print(f"  ⚠️  Creating addons directory: {addons_path}")
        addons_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ Addons path: {addons_path}")
    
    return True

def test_agent_import():
    """Test if the agent can be imported"""
    print("\n🤖 Testing agent import...")
    
    try:
        # Test if we can import the agent (this will fail if API key is not set, but that's expected)
        sys.path.insert(0, str(Path.cwd()))
        
        # We'll just test the import, not initialization
        from gemini_odoo_agent import GeminiOdooAgent, FileChange
        print("  ✅ GeminiOdooAgent class imported successfully")
        
        from web_ui import app
        print("  ✅ Web UI Flask app imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        # Expected if API key is not set
        if "GEMINI_API_KEY" in str(e):
            print("  ✅ Agent import works (API key needed for initialization)")
            return True
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'gemini_odoo_agent.py',
        'web_ui.py',
        '.env.example',
        'GEMINI_AGENT_README.md'
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def test_sample_module():
    """Test if sample module exists"""
    print("\n📦 Testing sample module...")
    
    sample_path = Path('test_modules/sample_inventory')
    if sample_path.exists():
        print("  ✅ Sample module exists")
        
        # Check for key files
        key_files = ['__manifest__.py', '__init__.py', 'models/product_template.py']
        for file_path in key_files:
            full_path = sample_path / file_path
            if full_path.exists():
                print(f"    ✅ {file_path}")
            else:
                print(f"    ⚠️  {file_path} - Missing")
    else:
        print("  ⚠️  Sample module not found (will be created by quick_test.py)")
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP TEST COMPLETE")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("\n1. 🔑 Configure your Gemini API key:")
    print("   • Go to https://aistudio.google.com/app/apikey")
    print("   • Create a new API key")
    print("   • Edit .env file and replace 'your_api_key_here' with your actual key")
    
    print("\n2. 🧪 Test the terminal interface:")
    print("   python gemini_odoo_agent.py")
    
    print("\n3. 🌐 Test the web interface:")
    print("   python web_ui.py")
    print("   Then open http://localhost:5000 in your browser")
    
    print("\n4. 📚 Read the documentation:")
    print("   cat GEMINI_AGENT_README.md")
    
    print("\n5. 🚀 Create your first module:")
    print("   Use either interface to create a test module")
    
    print("\n" + "="*60)
    print("🤖 Happy AI-Powered Odoo Development!")
    print("="*60)

def main():
    """Run all tests"""
    print("🔍 Gemini Odoo Agent Setup Test")
    print("="*40)
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Configuration", test_env_file),
        ("Agent Import", test_agent_import),
        ("File Structure", test_file_structure),
        ("Sample Module", test_sample_module)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*40)
    print("📊 TEST SUMMARY")
    print("="*40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Setup is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print_next_steps()

if __name__ == "__main__":
    main()