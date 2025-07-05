import telebot
from telebot import types
import threading
from db import load_questions, save_question, save_batch_link, load_questions_by_batch, mark_link_used, is_link_used, get_all_batches, get_all_subjects, get_questions_by_subject, update_question, get_question_by_id, get_actual_question_count_by_batch, update_batch_metadata_question_count, reactivate_batch_link, get_batch_info_by_id
from datetime import datetime
import uuid

TOKEN = "7432401952:AAHm4Sez4z8_zzwmo3A_k2eY-gcYDn8j0Z8"
bot = telebot.TeleBot(TOKEN)

questions = load_questions()
user_data = {}
insert_states = {}
active_tests = {}
edit_states = {}

def generate_link_token():
    return str(uuid.uuid4())

def send_question(chat_id, question_index, questions_list):
    question = questions_list[question_index]
    markup = types.InlineKeyboardMarkup()
    for i, option in enumerate(question["options"]):
        callback_data = f"{question_index}:{i}"
        markup.add(types.InlineKeyboardButton(option, callback_data=callback_data))
    bot.send_message(chat_id, f"السؤال {question_index + 1}:\n{question['question']}", reply_markup=markup)

def start_test(chat_id, questions_list):
    user_data[chat_id] = {
        "current_question": 0,
        "correct": 0,
        "incorrect": 0,
        "questions": questions_list
    }
    send_question(chat_id, 0, questions_list)
    start_timer(chat_id)

def start_timer(chat_id):
    def timeout():
        if chat_id in user_data:
            bot.send_message(chat_id, "⏰ انتهى وقت السؤال! ننتقل للسؤال التالي.")
            user_data[chat_id]["incorrect"] += 1
            user_data[chat_id]["current_question"] += 1
            next_q = user_data[chat_id]["current_question"]
            questions_list = user_data[chat_id]["questions"]
            if next_q < len(questions_list):
                send_question(chat_id, next_q, questions_list)
                start_timer(chat_id)
            else:
                finish_test(chat_id)
    timer = threading.Timer(60, timeout)
    timer.start()
    user_data[chat_id]["timer"] = timer

def finish_test(chat_id):
    data = user_data.pop(chat_id, None)
    if data:
        bot.send_message(chat_id, f"✅ انتهى الاختبار!\nالصحيحة: {data['correct']}\nالخاطئة: {data['incorrect']}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    args = message.text.split()
    if len(args) == 2 and args[1].startswith("quiz_"):
        token = args[1][len("quiz_"):]
        if is_link_used(token):
            bot.send_message(message.chat.id, "❌ هذا الرابط قد تم استخدامه مسبقاً ولا يمكن استخدامه مرة أخرى.")
            return
        questions_batch = load_questions_by_batch(token)
        if not questions_batch:
            bot.send_message(message.chat.id, "❌ الرابط غير صحيح أو انتهت صلاحية الاختبار.")
            return
        mark_link_used(token)
        start_test(message.chat.id, questions_batch)
    else:
        # No token, regular start message
        welcome_message = (
            "🎓 *مرحباً بك في نظام إدارة الاختبارات!*\n\n"
            "📋 *قائمة الأوامر المتاحة:*\n\n"

            "🔹 *إدارة الأسئلة:*\n"
            "   📝 /insertQuestions - إنشاء اختبار جديد\n"
            "   ✏️ /EditQuestion - تعديل الأسئلة الموجودة\n"
            "   📊 /Questions - عرض جميع الاختبارات\n\n"

            "🔹 *إدارة الروابط:*\n"
            "   🔄 /ActiveQuestionLinkAgain - إعادة تفعيل الروابط المستخدمة\n\n"

            "🔹 *اختبار النظام:*\n"
            "   🧪 /test - تجربة الاختبار (للمعلم)\n"
            "   🎯 /startquiz quiz\\_رمز - دخول اختبار برابط مباشر\n\n"

            "💡 *نصيحة:* ابدأ بإنشاء اختبار جديد باستخدام /insertQuestions"
        )

        bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')

@bot.message_handler(commands=['startquiz'])
def handle_start_quiz(message):
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, "❗ يرجى إرسال الأمر مع الرابط الخاص، مثال:\n/startquiz quiz_TOKEN_HERE")
        return

    token = args[1]
    if token.startswith("quiz_"):
        token = token[len("quiz_"):]
    if is_link_used(token):
        bot.send_message(message.chat.id, "❌ هذا الرابط قد تم استخدامه مسبقاً ولا يمكن استخدامه مرة أخرى.")
        return

    questions_batch = load_questions_by_batch(token)
    if not questions_batch:
        bot.send_message(message.chat.id, "❌ الرابط غير صحيح أو انتهت صلاحية الاختبار.")
        return

    mark_link_used(token)
    start_test(message.chat.id, questions_batch)

@bot.message_handler(commands=['test'])
def handle_test(message):
    global questions
    questions = load_questions()
    if not questions:
        bot.send_message(message.chat.id, "لا توجد أسئلة متاحة حالياً. الرجاء إضافة أسئلة أولاً باستخدام /insertQuestions")
        return
    start_test(message.chat.id, questions)

@bot.message_handler(commands=['insertQuestions'])
def handle_insert_question(message):
    chat_id = message.chat.id
    insert_states[chat_id] = {
        "step": "ask_subject",
        "batch": [],
    }
    bot.send_message(chat_id, "📘 ما اسم المادة أو الموضوع لهذه المجموعة من الأسئلة؟")

@bot.message_handler(func=lambda message: message.chat.id in edit_states)
def handle_edit_steps(message):
    chat_id = message.chat.id
    state = edit_states[chat_id]

    if state["step"] == "edit_text":
        # Update question text
        question_id = state["question_id"]
        new_text = message.text

        update_question(question_id, {"question": new_text})

        # Update batch metadata question count (in case something changed)
        question = get_question_by_id(question_id)
        if question:
            update_batch_metadata_question_count(question['batch_id'])

        bot.send_message(chat_id, f"✅ تم تحديث نص السؤال بنجاح!\n\nالنص الجديد: {new_text}")

        # Clear edit state
        edit_states.pop(chat_id, None)

    elif state["step"] == "edit_options":
        # Collect new options
        state["new_options"].append(message.text)
        state["current_option"] += 1

        if state["current_option"] < 4:
            bot.send_message(chat_id, f"🔄 أرسل الخيار رقم {state['current_option'] + 1}:")
        else:
            # All options collected, update question
            question_id = state["question_id"]
            new_options = state["new_options"]

            # Get current question to preserve the answer if it exists in new options
            current_question = get_question_by_id(question_id)
            current_answer = current_question["answer"]

            # Check if current answer exists in new options
            if current_answer in new_options:
                new_answer = current_answer
            else:
                # Set first option as default answer
                new_answer = new_options[0]
                bot.send_message(chat_id, f"⚠️ الإجابة الصحيحة السابقة لم تعد موجودة في الخيارات الجديدة.\nتم تعيين الخيار الأول كإجابة صحيحة: {new_answer}")

            update_question(question_id, {
                "options": new_options,
                "answer": new_answer
            })

            # Update batch metadata question count
            current_question = get_question_by_id(question_id)
            if current_question:
                update_batch_metadata_question_count(current_question['batch_id'])

            options_display = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(new_options)])
            bot.send_message(chat_id,
                f"✅ تم تحديث خيارات السؤال بنجاح!\n\n"
                f"الخيارات الجديدة:\n{options_display}\n\n"
                f"الإجابة الصحيحة: {new_answer}")

            # Clear edit state
            edit_states.pop(chat_id, None)

@bot.message_handler(func=lambda message: message.chat.id in insert_states)
def handle_insert_steps(message):
    chat_id = message.chat.id
    state = insert_states[chat_id]

    if state["step"] == "ask_subject":
        state["subject"] = message.text
        state["step"] = "ask_duration"
        bot.send_message(chat_id, "⏱️ ما مدة الاختبار بالدقائق؟ ")

    elif state["step"] == "ask_duration":
        if not message.text.isdigit() or int(message.text) <= 0:
            bot.send_message(chat_id, "❌ الرجاء إدخال رقم صحيح أكبر من 0 للمدة بالدقائق.")
            return
        state["duration_minutes"] = int(message.text)
        state["step"] = "ask_count"
        bot.send_message(chat_id, "📥 كم عدد الأسئلة التي تريد إدخالها؟")

    elif state["step"] == "ask_count":
        if not message.text.isdigit():
            bot.send_message(chat_id, "❌ يرجى إدخال رقم صحيح.")
            return
        state["total"] = int(message.text)
        state["current"] = 0
        state["step"] = "ask_question"
        bot.send_message(chat_id, f"📝 أرسل نص السؤال رقم 1:")

    elif state["step"] == "ask_question":
        state["question"] = message.text
        state["options"] = []
        state["step"] = "ask_options"
        bot.send_message(chat_id, "📌 أرسل 4 خيارات، كل خيار في رسالة منفصلة. ابدأ بالخيار الأول:")

    elif state["step"] == "ask_options":
        state["options"].append(message.text)
        if len(state["options"]) < 4:
            bot.send_message(chat_id, f"📌 أرسل الخيار رقم {len(state['options']) + 1}:")
        else:
            state["step"] = "ask_answer"
            bot.send_message(chat_id, "✅ أرسل رقم الإجابة الصحيحة من 1 إلى 4:")

    elif state["step"] == "ask_answer":
        if not message.text.isdigit():
            bot.send_message(chat_id, "❗ الرجاء إرسال رقم صحيح من 1 إلى 4.")
            return
        answer_index = int(message.text) - 1
        if answer_index not in range(4):
            bot.send_message(chat_id, "❗ الرقم خارج النطاق، الرجاء إرسال رقم بين 1 و4.")
            return

        correct_text = state["options"][answer_index]
        batch_id = state.get("batch_id")
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
            state["batch_id"] = batch_id

        new_question = {
            "question": state["question"],
            "options": state["options"],
            "answer": correct_text,
            "batch_id": batch_id,
            "subject": state["subject"]
        }

        state["batch"].append(new_question)
        state["current"] += 1

        if state["current"] == state["total"]:
            # توليد رمز فريد للربط
            link_token = generate_link_token()

            for q in state["batch"]:
                q["link_token"] = link_token
                q["used"] = False

            for q in state["batch"]:
                save_question(q)

            duration = state.get("duration_minutes")  # هنا تأخذ مدة المستخدم

            save_batch_link(batch_id, link_token, state["subject"], state["total"], duration)

            unique_link = f"https://t.me/TestStudentCollegeBot?start=quiz_{link_token}"
            bot.send_message(chat_id,
                f"✅ تم إدخال {state['total']} سؤال بنجاح.\n"
                f"مدة الاختبار: {duration} دقيقة\n"
                f"هذا هو رابط الاختبار الخاص (خاص بشخص واحد فقط):\n{unique_link}\n\n"
                f"يرجى إرسال هذا الرابط للطالب المخصص فقط.")
            insert_states.pop(chat_id)
        else:
            state["step"] = "ask_question"
            bot.send_message(chat_id, f"📝 أرسل نص السؤال رقم {state['current'] + 1}:")

@bot.message_handler(commands=['Questions'])
def handle_questions(message):
    chat_id = message.chat.id
    batches = get_all_batches()

    if not batches:
        bot.send_message(chat_id, "❗ لا توجد مجموعات أسئلة مضافة بعد.")
        return

    msg = "📋 قائمة الاختبارات المتوفرة:\n\n"
    for batch in batches:
        # Get real-time question count
        actual_count = get_actual_question_count_by_batch(batch['batch_id'])

        # Update metadata if count is different
        if actual_count != batch['question_count']:
            update_batch_metadata_question_count(batch['batch_id'])
            batch['question_count'] = actual_count

        # Fix bot username in telegram link if needed
        telegram_link = batch['telegram_link']
        if 'YourBotUsername' in telegram_link:
            telegram_link = telegram_link.replace('YourBotUsername', 'TestStudentCollegeBot')
            # Update the link in database
            from db import supabase
            supabase.table("batch_links").update({
                "telegram_link": telegram_link
            }).eq("batch_id", batch['batch_id']).execute()

        msg += f"📚 {batch['subject']} – {actual_count} سؤال – المدة: {batch['time']} دقيقة\n"
        msg += f"🔗 {telegram_link}\n\n"
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['EditQuestion'])
def handle_edit_question(message):
    chat_id = message.chat.id
    subjects = get_all_subjects()

    if not subjects:
        bot.send_message(chat_id, "❗ لا توجد مواد متاحة للتعديل. يرجى إضافة أسئلة أولاً باستخدام /insertQuestions")
        return

    # Create inline keyboard with subject buttons
    markup = types.InlineKeyboardMarkup()
    for subject in subjects:
        # Use subject name as both display text and callback data
        callback_data = f"edit_subject:{subject}"
        markup.add(types.InlineKeyboardButton(f"📚 {subject}", callback_data=callback_data))

    bot.send_message(
        chat_id,
        "📝 اختر المادة التي تريد تعديل أسئلتها:\n\n"
        "👆 اضغط على اسم المادة لعرض أسئلتها:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_subject:"))
def handle_subject_selection(call):
    chat_id = call.message.chat.id
    subject = call.data.split(":", 1)[1]

    # Get all questions for this subject
    questions = get_questions_by_subject(subject)

    if not questions:
        bot.answer_callback_query(call.id, "❌ لا توجد أسئلة لهذه المادة")
        return

    # Create inline keyboard with questions
    markup = types.InlineKeyboardMarkup()
    for i, question in enumerate(questions):
        question_text = question["question"]
        # Truncate long questions for button display
        display_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
        callback_data = f"edit_question:{question['id']}"
        markup.add(types.InlineKeyboardButton(f"📝 {i+1}. {display_text}", callback_data=callback_data))

    # Add back button
    markup.add(types.InlineKeyboardButton("🔙 العودة للمواد", callback_data="back_to_subjects"))

    bot.edit_message_text(
        f"📚 أسئلة مادة: {subject}\n\n"
        f"📊 عدد الأسئلة: {len(questions)}\n"
        f"👆 اختر السؤال الذي تريد تعديله:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, f"تم تحديد مادة: {subject}")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_subjects")
def handle_back_to_subjects(call):
    chat_id = call.message.chat.id
    subjects = get_all_subjects()

    # Recreate subject selection menu
    markup = types.InlineKeyboardMarkup()
    for subject in subjects:
        callback_data = f"edit_subject:{subject}"
        markup.add(types.InlineKeyboardButton(f"📚 {subject}", callback_data=callback_data))

    bot.edit_message_text(
        "📝 اختر المادة التي تريد تعديل أسئلتها:\n\n"
        "👆 اضغط على اسم المادة لعرض أسئلتها:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, "العودة لقائمة المواد")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_question:"))
def handle_question_edit(call):
    chat_id = call.message.chat.id
    question_id = int(call.data.split(":")[1])

    # Get the question details
    question = get_question_by_id(question_id)
    if not question:
        bot.answer_callback_query(call.id, "❌ السؤال غير موجود")
        return

    # Store editing state
    edit_states[chat_id] = {
        "question_id": question_id,
        "original_question": question,
        "step": "show_question"
    }

    # Create edit options menu
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل نص السؤال", callback_data=f"edit_text:{question_id}"))
    markup.add(types.InlineKeyboardButton("🔄 تعديل الخيارات", callback_data=f"edit_options:{question_id}"))
    markup.add(types.InlineKeyboardButton("✅ تغيير الإجابة الصحيحة", callback_data=f"edit_answer:{question_id}"))
    markup.add(types.InlineKeyboardButton("🔙 العودة للأسئلة", callback_data=f"back_to_questions:{question['subject']}"))

    # Display current question details
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    correct_answer_index = question["options"].index(question["answer"]) + 1 if question["answer"] in question["options"] else "غير محدد"

    question_details = (
        f"📝 السؤال الحالي:\n{question['question']}\n\n"
        f"📋 الخيارات:\n{options_text}\n\n"
        f"✅ الإجابة الصحيحة: {correct_answer_index}. {question['answer']}\n\n"
        f"👆 اختر ما تريد تعديله:"
    )

    bot.edit_message_text(
        question_details,
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, "اختر نوع التعديل")

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_questions:"))
def handle_back_to_questions(call):
    chat_id = call.message.chat.id
    subject = call.data.split(":", 1)[1]

    # Get all questions for this subject
    questions = get_questions_by_subject(subject)

    # Create inline keyboard with questions
    markup = types.InlineKeyboardMarkup()
    for i, question in enumerate(questions):
        question_text = question["question"]
        display_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
        callback_data = f"edit_question:{question['id']}"
        markup.add(types.InlineKeyboardButton(f"📝 {i+1}. {display_text}", callback_data=callback_data))

    markup.add(types.InlineKeyboardButton("🔙 العودة للمواد", callback_data="back_to_subjects"))

    bot.edit_message_text(
        f"📚 أسئلة مادة: {subject}\n\n"
        f"📊 عدد الأسئلة: {len(questions)}\n"
        f"👆 اختر السؤال الذي تريد تعديله:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, f"العودة لأسئلة {subject}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_text:"))
def handle_edit_text(call):
    chat_id = call.message.chat.id
    question_id = int(call.data.split(":")[1])

    edit_states[chat_id] = {
        "question_id": question_id,
        "step": "edit_text"
    }

    bot.send_message(chat_id, "✏️ أرسل نص السؤال الجديد:")
    bot.answer_callback_query(call.id, "أرسل النص الجديد")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_options:"))
def handle_edit_options(call):
    chat_id = call.message.chat.id
    question_id = int(call.data.split(":")[1])

    edit_states[chat_id] = {
        "question_id": question_id,
        "step": "edit_options",
        "new_options": [],
        "current_option": 0
    }

    bot.send_message(chat_id, "🔄 أرسل الخيار الأول الجديد:")
    bot.answer_callback_query(call.id, "أرسل الخيارات الجديدة")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_answer:"))
def handle_edit_answer(call):
    chat_id = call.message.chat.id
    question_id = int(call.data.split(":")[1])

    question = get_question_by_id(question_id)
    if not question:
        bot.answer_callback_query(call.id, "❌ السؤال غير موجود")
        return

    # Create buttons for each option
    markup = types.InlineKeyboardMarkup()
    for i, option in enumerate(question["options"]):
        callback_data = f"set_answer:{question_id}:{i}"
        is_current = "✅ " if option == question["answer"] else ""
        markup.add(types.InlineKeyboardButton(f"{is_current}{i+1}. {option}", callback_data=callback_data))

    markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data=f"edit_question:{question_id}"))

    bot.edit_message_text(
        f"✅ اختر الإجابة الصحيحة الجديدة:\n\n"
        f"📝 السؤال: {question['question']}\n\n"
        f"👆 اضغط على الإجابة الصحيحة:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    bot.answer_callback_query(call.id, "اختر الإجابة الصحيحة")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_answer:"))
def handle_set_answer(call):
    chat_id = call.message.chat.id
    parts = call.data.split(":")
    question_id = int(parts[1])
    option_index = int(parts[2])

    question = get_question_by_id(question_id)
    if not question:
        bot.answer_callback_query(call.id, "❌ السؤال غير موجود")
        return

    new_answer = question["options"][option_index]

    # Update the question in database
    update_question(question_id, {"answer": new_answer})

    # Update batch metadata question count
    updated_question = get_question_by_id(question_id)
    if updated_question:
        update_batch_metadata_question_count(updated_question['batch_id'])

    bot.answer_callback_query(call.id, f"✅ تم تحديث الإجابة إلى: {new_answer}")

    # Go back to question edit menu
    updated_question = get_question_by_id(question_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل نص السؤال", callback_data=f"edit_text:{question_id}"))
    markup.add(types.InlineKeyboardButton("🔄 تعديل الخيارات", callback_data=f"edit_options:{question_id}"))
    markup.add(types.InlineKeyboardButton("✅ تغيير الإجابة الصحيحة", callback_data=f"edit_answer:{question_id}"))
    markup.add(types.InlineKeyboardButton("🔙 العودة للأسئلة", callback_data=f"back_to_questions:{updated_question['subject']}"))

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(updated_question["options"])])
    correct_answer_index = updated_question["options"].index(updated_question["answer"]) + 1

    question_details = (
        f"📝 السؤال الحالي:\n{updated_question['question']}\n\n"
        f"📋 الخيارات:\n{options_text}\n\n"
        f"✅ الإجابة الصحيحة: {correct_answer_index}. {updated_question['answer']}\n\n"
        f"👆 اختر ما تريد تعديله:"
    )

    bot.edit_message_text(
        question_details,
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_answer:"))
def show_answer_handler(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "يرجى بدء الاختبار أولاً باستخدام /test أو الرابط الخاص")
        return
    timer = user_data[chat_id].get("timer")
    if timer:
        timer.cancel()

    question_index = int(call.data.split(":")[1])
    questions_list = user_data[chat_id]["questions"]
    correct_text = questions_list[question_index]["answer"]

    bot.answer_callback_query(call.id, f"✔️ الإجابة الصحيحة: {correct_text}")
    user_data[chat_id]["current_question"] += 1
    next_q = user_data[chat_id]["current_question"]
    if next_q < len(questions_list):
        send_question(chat_id, next_q, questions_list)
        start_timer(chat_id)
    else:
        finish_test(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.isdigit() or (call.data.count(":") == 1 and all(part.isdigit() for part in call.data.split(":"))))
def handle_answer(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "ابدأ الاختبار أولاً باستخدام /test أو الرابط الخاص")
        return

    timer = user_data[chat_id].get("timer")
    if timer:
        timer.cancel()

    try:
        question_index, chosen_option = map(int, call.data.split(":"))
    except:
        return

    questions_list = user_data[chat_id]["questions"]
    question = questions_list[question_index]
    correct_text = question["answer"]
    chosen_text = question["options"][chosen_option]

    if chosen_text == correct_text:
        user_data[chat_id]["correct"] += 1
        bot.answer_callback_query(call.id, "✅ إجابة صحيحة")
    else:
        user_data[chat_id]["incorrect"] += 1
        bot.answer_callback_query(call.id, "❌ إجابة خاطئة")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💡 إظهار الإجابة الصحيحة", callback_data=f"show_answer:{question_index}"))
        bot.send_message(chat_id, "إجابتك خاطئة. اضغط على الزر أدناه لمعرفة الإجابة الصحيحة:", reply_markup=markup)

    user_data[chat_id]["current_question"] += 1
    next_q = user_data[chat_id]["current_question"]
    if next_q < len(questions_list):
        send_question(chat_id, next_q, questions_list)
        start_timer(chat_id)
    else:
        finish_test(chat_id)

@bot.message_handler(commands=['ActiveQuestionLinkAgain'])
def handle_active_question_link_again(message):
    """Handle the command to reactivate expired question links"""
    chat_id = message.chat.id
    batches = get_all_batches()

    if not batches:
        bot.send_message(chat_id, "❗ لا توجد مجموعات أسئلة مضافة بعد.")
        return

    # Filter and show all batches with their status
    msg = "🔄 إعادة تفعيل روابط الأسئلة:\n\n"
    msg += "📋 قائمة جميع الاختبارات:\n\n"

    active_batches = []
    for batch in batches:
        # Get real-time question count
        actual_count = get_actual_question_count_by_batch(batch['batch_id'])

        # Update metadata if count is different
        if actual_count != batch['question_count']:
            update_batch_metadata_question_count(batch['batch_id'])
            batch['question_count'] = actual_count

        # Fix bot username in telegram link if needed
        telegram_link = batch['telegram_link']
        if 'YourBotUsername' in telegram_link:
            telegram_link = telegram_link.replace('YourBotUsername', 'TestStudentCollegeBot')
            # Update the link in database
            from db import supabase
            supabase.table("batch_links").update({
                "telegram_link": telegram_link
            }).eq("batch_id", batch['batch_id']).execute()

        status_emoji = "❌ مستخدم" if batch['used'] else "✅ نشط"
        msg += f"📚 {batch['subject']} – {actual_count} سؤال – المدة: {batch['time']} دقيقة\n"
        msg += f"📊 الحالة: {status_emoji}\n"
        msg += f"🔗 {telegram_link}\n\n"

        active_batches.append(batch)

    if not active_batches:
        bot.send_message(chat_id, "❗ لا توجد اختبارات متاحة.")
        return

    # Create inline keyboard for reactivation
    markup = types.InlineKeyboardMarkup()
    for batch in active_batches:
        if batch['used']:  # Only show used/expired batches for reactivation
            button_text = f"🔄 إعادة تفعيل: {batch['subject']}"
            callback_data = f"reactivate:{batch['batch_id']}"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))

    if markup.keyboard:  # If there are any used batches to reactivate
        msg += "\n👆 اختر الاختبار الذي تريد إعادة تفعيل رابطه:"
        bot.send_message(chat_id, msg, reply_markup=markup)
    else:
        msg += "\n✅ جميع الروابط نشطة حالياً!"
        bot.send_message(chat_id, msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reactivate:"))
def handle_reactivate_batch(call):
    """Handle batch reactivation callback"""
    chat_id = call.message.chat.id
    batch_id = call.data.split(":", 1)[1]

    # Get batch info
    batch_info = get_batch_info_by_id(batch_id)
    if not batch_info:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على الاختبار")
        return

    # Reactivate the batch
    if reactivate_batch_link(batch_id):
        # Success message
        success_msg = (
            f"🎉 تم إعادة تفعيل الاختبار بنجاح!\n\n"
            f"📚 المادة: {batch_info['subject']}\n"
            f"📊 عدد الأسئلة: {batch_info['question_count']}\n"
            f"⏱️ المدة: {batch_info['duration_minutes']} دقيقة\n"
            f"🟢 الحالة: نشط ومتاح للاستخدام\n\n"
            f"🔗 الرابط الجاهز للإرسال:\n{batch_info['telegram_link']}\n\n"
            f"✅ الاختبار جاهز الآن!\n"
            f"📤 يمكنك إرسال هذا الرابط لأي طالب جديد\n"
            f"🎯 الرابط سيعمل بشكل طبيعي عند النقر عليه"
        )

        bot.edit_message_text(
            success_msg,
            chat_id=chat_id,
            message_id=call.message.message_id
        )

        bot.answer_callback_query(call.id, f"✅ تم تفعيل اختبار {batch_info['subject']} بنجاح!")
    else:
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء إعادة التفعيل")

bot.polling()
