import telebot
from tinydb import TinyDB, Query
import random

# =====================
# 1. Bot Token
# =====================
TOKEN = "8293084237:AAFIadRPQZLXbiQ0IhYDeWdaxd3nGmuzTX0"  # <-- Replace with your BotFather token
bot = telebot.TeleBot(TOKEN)

# =====================
# 2. Database Setup
# =====================
db = TinyDB('users.json')  # Stores users, answers, points
User = Query()

# =====================
# 3. Full Question Pool (50+ questions example)
# =====================
all_questions = [
    "What's your favorite food?",
    "What's your favorite hobby?",
    "What's your favorite color?",
    "Which country do you want to visit?",
    "Who's your favorite celebrity?",
    "What's your favorite movie?",
    "What's your favorite sport?",
    "What's your favorite book?",
    "What's your dream job?",
    "What's your favorite animal?",
    # ... add up to 50-70 questions
]

# =====================
# 4. Track each user's registration progress
# =====================
user_progress = {}        # Tracks which question number the user is answering
user_questions = {}       # Stores 7 random questions per user

# =====================
# 5. /reg command → start registration
# =====================
@bot.message_handler(commands=['reg'])
def register(message):
    user_id = message.from_user.id
    # Pick 7 random questions for this user
    user_questions[user_id] = random.sample(all_questions, 7)
    user_progress[user_id] = 0
    bot.send_message(user_id, "Hi! Let's get to know you. Answer these 7 questions:")
    bot.send_message(user_id, user_questions[user_id][0])

# =====================
# 6. Handle user's answers
# =====================
@bot.message_handler(func=lambda message: message.from_user.id in user_progress)
def handle_answers(message):
    user_id = message.from_user.id
    q_index = user_progress[user_id]

    # Save answer in database
    entry = db.get(User.user_id == user_id)
    if not entry:
        db.insert({"user_id": user_id, "username": message.from_user.username, "answers": {}, "points": 0})
        entry = db.get(User.user_id == user_id)

    answers = entry['answers']
    answers[user_questions[user_id][q_index]] = message.text
    db.update({'answers': answers}, User.user_id == user_id)

    # Next question or finish registration
    q_index += 1
    if q_index < 7:
        user_progress[user_id] = q_index
        bot.send_message(user_id, user_questions[user_id][q_index])
    else:
        del user_progress[user_id]
        del user_questions[user_id]
        bot.send_message(user_id, "Registration complete! You can now play the game in the group using /knoweachother")

# =====================
# 7. /knoweachother → start guessing game
# =====================
@bot.message_handler(commands=['knoweachother'])
def start_game(message):
    all_users = db.all()
    if len(all_users) < 2:
        bot.reply_to(message, "Not enough registered members to start the game.")
        return

    # Pick random member and random question
    selected_user = random.choice(all_users)
    question, answer = random.choice(list(selected_user['answers'].items()))
    bot.send_message(message.chat.id, f"Guess {selected_user['username']}'s answer: {question}")

    bot.register_next_step_handler_by_chat_id(message.chat.id, check_answer, answer, selected_user['user_id'])

# =====================
# 8. Check answer
# =====================
def check_answer(message, correct_answer, selected_user_id):
    if message.text.lower() == correct_answer.lower():
        user_entry = db.get(User.user_id == message.from_user.id)
        points = user_entry['points'] + 1
        db.update({'points': points}, User.user_id == message.from_user.id)
        bot.reply_to(message, f"Correct! {message.from_user.username} gets 1 point 🎉")
    else:
        bot.reply_to(message, f"Oops! The correct answer was: {correct_answer}")

# =====================
# 9. /score → show leaderboard
# =====================
@bot.message_handler(commands=['score'])
def show_score(message):
    all_users = db.all()
    if not all_users:
        bot.reply_to(message, "No scores yet.")
        return

    scoreboard = "🏆 Friendship Game Scores 🏆\n"
    sorted_users = sorted(all_users, key=lambda x: x['points'], reverse=True)
    for u in sorted_users:
        scoreboard += f"{u['username']}: {u['points']} points\n"

    bot.send_message(message.chat.id, scoreboard)

# =====================
# 10. Run the Bot
# =====================
bot.polling()
