import telebot
from telebot import types
import threading
from db import load_questions_by_batch, mark_link_used, is_link_used, get_batch_metadata
import time

# Student Bot Token
STUDENT_TOKEN = "8042475385:AAGipEjvwZrxlibKGRtcoQFGYEYJWb9amBE"
student_bot = telebot.TeleBot(STUDENT_TOKEN)

# Store user data for active tests
user_data = {}

def send_anti_cheat_warning(chat_id):
    """Send warning about cheating attempts"""
    warning_message = (
        "🚨 تحذير من نظام مكافحة الغش!\n\n"
        "⚠️ تم رصد محاولة مشاركة أو نسخ محتوى الاختبار\n"
        "🚫 هذا السلوك مخالف لقوانين الاختبار\n"
        "📋 في حالة تكرار المحاولة سيتم إلغاء الاختبار\n\n"
        "✅ يرجى الاستمرار في الاختبار بشكل نزيه"
    )
    student_bot.send_message(chat_id, warning_message, protect_content=True)

def send_question(chat_id, question_index, questions_list):
    """Send a question with multiple choice options to the student"""
    question = questions_list[question_index]
    markup = types.InlineKeyboardMarkup()

    # Create buttons for each option
    for i, option in enumerate(question["options"]):
        callback_data = f"answer_{question_index}_{i}"
        markup.add(types.InlineKeyboardButton(option, callback_data=callback_data))

    # Send question with timer info and content protection
    bot_message = student_bot.send_message(
        chat_id,
        f"📝 السؤال {question_index + 1} من {len(questions_list)}:\n\n"
        f"{question['question']}\n\n"
        f"⏰ لديك 60 ثانية للإجابة\n\n"
        f"🚫 تحذير: ممنوع أخذ لقطة شاشة أو إعادة توجيه الأسئلة",
        reply_markup=markup,
        protect_content=True  # Prevents forwarding
    )

    return bot_message

def start_test(chat_id, questions_list, batch_info):
    """Initialize a new test session for a student"""
    user_data[chat_id] = {
        "current_question": 0,
        "correct": 0,
        "incorrect": 0,
        "questions": questions_list,
        "batch_info": batch_info,
        "start_time": time.time(),
        "timer": None
    }
    
    # Send welcome message with content protection
    student_bot.send_message(
        chat_id,
        f"🎓 مرحباً بك في اختبار {batch_info.get('subject', 'غير محدد')}\n"
        f"📊 عدد الأسئلة: {len(questions_list)}\n"
        f"⏱️ مدة الاختبار: {batch_info.get('duration_minutes', 'غير محدد')} دقيقة\n"
        f"⏰ كل سؤال له مهلة زمنية 60 ثانية\n\n"
        f"🚫 تحذير هام: ممنوع أخذ لقطات شاشة أو إعادة توجيه محتوى الاختبار\n"
        f"📋 أي محاولة للغش ستؤدي إلى إلغاء الاختبار\n\n"
        f"🚀 سنبدأ الآن...",
        protect_content=True
    )
    
    # Start first question
    send_question(chat_id, 0, questions_list)
    start_timer(chat_id)

def start_timer(chat_id):
    """Start 60-second timer for current question"""
    def timeout():
        if chat_id in user_data:
            # Cancel any existing timer
            if user_data[chat_id].get("timer"):
                user_data[chat_id]["timer"].cancel()

            student_bot.send_message(
                chat_id,
                "⏰ انتهى وقت السؤال! ننتقل للسؤال التالي.\n"
                "🚫 تذكير: ممنوع أخذ لقطات شاشة",
                protect_content=True
            )
            user_data[chat_id]["incorrect"] += 1
            move_to_next_question(chat_id)
    
    # Cancel previous timer if exists
    if user_data[chat_id].get("timer"):
        user_data[chat_id]["timer"].cancel()
    
    # Start new timer
    timer = threading.Timer(60.0, timeout)
    timer.start()
    user_data[chat_id]["timer"] = timer

def move_to_next_question(chat_id):
    """Move to the next question or finish test"""
    if chat_id not in user_data:
        return
    
    user_data[chat_id]["current_question"] += 1
    next_q = user_data[chat_id]["current_question"]
    questions_list = user_data[chat_id]["questions"]
    
    if next_q < len(questions_list):
        send_question(chat_id, next_q, questions_list)
        start_timer(chat_id)
    else:
        finish_test(chat_id)

def finish_test(chat_id):
    """Complete the test and show results"""
    data = user_data.pop(chat_id, None)
    if not data:
        return
    
    # Cancel timer if exists
    if data.get("timer"):
        data["timer"].cancel()
    
    # Calculate results
    total_questions = len(data["questions"])
    correct = data["correct"]
    incorrect = data["incorrect"]
    percentage = (correct / total_questions) * 100 if total_questions > 0 else 0
    
    # Calculate time taken
    time_taken = int((time.time() - data["start_time"]) / 60)  # in minutes
    
    # Send results with content protection
    result_message = (
        f"✅ انتهى الاختبار!\n\n"
        f"📊 النتائج:\n"
        f"✔️ الإجابات الصحيحة: {correct}\n"
        f"❌ الإجابات الخاطئة: {incorrect}\n"
        f"📈 النسبة المئوية: {percentage:.1f}%\n"
        f"⏱️ الوقت المستغرق: {time_taken} دقيقة\n\n"
    )

    if percentage >= 70:
        result_message += "🎉 تهانينا! لقد نجحت في الاختبار!"
    elif percentage >= 50:
        result_message += "👍 أداء جيد! يمكنك تحسين النتيجة أكثر."
    else:
        result_message += "📚 يُنصح بمراجعة المادة والمحاولة مرة أخرى."

    result_message += "\n\n🚫 هذه النتائج سرية وممنوع مشاركتها"

    student_bot.send_message(chat_id, result_message, protect_content=True)

@student_bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command with quiz token"""
    args = message.text.split()
    
    if len(args) == 2 and args[1].startswith("quiz_"):
        # Extract token from the start parameter
        token = args[1][len("quiz_"):]
        
        # Check if link is already used
        if is_link_used(token):
            student_bot.send_message(
                message.chat.id, 
                "❌ هذا الرابط قد تم استخدامه مسبقاً ولا يمكن استخدامه مرة أخرى.\n"
                "يرجى الحصول على رابط جديد من المعلم."
            )
            return
        
        # Load questions for this batch
        questions_batch = load_questions_by_batch(token)
        if not questions_batch:
            student_bot.send_message(
                message.chat.id, 
                "❌ الرابط غير صحيح أو انتهت صلاحية الاختبار.\n"
                "يرجى التأكد من الرابط أو الحصول على رابط جديد من المعلم."
            )
            return
        
        # Mark link as used
        mark_link_used(token)

        # Get batch info (subject, duration, etc.)
        batch_metadata = get_batch_metadata(token)
        batch_info = {
            "subject": batch_metadata.get("subject", "غير محدد") if batch_metadata else questions_batch[0].get("subject", "غير محدد"),
            "duration_minutes": batch_metadata.get("duration_minutes", 15) if batch_metadata else 15
        }
        
        # Start the test
        start_test(message.chat.id, questions_batch, batch_info)
        
    else:
        # No token provided - show welcome message
        student_bot.send_message(
            message.chat.id,
            "🎓 مرحباً بك في بوت اختبارات الطلاب!\n\n"
            "📝 لبدء الاختبار، يجب أن تحصل على رابط خاص من معلمك.\n"
            "🔗 الرابط سيكون بالشكل التالي:\n"
            "https://t.me/TestStudentCollegeBot?start=quiz_XXXXXX\n\n"
            "💡 إذا كان لديك رابط، اضغط عليه مباشرة أو أرسل الأمر:\n"
            "/startquiz quiz_XXXXXX"
        )

@student_bot.message_handler(commands=['startquiz'])
def handle_start_quiz(message):
    """Alternative way to start quiz with token"""
    args = message.text.split()
    if len(args) != 2:
        student_bot.send_message(
            message.chat.id, 
            "❗ يرجى إرسال الأمر مع رمز الاختبار، مثال:\n"
            "/startquiz quiz_TOKEN_HERE"
        )
        return

    token = args[1]
    if token.startswith("quiz_"):
        token = token[len("quiz_"):]
    
    # Check if link is already used
    if is_link_used(token):
        student_bot.send_message(
            message.chat.id, 
            "❌ هذا الرابط قد تم استخدامه مسبقاً ولا يمكن استخدامه مرة أخرى."
        )
        return

    # Load questions for this batch
    questions_batch = load_questions_by_batch(token)
    if not questions_batch:
        student_bot.send_message(
            message.chat.id, 
            "❌ الرابط غير صحيح أو انتهت صلاحية الاختبار."
        )
        return

    # Mark link as used
    mark_link_used(token)

    # Get batch info
    batch_metadata = get_batch_metadata(token)
    batch_info = {
        "subject": batch_metadata.get("subject", "غير محدد") if batch_metadata else questions_batch[0].get("subject", "غير محدد"),
        "duration_minutes": batch_metadata.get("duration_minutes", 15) if batch_metadata else 15
    }
    
    # Start the test
    start_test(message.chat.id, questions_batch, batch_info)

@student_bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(call):
    """Handle student's answer selection"""
    chat_id = call.message.chat.id
    
    # Check if user has an active test
    if chat_id not in user_data:
        student_bot.answer_callback_query(
            call.id, 
            "❌ لا يوجد اختبار نشط. يرجى بدء اختبار جديد."
        )
        return

    # Cancel the timer
    if user_data[chat_id].get("timer"):
        user_data[chat_id]["timer"].cancel()

    try:
        # Parse callback data: answer_questionIndex_optionIndex
        _, question_index, chosen_option = call.data.split("_")
        question_index = int(question_index)
        chosen_option = int(chosen_option)
    except (ValueError, IndexError):
        student_bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
        return

    # Get question data
    questions_list = user_data[chat_id]["questions"]
    question = questions_list[question_index]
    correct_answer = question["answer"]
    chosen_text = question["options"][chosen_option]

    # Check if answer is correct
    if chosen_text == correct_answer:
        user_data[chat_id]["correct"] += 1
        student_bot.answer_callback_query(call.id, "✅ إجابة صحيحة!")
        student_bot.send_message(chat_id, "✅ إجابة صحيحة! أحسنت.", protect_content=True)
    else:
        user_data[chat_id]["incorrect"] += 1
        student_bot.answer_callback_query(call.id, "❌ إجابة خاطئة")
        student_bot.send_message(
            chat_id,
            f"❌ إجابة خاطئة.\n"
            f"💡 الإجابة الصحيحة هي: {correct_answer}\n"
            f"🚫 ممنوع مشاركة الإجابات",
            protect_content=True
        )

    # Move to next question
    move_to_next_question(chat_id)

@student_bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 'audio', 'sticker'])
def handle_other_messages(message):
    """Handle any other messages during test and detect potential cheating"""
    chat_id = message.chat.id

    # Check for forwarded messages (potential cheating)
    if message.forward_from or message.forward_from_chat:
        send_anti_cheat_warning(chat_id)
        return

    # Check for suspicious commands or keywords
    if message.content_type == 'text':
        text = message.text.lower()
        suspicious_keywords = ['screenshot', 'لقطة', 'صورة', 'forward', 'إعادة توجيه', 'نسخ', 'copy']

        if any(keyword in text for keyword in suspicious_keywords):
            send_anti_cheat_warning(chat_id)
            return

    # Check for media content during test (potential screenshots)
    if message.content_type in ['photo', 'document', 'video'] and chat_id in user_data:
        student_bot.send_message(
            chat_id,
            "🚫 ممنوع إرسال الصور أو الملفات أثناء الاختبار!\n"
            "📝 يرجى الإجابة على السؤال الحالي باستخدام الأزرار المتاحة.",
            protect_content=True
        )
        return

    if chat_id in user_data:
        student_bot.send_message(
            chat_id,
            "📝 يرجى الإجابة على السؤال الحالي باستخدام الأزرار المتاحة.\n"
            "🚫 تذكير: ممنوع أخذ لقطات شاشة أو مشاركة المحتوى",
            protect_content=True
        )
    else:
        student_bot.send_message(
            chat_id,
            "🎓 مرحباً! لبدء اختبار جديد، يرجى استخدام الرابط الذي حصلت عليه من معلمك.\n"
            "أو استخدم الأمر /start\n\n"
            "🚫 تذكير: جميع محتويات الاختبار محمية ضد النسخ والمشاركة",
            protect_content=True
        )

if __name__ == "__main__":
    print("🤖 Student Bot is starting...")
    print("Bot username: @TestStudentCollegeBot")
    student_bot.polling(none_stop=True)
