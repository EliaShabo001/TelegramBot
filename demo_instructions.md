# 🎯 Demo Instructions - Telegram Quiz Bot System

## 🚀 Quick Start Guide

### Step 1: Start Both Bots
```bash
python run_bots.py
```

This will start both:
- **Teacher Bot** (for creating quizzes)
- **Student Bot** (@TestStudentCollegeBot - for taking quizzes)

### Step 2: Create a Quiz (Teacher Side)

1. **Find your Teacher Bot** in Telegram (the one with the original token)
2. **Send** `/insertQuestions`
3. **Follow the wizard**:
   ```
   📘 ما اسم المادة أو الموضوع لهذه المجموعة من الأسئلة؟
   → Type: "Mathematics" (or any subject)
   
   ⏱️ ما مدة الاختبار بالدقائق؟
   → Type: "10" (or any number)
   
   📥 كم عدد الأسئلة التي تريد إدخالها؟
   → Type: "2" (for a quick demo)
   
   📝 أرسل نص السؤال رقم 1:
   → Type: "What is 2 + 2?"
   
   📌 أرسل 4 خيارات، كل خيار في رسالة منفصلة. ابدأ بالخيار الأول:
   → Type: "3"
   → Type: "4"  
   → Type: "5"
   → Type: "6"
   
   ✅ أرسل رقم الإجابة الصحيحة من 1 إلى 4:
   → Type: "2" (for option "4")
   
   📝 أرسل نص السؤال رقم 2:
   → Type: "What is 5 × 3?"
   
   📌 أرسل 4 خيارات، كل خيار في رسالة منفصلة. ابدأ بالخيار الأول:
   → Type: "12"
   → Type: "15"
   → Type: "18"
   → Type: "20"
   
   ✅ أرسل رقم الإجابة الصحيحة من 1 إلى 4:
   → Type: "2" (for option "15")
   ```

4. **Get the Quiz Link**: You'll receive something like:
   ```
   ✅ تم إدخال 2 سؤال بنجاح.
   مدة الاختبار: 10 دقيقة
   هذا هو رابط الاختبار الخاص (خاص بشخص واحد فقط):
   https://t.me/TestStudentCollegeBot?start=quiz_abc123-def456-ghi789
   
   يرجى إرسال هذا الرابط للطالب المخصص فقط.
   ```

### Step 3: Take the Quiz (Student Side)

1. **Copy the quiz link** from the teacher bot
2. **Click the link** - it will open @TestStudentCollegeBot
3. **The quiz starts automatically**:
   ```
   🎓 مرحباً بك في اختبار Mathematics
   📊 عدد الأسئلة: 2
   ⏱️ مدة الاختبار: 10 دقيقة
   ⏰ كل سؤال له مهلة زمنية 60 ثانية
   
   🚀 سنبدأ الآن...
   ```

4. **Answer the questions** by clicking the buttons
5. **Get immediate feedback** after each answer
6. **See final results**:
   ```
   ✅ انتهى الاختبار!
   
   📊 النتائج:
   ✔️ الإجابات الصحيحة: 2
   ❌ الإجابات الخاطئة: 0
   📈 النسبة المئوية: 100.0%
   ⏱️ الوقت المستغرق: 1 دقيقة
   
   🎉 تهانينا! لقد نجحت في الاختبار!
   ```

### Step 4: Verify One-Time Use

1. **Try to use the same link again**
2. **You'll get**: "❌ هذا الرابط قد تم استخدامه مسبقاً ولا يمكن استخدامه مرة أخرى."

## 🔍 Additional Features to Test

### View All Quizzes (Teacher)
- Send `/Questions` to the teacher bot
- See all created quizzes with their links

### Edit Existing Questions (Teacher) - NEW FEATURE! 🆕
1. **Send** `/EditQuestion` to the teacher bot
2. **Select Subject**: Choose from available subjects like:
   ```
   📚 Mathematics
   📚 EnglishChapter2
   📚 IronManBook
   ```
3. **Select Question**: Choose which question to edit
4. **Choose Edit Type**:
   - ✏️ Edit question text
   - 🔄 Edit answer options
   - ✅ Change correct answer
5. **Make Changes**: Follow the prompts to update the question
6. **Confirmation**: Get confirmation that changes were saved

### Alternative Quiz Start (Student)
- Instead of clicking the link, you can send:
- `/startquiz quiz_TOKEN` to @TestStudentCollegeBot

### Timer Testing
- When taking a quiz, wait 60 seconds without answering
- The bot will automatically move to the next question

## 🎯 Key Features Demonstrated

✅ **Unique Quiz Links**: Each quiz gets a unique, one-time-use link
✅ **Two-Bot System**: Separate bots for teachers and students  
✅ **Real-time Feedback**: Immediate response to answers
✅ **Timer System**: 60-second limit per question
✅ **Detailed Results**: Comprehensive scoring and feedback
✅ **Link Expiration**: Prevents reuse of quiz links
✅ **Database Integration**: All data stored in Supabase
✅ **Arabic Interface**: User-friendly Arabic messages
✅ **Question Editing**: Edit existing questions, options, and answers 🆕
✅ **Anti-Cheat Protection**: Prevents forwarding and warns against screenshots 🆕

## 🛠️ Troubleshooting

### If the Student Bot doesn't respond:
1. Check if `StudentBot.py` is running
2. Verify the bot token is correct
3. Ensure @TestStudentCollegeBot is accessible

### If quiz links don't work:
1. Check database connection
2. Verify the link format
3. Ensure the token hasn't been used already

### If questions don't save:
1. Check Supabase connection in `db.py`
2. Verify table schemas match the documentation
3. Check for any database errors in the console

## 📱 Bot Usernames

- **Teacher Bot**: Uses the original token (check TelegramBot.py)
- **Student Bot**: @TestStudentCollegeBot

## 🎉 Success Indicators

You'll know everything is working when:
1. ✅ Both bots start without errors
2. ✅ Teacher can create quizzes and get links
3. ✅ Students can click links and take quizzes
4. ✅ Results are displayed correctly
5. ✅ Links expire after one use
6. ✅ Database stores all information properly

Happy testing! 🚀
