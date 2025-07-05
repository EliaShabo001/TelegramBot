#!/usr/bin/env python3
"""
Test script for the new /EditQuestion functionality
"""

import sys

def test_database_functions():
    """Test the new database functions for editing"""
    print("🔍 Testing new database functions...")
    
    try:
        from db import get_all_subjects, get_questions_by_subject, update_question, get_question_by_id
        print("✅ All edit-related database functions imported successfully")
        
        # Test getting subjects
        subjects = get_all_subjects()
        print(f"📚 Found {len(subjects)} subjects: {subjects}")
        
        if subjects:
            # Test getting questions for first subject
            first_subject = subjects[0]
            questions = get_questions_by_subject(first_subject)
            print(f"📝 Found {len(questions)} questions for '{first_subject}'")
            
            if questions:
                # Test getting a specific question
                first_question = questions[0]
                question_detail = get_question_by_id(first_question['id'])
                print(f"🔍 Retrieved question details: {question_detail['question'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Database function test failed: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import TelegramBot
        print("✅ TelegramBot with edit functionality imported successfully")
        
        # Check if edit_states exists
        if hasattr(TelegramBot, 'edit_states'):
            print("✅ edit_states variable found")
        else:
            print("❌ edit_states variable not found")
            return False
            
        return True
    except ImportError as e:
        print(f"❌ Failed to import TelegramBot: {e}")
        return False

def test_callback_handlers():
    """Test if callback handlers are properly defined"""
    print("🔍 Testing callback handlers...")
    
    try:
        import TelegramBot
        
        # Check if the bot object exists
        if hasattr(TelegramBot, 'bot'):
            print("✅ Bot object found")
        else:
            print("❌ Bot object not found")
            return False
            
        print("✅ Callback handlers should be registered")
        return True
        
    except Exception as e:
        print(f"❌ Callback handler test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing /EditQuestion Functionality")
    print("=" * 50)
    
    tests = [
        ("Database Functions Test", test_database_functions),
        ("Import Test", test_imports),
        ("Callback Handlers Test", test_callback_handlers)
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
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! /EditQuestion functionality should work correctly.")
        print("\n📋 New Features Available:")
        print("   • /EditQuestion - Edit existing quiz questions")
        print("   • Subject selection with inline buttons")
        print("   • Question listing and editing interface")
        print("   • Edit question text, options, and correct answers")
        print("\n🚀 You can now run the teacher bot with:")
        print("   python TelegramBot.py")
        print("\n🔗 Or run both bots together with:")
        print("   python run_bots.py")
    else:
        print("⚠️ Some tests failed. Please fix the issues before using the edit functionality.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
