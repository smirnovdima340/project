from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from config import TOKEN, MAX_TOKENS
from gpt import GPT

bot = TeleBot('')
gpt = GPT()

# Словарик для хранения задач пользователей и ответов GPT
users_history = {}


# Функция для создания клавиатуры с нужными кнопочками
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


# Приветственное сообщение /start
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я бот-помощник для ответов на вопросы об интернет мошенничестве и фишинге\n"
                          f"Ты можешь прислать свой вопрос, а я постараюсь на него ответить.\n"
                          "Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.",
                     reply_markup=create_keyboard(["/solve_task", '/help']))


# Команда /help
@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text="Чтобы задать вопрос: нажми /solve_task, а затем напиши вопрос",
                     reply_markup=create_keyboard(["/solve_task"]))


# Команда /debug
@bot.message_handler(commands=['debug'])
def debug(message):
    # bot.send_document()
    pass


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши новый вопрос:")
    bot.register_next_step_handler(message, get_promt)


# Фильтр для обработки кнопочки "Продолжить решение"
def continue_filter(message):
    button_text = 'Продолжить'
    return message.text == button_text


# Получение задачи от пользователя или продолжение решения
@bot.message_handler(func=continue_filter)
def get_promt(message):
    user_id = message.from_user.id

    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, get_promt)
        return

    # Получаем текст сообщения от пользователя
    user_request = message.text

    if (user_id not in users_history or users_history[user_id] == {}) and user_request == "Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить ответ на вопрос, сначала нужно отправить текст вопроса")
        bot.send_message(user_id, "Напиши новый вопрос")
        bot.register_next_step_handler(message, get_promt)
        return

    ### GPT: проверка количества токенов

    if gpt.count_tokens(user_request) > MAX_TOKENS:
        bot.send_message(user_id, "Запрос превышает количество символов.\nИсправьте, пожалуйста, запрос")
        bot.register_next_step_handler(message, get_promt)
        return

    if user_id not in users_history or users_history[user_id] == {}:
        # Сохраняем промт пользователя и начало ответа GPT в словарик users_history
        users_history[user_id] = {
            'system_content': "Ты - дружелюбный помощник для ответов на вопросы на русском языке",
            'user_request': user_request,
            'assistant_content': "Ответим на вопрос"
        }

    ### GPT: формирование промта и отправка запроса к нейросети
    promt = gpt.make_promt(users_history[user_id])
    resp = gpt.send_request(promt)

    ### GPT: проверка ошибок и обработка ответа
    status, answer = gpt.process_resp(resp)

    if not status:
        gpt.save_log(user_id, answer)
        bot.send_message(user_id, text=answer)
        return

    users_history[user_id]['assistant_content'] += answer
    bot.send_message(user_id, text=users_history[user_id]['assistant_content'],
                     reply_markup=create_keyboard(["Продолжить ", "Завершить"]))


def end_filter(message):
    button_text = 'Завершить'
    return message.text == button_text


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    user_id = message.from_user.id
    if user_id in users_history:
        bot.send_message(user_id, "Текущий вопрос завершен")
    users_history[user_id] = {}
    solve_task(message)

bot.polling()