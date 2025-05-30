import telebot
import my_token

bot = telebot.TeleBot(my_token.API_TOKEN)


# Очереди в чатах
queues = {}

# Получить имя пользователя
def get_user_name(user):
    if user.username:
        return f"@{user.username}"
    else:
        return f"{user.first_name} {user.last_name}".strip()


# Получить очередь чата
def get_queue(chat_id):
    if chat_id not in queues:
        queues[chat_id] = []
    return queues[chat_id]

# Проверка пользователя на владельца чата
def is_chat_owner(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id and admin.status == 'creator':
                return True
    except Exception as e:
        print("Ошибка при проверке владельца чата:", e)
    return False

#Встать в очередь
@bot.message_handler(commands=['queue'])
def handle_queue(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    queue = get_queue(chat_id)

    if any(u['id'] == user_id for u in queue):
        position = next(i for i, u in enumerate(queue) if u['id'] == user_id) + 1
        bot.reply_to(message, f"Вы уже в очереди под номером {position}.")
    else:
        queue.append({
            'id': user_id,
            'username': get_user_name(message.from_user)
            })
        bot.reply_to(message, f"Вы добавлены в очередь. Ваш номер: {len(queue)}.")

# Выйти из очереди
@bot.message_handler(commands=['quit'])
def handle_quit(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    queue = get_queue(chat_id)

    for user in queue:
        if user['id'] == user_id:
            queue.remove(user)
            bot.reply_to(message, "Вы вышли из очереди.")
            return
    bot.reply_to(message, "Вы не в очереди.")

# Следующий (только владелец чата (например: Антон Андреевич))
@bot.message_handler(commands=['next'])
def handle_next(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    queue = get_queue(chat_id)

    if not is_chat_owner(chat_id, user_id):
        bot.reply_to(message, "Только Антон Андреевич чата может использовать эту команду.")
        return

    if queue:
        finished = queue.pop(0)
        if queue:
            bot.send_message(chat_id, f"Следующий: {queue[0]['username']}")
        else:
            bot.send_message(chat_id, "Очередь пуста.")
    else:
        bot.send_message(chat_id, "Очередь пуста.")

# Очистить очередь (только владелец чата(например: Антон Андреевич))
@bot.message_handler(commands=['clear'])
def handle_reset(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_chat_owner(chat_id, user_id):
        bot.reply_to(message, "Только Антон Андреевич чата может очистить очередь.")
        return

    queues[chat_id] = []
    bot.send_message(chat_id, "Очередь очищена.")

# Список очереди
@bot.message_handler(commands=['list'])
def handle_list(message):
    chat_id = message.chat.id
    queue = get_queue(chat_id)

    if not queue:
        bot.reply_to(message, "Очередь пуста.")
        return
    text = "Текущая очередь:\n"
    for i, user in enumerate(queue, 1):
        text += f"{i}. {user['username']}\n"
    bot.send_message(chat_id, text)

# Пропустить вперед себя
@bot.message_handler(commands=['skip'])
def handle_skip(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    queue = get_queue(chat_id)

    for i in range(len(queue)):
        if queue[i]['id'] == user_id:
            if i < len(queue) - 1:
                temp = queue[i]
                queue[i] = queue[i + 1]
                queue[i + 1] = temp
                bot.reply_to(message, f"Вы пропустили вперёд {queue[i]['username']}.")
            else:
                bot.reply_to(message, "Вы уже последний в очереди.")
            return
    bot.reply_to(message, "Вы не в очереди.")

bot.infinity_polling()
