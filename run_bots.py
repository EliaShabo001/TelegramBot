#!/usr/bin/env python3
"""
Script to run both Teacher Bot and Student Bot simultaneously
"""

import threading
import time
import sys

def run_teacher_bot():
    """Run the teacher bot"""
    try:
        print("🎓 Starting Teacher Bot...")
        import TelegramBot
        print("✅ Teacher Bot started successfully!")
    except Exception as e:
        print(f"❌ Error starting Teacher Bot: {e}")

def run_student_bot():
    """Run the student bot"""
    try:
        print("🎒 Starting Student Bot...")
        import StudentBot
        print("✅ Student Bot started successfully!")
    except Exception as e:
        print(f"❌ Error starting Student Bot: {e}")

def main():
    print("🤖 Starting Quiz Bot System...")
    print("=" * 50)
    
    # Create threads for both bots
    teacher_thread = threading.Thread(target=run_teacher_bot, daemon=True)
    student_thread = threading.Thread(target=run_student_bot, daemon=True)
    
    # Start both bots
    teacher_thread.start()
    time.sleep(2)  # Small delay between starting bots
    student_thread.start()
    
    print("\n🚀 Both bots are running!")
    print("📋 Teacher Bot: Create and manage quizzes")
    print("🎓 Student Bot (@TestStudentCollegeBot): Take quizzes")
    print("\nPress Ctrl+C to stop both bots...")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bots...")
        print("👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
