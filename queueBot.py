import telebot
import my_token

bot = telebot.TeleBot(my_token.API_TOKEN)


# Очереди в чатах
queues = {}
# Рабочая тема для чатов
active_topics = {}

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

def is_valid_topic(message):
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    return chat_id in active_topics and active_topics[chat_id] == thread_id

# Начальное сообщение
@bot.message_handler(commands=['start'])
def enable_this_topic(message):
    bot.reply_to(message, "Для начала работы бота отправьте команду /enableThisTopic в той теме чат"
                          "а которую желаете сделать рабочей темой для бота, кроме основной темы.")

# Помощь
@bot.message_handler(commands=['help'])
def enable_this_topic(message):
    help_text = (
        "📋 <b>Список команд:</b>\n"
        "/start — старт\n"
        "/help — список команд\n"
        "/queue — встать в очередь\n"
        "/list — показать очередь\n"
        "/skip — пропустить 1 человека вперёд\n"
        "/quit — выйти из очереди\n"
        "/current — кто сейчас первый\n"
        "/clear — очистить очередь\n"
        "/next — следующий по очереди\n"
        "/enableThisTopic — сделать эту тему рабочей"
    )
    bot.reply_to(message, help_text, parse_mode="HTML")


# Сделать тему рабочей, все остальные нерабочие
@bot.message_handler(commands=['enableThisTopic'])
def enable_this_topic(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    thread_id = message.message_thread_id


    if message.chat.type != "supergroup":
        bot.reply_to(message, "Бот работает только в супергруппах с темами.")
        return

    if thread_id is None:
        bot.reply_to(message, "Команду нужно отправлять внутри темы (не основной).")
        return

    if not is_chat_owner(chat_id, user_id):
        bot.reply_to(message, "Только владелец чата может включать тему.")
        return

    active_topics[chat_id] = thread_id
    bot.reply_to(message, f"Бот теперь будет работать только в этой теме (ID {thread_id}).")

#Встать в очередь
@bot.message_handler(commands=['queue'])
def handle_queue(message):
    if not is_valid_topic(message):
        return
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
    if not is_valid_topic(message):
        return
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
    if not is_valid_topic(message):
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    queue = get_queue(chat_id)

    if not is_chat_owner(chat_id, user_id):
        bot.reply_to(message, "Только Антон Андреевич чата может использовать эту команду.")
        return

    if queue:
        finished = queue.pop(0)
        if queue:
            bot.reply_to(message, f"Следующий: {queue[0]['username']}")
        else:
            bot.reply_to(message, "Очередь пуста.")
    else:
        bot.reply_to(message, "Очередь пуста.")

# Текущий первый в очереди
@bot.message_handler(commands=['current'])
def handle_next(message):
    if not is_valid_topic(message):
        return
    chat_id = message.chat.id
    queue = get_queue(chat_id)

    if queue:
        bot.reply_to(message, f"Первый в очереди: {queue[0]['username']}")
    else:
        bot.reply_to(message, "Очередь пуста.")

# Очистить очередь (только владелец чата(например: Антон Андреевич))
@bot.message_handler(commands=['clear'])
def handle_reset(message):
    if not is_valid_topic(message):
        return
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_chat_owner(chat_id, user_id):
        bot.reply_to(message, "Только Антон Андреевич чата может очистить очередь.")
        return

    queues[chat_id] = []
    bot.reply_to(message, "Очередь очищена.")

# Список очереди
@bot.message_handler(commands=['list'])
def handle_list(message):
    if not is_valid_topic(message):
        return
    chat_id = message.chat.id
    queue = get_queue(chat_id)

    if not queue:
        bot.reply_to(message, "Очередь пуста.")
        return
    text = "Текущая очередь:\n"
    for i, user in enumerate(queue, 1):
        text += f"{i}. {user['username']}\n"
    bot.reply_to(message, text)

# Пропустить вперед себя
@bot.message_handler(commands=['skip'])
def handle_skip(message):
    if not is_valid_topic(message):
        return
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
