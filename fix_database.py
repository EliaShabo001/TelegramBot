#!/usr/bin/env python3
"""
Script to fix existing database entries:
1. Update bot username from YourBotUsername to TestStudentCollegeBot
2. Sync question counts in batches_metadata with actual questions
"""

from db import supabase, get_all_batches, get_actual_question_count_by_batch, update_batch_metadata_question_count

def fix_bot_usernames():
    """Fix bot usernames in telegram links"""
    print("🔧 Fixing bot usernames in telegram links...")
    
    # Get all batch links
    response = supabase.table("batch_links").select("*").execute()
    
    if not response.data:
        print("❗ No batch links found")
        return
    
    fixed_count = 0
    for batch_link in response.data:
        telegram_link = batch_link.get("telegram_link", "")
        
        if "YourBotUsername" in telegram_link:
            new_link = telegram_link.replace("YourBotUsername", "TestStudentCollegeBot")
            
            # Update the link
            supabase.table("batch_links").update({
                "telegram_link": new_link
            }).eq("batch_id", batch_link["batch_id"]).execute()
            
            print(f"✅ Fixed link for batch {batch_link['batch_id']}")
            print(f"   Old: {telegram_link}")
            print(f"   New: {new_link}")
            fixed_count += 1
    
    if fixed_count == 0:
        print("✅ All telegram links already have correct bot username")
    else:
        print(f"✅ Fixed {fixed_count} telegram links")

def sync_question_counts():
    """Sync question counts in batches_metadata with actual questions"""
    print("\n🔧 Syncing question counts...")
    
    batches = get_all_batches()
    
    if not batches:
        print("❗ No batches found")
        return
    
    synced_count = 0
    for batch in batches:
        batch_id = batch['batch_id']
        stored_count = batch['question_count']
        actual_count = get_actual_question_count_by_batch(batch_id)
        
        if stored_count != actual_count:
            update_batch_metadata_question_count(batch_id)
            print(f"✅ Updated batch {batch_id} ({batch.get('subject', 'Unknown')})")
            print(f"   Stored count: {stored_count} → Actual count: {actual_count}")
            synced_count += 1
        else:
            print(f"✓ Batch {batch_id} ({batch.get('subject', 'Unknown')}) - count is correct: {actual_count}")
    
    if synced_count == 0:
        print("✅ All question counts are already in sync")
    else:
        print(f"✅ Synced {synced_count} batch question counts")

def show_current_status():
    """Show current status of batches"""
    print("\n📊 Current batch status:")
    print("=" * 60)
    
    batches = get_all_batches()
    
    if not batches:
        print("❗ No batches found")
        return
    
    for batch in batches:
        batch_id = batch['batch_id']
        subject = batch.get('subject', 'Unknown')
        stored_count = batch['question_count']
        actual_count = get_actual_question_count_by_batch(batch_id)
        telegram_link = batch.get('telegram_link', '')
        
        # Check bot username
        bot_status = "✅ TestStudentCollegeBot" if "TestStudentCollegeBot" in telegram_link else "❌ Wrong bot"
        count_status = "✅ Synced" if stored_count == actual_count else f"❌ {stored_count}→{actual_count}"
        
        print(f"📚 {subject}")
        print(f"   Batch ID: {batch_id}")
        print(f"   Questions: {count_status}")
        print(f"   Bot Username: {bot_status}")
        print(f"   Link: {telegram_link}")
        print()

def main():
    """Run all fixes"""
    print("🛠️ Database Fix Script")
    print("=" * 50)
    
    # Show current status
    show_current_status()
    
    # Fix bot usernames
    fix_bot_usernames()
    
    # Sync question counts
    sync_question_counts()
    
    print("\n" + "=" * 50)
    print("🎉 Database fixes completed!")
    print("\n📋 What was fixed:")
    print("   • Bot usernames in telegram links")
    print("   • Question counts in batch metadata")
    print("\n🚀 You can now use /Questions to see updated information")

if __name__ == "__main__":
    main()
