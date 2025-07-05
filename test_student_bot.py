#!/usr/bin/env python3
"""
Test script for the Student Bot
This script helps verify that the student bot is working correctly
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import telebot
        print("✅ telebot imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import telebot: {e}")
        return False
    
    try:
        from db import load_questions_by_batch, mark_link_used, is_link_used, get_batch_metadata
        print("✅ Database functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database functions: {e}")
        return False
    
    try:
        import StudentBot
        print("✅ StudentBot module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import StudentBot: {e}")
        return False
    
    return True

def test_bot_token():
    """Test if the bot token is valid format"""
    print("\n🔑 Testing bot token...")
    
    from StudentBot import STUDENT_TOKEN
    
    if not STUDENT_TOKEN:
        print("❌ Bot token is empty")
        return False
    
    if not STUDENT_TOKEN.count(':') == 1:
        print("❌ Bot token format is invalid")
        return False
    
    bot_id, token_part = STUDENT_TOKEN.split(':')
    
    if not bot_id.isdigit():
        print("❌ Bot ID part is not numeric")
        return False
    
    if len(token_part) < 35:
        print("❌ Token part seems too short")
        return False
    
    print(f"✅ Bot token format is valid (Bot ID: {bot_id})")
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from db import supabase
        
        # Try a simple query
        response = supabase.table("batch_links").select("batch_id").limit(1).execute()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Student Bot Setup")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Bot Token Test", test_bot_token),
        ("Database Test", test_database_connection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Student bot should work correctly.")
        print("\n🚀 You can now run the student bot with:")
        print("   python StudentBot.py")
        print("\n🔗 Or run both bots together with:")
        print("   python run_bots.py")
    else:
        print("⚠️ Some tests failed. Please fix the issues before running the bot.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
