import telebot
import json
import os
from background import keep_alive
from telebot import types

TOKEN = 'твой токен'
YOUR_CHANNEL_ID = '-1001959485469'
PASSWORD = '1234'  # Здесь указывается ваш пароль
DATABASE_FILE = 'database.txt'  # Путь к файлу базы данных
BLACKLIST_FILE = 'blacklist.txt'  # Путь к файлу чёрного списка
RATINGS_FILE = 'monthly_ratings.json' # Путь к файлу, где хранятся данные о рейтинге за месяц (экспорт данных можно осущиствить введя команду \export_ratings, при вводе этой команды базаднанных monthly_ratings.json обнуляется, поэтому вводить эту команду нужно раз в месяц )
CHANNEL_ID = '-1001959485469' # Здесь указываете ID вашего закрытого канала для отправки рейтинга
#TASK /home/guidfable/.local/bin/python3 /path/to/restart_bot.py

bot = telebot.TeleBot(TOKEN)

# Флаг, указывающий, прошла ли верификация пользователя
verified_users = {}

# Инициализируем данные о рейтинге за месяц
monthly_ratings = {
    'Чистота и уборка': [0.0, 0],
    'Освещённость': [0.0, 0],
    'Звуковая обстановка': [0.0, 0],
    'Ландшафтный дизайн': [0.0, 0],
    'Уровень участия жильцов': [0.0, 0],
}

current_user_id = None
current_user_name = None

# Загрузка чёрного списка из файла
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as file:
            return [int(line.strip()) for line in file]
    except FileNotFoundError:
        return []

# Проверка, находится ли пользователь в чёрном списке
def is_user_in_blacklist(user_id):
    blacklist = load_blacklist()
    return user_id in blacklist

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if is_user_in_blacklist(user_id):
        bot.send_message(user_id, "Вы находитесь в чёрном списке и не можете использовать бота.")
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('Обращение жильцов')
    item2 = telebot.types.KeyboardButton('Передача показаний')
    item3 = telebot.types.KeyboardButton('О компании')
    item4 = telebot.types.KeyboardButton('Связаться с диспетчером')
    item55 = telebot.types.KeyboardButton('Руководство по использованию бота')

    markup.add(item1, item2, item3, item4, item55)

    bot.send_message(message.chat.id,
                     'Привет, {0.first_name}.\n\n🤖Я электронный диспетчер управляющей компании.\n\nС моей помощью Вы можете:\n\n📌узнать об отключении воды и ремонтных работах в Вашем доме.\n\n📌 подсказать управляющему, что именно волнует жильцов Вашего дома.\n\n📌сможете отправить показания счетчиков, просто сделав их фото.\n\n📌Мы разработали систему оценки двора, учитывая различные аспекты, проголосовать можно прямо сейчас нажав ➡️ /rate_yard.\n\nТеперь в один клик (!) можно получать новости из разных каналов (!!) в одной папке 🤩\n\nСобрали для вас 3 полезных группы нашего района, ссылка на папку с группами ⬇️\nhttps://t.me/addlist/Zm7faHv80180ZTYy \n\nВведите пароль⬇️'.format(
                         message.from_user), reply_markup=markup, disable_web_page_preview=True)

@bot.message_handler(func=lambda message: message.text == "Да")
def send_contact(message):
  markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
  button = types.KeyboardButton("Поделиться контактом", request_contact=True)
  markup.add(button)

  bot.send_message(message.chat.id,
                   "Пожалуйста, поделитесь своим контактом",
                   reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
  bot.send_message(message.chat.id,
                   "Спасибо, ваш контакт получен.\nКнопка /start вернет вас в главное меню.")

  # отправка контакта в канал
  bot.send_contact(CHANNEL_ID, message.contact.phone_number,
                   message.contact.first_name)

@bot.message_handler(func=lambda message: message.text == "Нет")
def back_to_menu(message):
  bot.clear_step_handler(message)
  start(message)

@bot.message_handler(commands=['rate_yard'])
def rate_yard(message):
    global current_user_id, current_user_name
    current_user_id = message.chat.id
    current_user_name = message.from_user.first_name
    bot.send_message(current_user_id, "Оцените Чистоту и уборку в Вашем дворе от 1 до 5:\n\n1: Грязно и мусорно - Во дворе присутствует большое количество мусора, мусорных контейнеров, и общая чистота оставляет желать лучшего. Видимые следы грязи и мусора повсюду.\n\n5: Очень чисто и ухожено - Двор выглядит безупречно чистым и аккуратным.")
    bot.register_next_step_handler(message, save_cleanliness_rating)

def save_cleanliness_rating(message):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        bot.send_message(current_user_id, "Произошла ошибка нажмите кнопку /start")
        return

    average_rating, total_votes = monthly_ratings['Чистота и уборка']
    total_votes += 1
    average_rating = ((average_rating * (total_votes - 1)) + rating) / total_votes
    monthly_ratings['Чистота и уборка'] = [average_rating, total_votes]

    bot.send_message(current_user_id, f"Оцените Освещённость:\n\n1: Плохая видимость в ночное время - Вечером и ночью двор плохо освещен, что создает проблемы с видимостью и безопасностью. Мало или вообще нет уличного освещения.\n\n5: Очень хорошая освещённость - Вечером и ночью двор прекрасно освещен. Хорошая видимость и безопасность для жильцов.")
    bot.register_next_step_handler(message, save_lighting_rating)

def save_lighting_rating(message):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        bot.send_message(current_user_id, "Произошла ошибка нажмите кнопку /start")
        return

    average_rating, total_votes = monthly_ratings['Освещённость']
    total_votes += 1
    average_rating = ((average_rating * (total_votes - 1)) + rating) / total_votes
    monthly_ratings['Освещённость'] = [average_rating, total_votes]

    bot.send_message(current_user_id, f"Оцените Звуковую обстановку:\n\n1: Очень шумно и неприятно - Во дворе постоянный шум, например, из-за проезжающего транспорта, строительных работ или других источников шума. Это мешает покою и комфорту жильцов.\n\n5: Очень тихо и спокойно - В дворе практически нет шума. Это создает спокойную и приятную атмосферу для жильцов.")
    bot.register_next_step_handler(message, save_sound_rating)

def save_sound_rating(message):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        bot.send_message(current_user_id, "Произошла ошибка нажмите кнопку /start")
        return

    average_rating, total_votes = monthly_ratings['Звуковая обстановка']
    total_votes += 1
    average_rating = ((average_rating * (total_votes - 1)) + rating) / total_votes
    monthly_ratings['Звуковая обстановка'] = [average_rating, total_votes]

    bot.send_message(current_user_id, f"Оцените Ландшафтный дизайн:\n\n1: Некрасивый и запущенный - Двор выглядит неухоженным, отсутствует зелень, цветы и декоративные элементы. Он может выглядеть уныло и неаккуратно.\n\n5: Красиво и ухожено, есть зелень и цветы - В дворе красивый ландшафтный дизайн, зелень, цветы, и ухоженная территория. Это делает его привлекательным и приятным для жильцов.")
    bot.register_next_step_handler(message, save_landscape_rating)

def save_landscape_rating(message):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        bot.send_message(current_user_id, "Произошла ошибка нажмите кнопку /start")
        return

    average_rating, total_votes = monthly_ratings['Ландшафтный дизайн']
    total_votes += 1
    average_rating = ((average_rating * (total_votes - 1)) + rating) / total_votes
    monthly_ratings['Ландшафтный дизайн'] = [average_rating, total_votes]

    bot.send_message(current_user_id, f"Оцените Уровень участия жильцов:\n\n1: Мало активности и участия в улучшении дворовой среды - Жильцы мало активны и мало участвуют в общественных инициативах и работах по улучшению двора.\n\n5: Высокий уровень активности и инициативы жильцов - Жильцы активно участвуют в улучшении дворовой среды, проводят мероприятия и акции по благоустройству, инициируют и поддерживают проекты по улучшению двора.")
    bot.register_next_step_handler(message, save_participation_rating)

def save_participation_rating(message):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        bot.send_message(current_user_id, "Произошла ошибка нажмите кнопку /start")
        return

    average_rating, total_votes = monthly_ratings['Уровень участия жильцов']
    total_votes += 1
    average_rating = ((average_rating * (total_votes - 1)) + rating) / total_votes
    monthly_ratings['Уровень участия жильцов'] = [average_rating, total_votes]

    bot.send_message(current_user_id, f"Спасибо за Ваш голос.\n\nКнопка /start вернет вас в главное меню")

    with open(RATINGS_FILE, 'w') as file:
        json.dump(monthly_ratings, file, indent=4)

@bot.message_handler(commands=['export_ratings'])
def export_ratings(message):
    total_votes_cleanliness = monthly_ratings['Чистота и уборка'][1]
    text = f"Рейтинг за месяц\nВсего голосов: {total_votes_cleanliness}:\n\n"
    for category, (average_rating, total_votes) in monthly_ratings.items():
        text += f"{category}: \nСредний рейтинг - {average_rating:.2f},\n\n"

    bot.send_message(CHANNEL_ID, text)

    for category in monthly_ratings:
        monthly_ratings[category] = [0.0, 0]

@bot.message_handler(commands=['user'])
def add_user_to_database(message):
    user_id = message.chat.id  # Получить user_id из объекта message
    if is_user_in_database(user_id):
        bot.send_message(user_id, "Вы уже есть в базе данных")
    else:
        with open(DATABASE_FILE, 'a') as file:
            file.write(str(user_id) + '\n')
        bot.send_message(user_id, "Вы были добавлены в базу данных")

def is_user_in_database(user_id):
    with open(DATABASE_FILE, 'r') as file:
        for line in file:
            if str(user_id) == line.strip():
                return True
    return False

@bot.message_handler(commands=['echo'])
def handle_echo_command(message):
    if len(message.text.split()) > 1:
        # Получаем текст сообщения после команды /echo
        echo_message = ' '.join(message.text.split()[1:])
        send_echo_message(echo_message)
        bot.reply_to(message, "Сообщение отправлено всем пользователям.")
    else:
        bot.reply_to(message, "Вы не указали текст сообщения.")

@bot.message_handler(commands=['dobro'])
def send_gif(message):
    chat_id = message.chat.id
    gif_path = os.path.join('/home/runner/telegram-bot', 'image3.gif')  # путь к вашему GIF-файлу
    gif_caption = 'Хорошего тебе настроения микро челик'  # Здесь будет тексто

    with open(gif_path, 'rb') as gif:
        bot.send_document(chat_id, gif, caption=gif_caption)

@bot.message_handler(commands=['sendgif2'])
def send_gif(message):
    chat_id = message.chat.id
    gif_path = os.path.join('/home/runner/telegram-bot', 'image2.gif')
    gif_caption = 'Шаг 1. В главном меню пользователь выбирает опцию "Обращение жильцов".\n\nШаг. 2 После получения списка опций от бота, пользователь выбирает опцию "Фото" с помощью кнопки на клавиатуре.\nБот отправляет запрос пользователю, запрашивая фотографию\n\nШаг 3.Пользователь отвечает на запрос бота, отправляя фотографию, связанную с обращением.\nБот обрабатывает фото, полученное от пользователя. Это может включать в себя анализ изображения и его сохранение для дальнейшей обработки.\n\n Шаг 4. Пользователь описывает проблему, указывает фаимилию собственника и номер квартиры.\nБот сохраняет информацию об обращении жильца, включая текстовое описание и прикрепленное фото, в базе данных.\nБот отправляет пользователю сообщение о том, что его обращение успешно зарегистрировано и будет рассмотрено.'  # Здесь будет текст

    with open(gif_path, 'rb') as gif:
        bot.send_document(chat_id, gif, caption=gif_caption)

@bot.message_handler(commands=['sendgif'])
def send_gif(message):
    chat_id = message.chat.id
    gif_path = os.path.join('/home/runner/telegram-bot', 'image3.gif')  # путь к вашему GIF-файлу
    gif_caption = 'Шаг 1. Для начала работы с ботом нажмите на подсвеченное синим цветом имя бота @DombotII.\n\nШаг 2. Нажмите кнопку Start.\nВы увидите главное меню.\n\nШаг 3. Введите пароль: 1234.\nВы увидите сообщение "Вы успешно прошли верификацию!", а значит можете использовать бота.'  # Здесь будет текст

    with open(gif_path, 'rb') as gif:
        bot.send_document(chat_id, gif, caption=gif_caption)


# Команда для получения информации о клининге и ценах на услуги
@bot.message_handler(commands=['2'])
def plumber_info(message):
    user_id = message.chat.id
    if is_user_in_blacklist(user_id):
        bot.send_message(user_id, "Вы находитесь в чёрном списке и не можете использовать бота.")
        return

    # Информация о работнике
    plumber_info_text = "Светлана Алексеевна\n\n📞Телефон: 89132677271"

    # Цены на услуги работника
    plumber_prices = {
        "Уборка квартир": "1500 рублей\n",
        "Химчистка ковров": "700 рублей\n",
        "Мойка окон": "3000 рублей\n",
        "Услуги по глажке": "2000 рублей\n",
        "Уборка после ремонта": "8500 рублей\n",
        # Добавьте остальные услуги и цены
    }

    response = plumber_info_text + "\n\nЦены на профессиональную уборку:\n"
    for service, price in plumber_prices.items():
        response += f"{service}: {price}\n"

    bot.send_message(user_id, response)

# Команда для получения информации о электрике и ценах на его услуги
@bot.message_handler(commands=['4'])
def plumber_info(message):
    user_id = message.chat.id
    if is_user_in_blacklist(user_id):
        bot.send_message(user_id, "Вы находитесь в чёрном списке и не можете использовать бота.")
        return

    # Информация о электрике
    plumber_info_text = "Петр Евгеньевич\n\n📞Телефон: 89132666179"

    # Цены на услуги электрика
    plumber_prices = {
        "Диагностика неисправности электропроводки": "1500 рублей\n",
        "Поиск обрыва и устранение короткого замыкания": "1500 рублей\n",
        "Ремонт розеток и выключателей": "1500 рублей\n",
        "Замена электросчётчика(прибор учёта) и эл.автоматов": "1500 рублей\n",
        "Полная или частичная замена электропроводки квартир": "1500 рублей\n",
        # Добавьте остальные услуги и цены
    }

    response = plumber_info_text + "\n\nЦены на услуги электрика:\n"
    for service, price in plumber_prices.items():
        response += f"{service}: {price}\n"

    bot.send_message(user_id, response)

# Команда для получения информации о хаус-мастере и ценах на его услуги
@bot.message_handler(commands=['3'])
def plumber_info(message):
    user_id = message.chat.id
    if is_user_in_blacklist(user_id):
        bot.send_message(user_id, "Вы находитесь в чёрном списке и не можете использовать бота.")
        return

    # Информация о хаус-мастере
    plumber_info_text = "Олег Иванович\n\n📞Телефон: 89132266174"

    # Цены на услуги хаус-мастера
    plumber_prices = {
        "Устранение мелких неисправностей": "1000 рублей/час\n",
        "Наладка дверей": "700 рублей\n",
        "Ремонт окон": "3000 рублей\n",
        "Ремонт кондиционера": "2000 рублей\n",
        "Ремонт мебели и техники": "1500 рублей\n",
        # Добавьте остальные услуги и цены
    }

    response = plumber_info_text + "\n\nЦены на услуги хаус-мастера:\n"
    for service, price in plumber_prices.items():
        response += f"{service}: {price}\n"

    bot.send_message(user_id, response)

# Команда для получения информации о сантехнике и ценах на его услуги
@bot.message_handler(commands=['1'])
def plumber_info(message):
    user_id = message.chat.id
    if is_user_in_blacklist(user_id):
        bot.send_message(user_id, "Вы находитесь в чёрном списке и не можете использовать бота.")
        return

    # Информация о сантехнике
    plumber_info_text = "Виктор Семёнович\n\n📞Телефон: 89132666179"

    # Цены на услуги сантехника
    plumber_prices = {
        "Установка раковины": "1500 рублей\n",
        "Установка смесителя": "700 рублей\n",
        "Установка душевой кабины": "3000 рублей\n",
        "Монтаж водоснабжения": "2000 рублей\n",
        "Установка унитаза": "1500 рублей\n",
        "Приборы учета": "900 рублей\n",
        # Добавьте остальные услуги и цены
    }

    response = plumber_info_text + "\n\nЦены на услуги сантехника:\n"
    for service, price in plumber_prices.items():
        response += f"{service}: {price}\n"

    bot.send_message(user_id, response)

# Проверка чёрного списка перед обработкой сообщения
@bot.message_handler(func=lambda message: not is_user_in_blacklist(message.from_user.id))
def handle_message(message):
    message_text = message.text
    chat_id = message.chat.id

    if chat_id not in verified_users:
        # Пользователь не прошел верификацию, запрашиваем пароль
        if message_text == PASSWORD:
            # Пользователь ввел правильный пароль, прошла верификация
            verified_users[chat_id] = True
            bot.send_message(chat_id, 'Вы успешно прошли верификацию!\n\nМожете продолжать использование бота.')
        else:
            # Пользователь ввел неправильный пароль
            bot.send_message(chat_id, 'Неправильный пароль. Попробуйте снова.')

    # Пользователь прошел верификацию, обрабатываем сообщения
    else:
        if message_text == 'Передача показаний':
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            item5 = telebot.types.KeyboardButton('Текст')
            item6 = telebot.types.KeyboardButton('Фото')
            back = telebot.types.KeyboardButton('⬅️Назад')

            markup.add(item5, item6, back)

            bot.send_message(chat_id,
                             '📮Для передачи показаний счетчиков Вы можете воспользоваться двумя способами:\n\n📝Текст. Вам будет предложено по порядку передать показания счетчика холодной, а затем горячей воды. Вы вносите показания просто набирая цифры.\n\n📷Фото. В этом режиме всё ещё проще. Вы отправляете фото счётчиков.\n\nКнопка /start вернет вас в главное меню',
                             reply_markup=markup)

        elif message_text == "Обращение жильцов":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            item7 = telebot.types.KeyboardButton('Сообщение')
            item11 = telebot.types.KeyboardButton('Фото')
            back = telebot.types.KeyboardButton('⬅️Назад')

            markup.add(item7,item11, back)

            bot.send_message(chat_id,
                             '📝Вы можете написать нам о любой проблеме в Вашем доме.\n\n📌Течёт батарея\n📌Плохо убран подъезд\n📌Не работает домофон\n📌Нахамил наш работник\n\nИ многое другое, о чем сочтете нужным уведомить нас. Кроме этого мы будем рады получать отзывыо нашей работе и Ваши пожелания.\n\nКнопка /start вернет вас в главное меню',
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_tenant_message2)

        elif message_text == "О компании":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = telebot.types.KeyboardButton('⬅️Назад')
            item10 = telebot.types.KeyboardButton('/user')
            markup.add(back, item10)

            bot.send_message(chat_id,
                             'Компания "Управляющая Компания" основана в 2005 году. Основное направление деятельности – управление и обслуживание многоквартирных домов. В настоящее время обслуживается 35 домов в городе.\n- Адрес: ул. Пушкина, д.14, офис 88\n\nКонтактные данные:\nРуководитель - Иванов Иван Иванович.\n📞Телефон: +7 (123) 111-22-33\n📬Email: company@mail.ru\n\nВиктор Семёнович - /1\nСантехник\n📞Телефон: 89132666179.\n\nСветлана Алексеевна - /2\nПрофессиональная уборка(Клининг)\n📞Телефон: 89132265431\n\nОлег Иванович - /3\nХаус-мастер\n📞Телефон: 89132266174 \n\nПётр Евгеньевич - /4\nЭлектрик\n📞Телефон: 89132666179 \n\nКнопка /start вернет вас в главное меню',
                             reply_markup=markup)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton('⬅️Назад')

            markup.add(back)
        elif message_text == "/user":
            add_user_to_database(message)

        elif message_text == "Связаться с диспетчером":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            item8 = telebot.types.KeyboardButton('Сообщение')
            back = telebot.types.KeyboardButton('⬅️Назад')

            markup.add(item8, back)

            bot.send_message(chat_id,
                             '📞Связаться с диспетчером\nВы можете по телефону\n+7 (123) 456-78-90 \n\n⚡️Или оставить сообщение и диспетчер сам свяжется с Вам.\n\nКнопка /start вернет вас в главное меню',
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_contact_message)

        elif message_text == "⬅️Назад":
            if back_to_menu(message):
                 bot.clear_step_handler(message) # сбрасываем ожидание следующего шага

        elif message_text == "Текст":
            bot.send_message(chat_id, 'Введите номер квартиры')
            bot.register_next_step_handler(message, process_apartment_number)
        elif message_text == "Фото":
            bot.send_message(chat_id, 'Введите номер квартиры')
            bot.register_next_step_handler(message, process_apartment_number2)

        elif message_text == "Руководство по использованию бота":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = telebot.types.KeyboardButton('⬅️Назад')
            markup.add(back)

            bot.send_message(chat_id,
                             '/sendgif\n\n/sendgif2',
                             reply_markup=markup)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back = types.KeyboardButton('⬅️Назад')

            markup.add(back)


def process_apartment_number(message):
    apartment = message.text
    bot.send_message(message.chat.id, 'Введите фамилию собственника')
    bot.register_next_step_handler(message, process_owner_surname, apartment)

def process_apartment_number2(message):
    apartment2 = message.text
    bot.send_message(message.chat.id, 'Введите фамилию собственника')
    bot.register_next_step_handler(message, process_owner_surname2, apartment2)

def process_owner_surname(message, apartment):
    owner_surname = message.text
    bot.send_message(message.chat.id, 'Введите показания счетчика холодной воды')
    bot.register_next_step_handler(message, process_cold_water, apartment, owner_surname)

def process_owner_surname2(message, apartment2):
    owner_surname2 = message.text
    bot.send_message(message.chat.id, 'Прикрепите фотографию')
    bot.register_next_step_handler(message, process_counter_photo2, apartment2, owner_surname2)

def process_cold_water(message, apartment, owner_surname):
    cold_water = message.text
    bot.send_message(message.chat.id, 'Введите показания счетчика горячей воды')
    bot.register_next_step_handler(message, process_hot_water, apartment, owner_surname, cold_water)

def process_hot_water(message, apartment, owner_surname, cold_water):
    hot_water = message.text

    message_to_send5 = f'💧💧💧Показания воды\n\nНомер квартиры: {apartment}\nФамилия собственника: {owner_surname}\nПоказания счетчика холодной воды: {cold_water}\nПоказания счетчика горячей воды: {hot_water}'

    bot.send_message(message.chat.id,
                     '🤝Спасибо за передачу показаний!\n\nКнопка /start вернет вас в главное меню',
                     reply_markup=telebot.types.ReplyKeyboardRemove())

    # Отправляем сообщение диспетчеру в закрытый канал
    bot.send_message(YOUR_CHANNEL_ID, message_to_send5)

def process_tenant_message2(message):
    if message.text == 'Сообщение':
        bot.send_message(message.chat.id, 'Введите ваше сообщение')
        bot.register_next_step_handler(message, send_tenant_message)
    elif message.text == 'Фото':
        bot.send_message(message.chat.id, 'Пожалуйста, прикрепите фотографию проблемы.')
        bot.register_next_step_handler(message, process_tenant_photo)

def process_tenant_photo(message):
    if message.content_type == 'photo':
        # Получите идентификатор фотографии
        photo_id = message.photo[-1].file_id

        # Запросите описание проблемы
        bot.send_message(message.chat.id, 'Пожалуйста, напишите описание проблемы.')

        # Сохраните идентификатор фотографии в контексте пользователя
        bot.register_next_step_handler(message, process_tenant_description, photo_id)
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, прикрепите фотографию проблемы.')

def process_tenant_description(message, photo_id):
    # Получите текст описания проблемы
    description = message.text

    # Запросите фамилию собственника
    bot.send_message(message.chat.id, 'Пожалуйста, укажите фамилию собственника.')

    # Сохраните идентификатор фотографии и описание в контексте пользователя
    bot.register_next_step_handler(message, process_owner_surname3, photo_id, description)

def process_owner_surname3(message, photo_id, description):
    # Получите фамилию собственника
    owner_surname = message.text

    # Запросите номер квартиры
    bot.send_message(message.chat.id, 'Пожалуйста, укажите номер квартиры.')

    # Сохраните фамилию собственника, описание и идентификатор фотографии в контексте пользователя
    bot.register_next_step_handler(message, process_apartment, photo_id, description, owner_surname)

def process_apartment(message, photo_id, description, owner_surname):
    # Получите номер квартиры
    apartment = message.text

    # Получите user_id отправителя
    user_id = message.from_user.id

    # Создайте сообщение для отправки в закрытую группу
    message_to_send6 = f'📷Фото проблемы: \n\nОписание: {description}\n\nФамилия собственника: {owner_surname}\nНомер квартиры: {apartment}\nUser ID: {user_id}'

    bot.send_message(message.chat.id,
                     '🤝Спасибо за ваше обращение!\n\nКнопка /start вернет вас в главное меню.',
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_yes = types.KeyboardButton("Да")
    button_no = types.KeyboardButton("Нет")
    markup.add(button_yes, button_no)

    bot.send_message(message.chat.id,
                 'Хотите ли вы, чтобы наш оператор связался с вами?',
                 reply_markup=markup)
    # Отправьте сообщение диспетчеру в закрытую группу
    bot.send_photo(YOUR_CHANNEL_ID, photo_id, caption=message_to_send6)

def process_tenant_message(message):
    if message.text == 'Сообщение':
        bot.send_message(message.chat.id, 'Введите ваше сообщение')
        bot.register_next_step_handler(message, send_tenant_message)
    elif message.text == '⬅️Назад':
        # Вернуться в главное меню
        start(message)

def send_tenant_message(message):
    tenant_message = message.text

    message_to_send2 = f'🗒Обращение жильцов\n\n{tenant_message}'

    bot.send_message(message.chat.id,
                     '🤝Спасибо за обращение!\n\nКнопка /start вернет вас в главное меню',
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_yes = types.KeyboardButton("Да")
    button_no = types.KeyboardButton("Нет")
    markup.add(button_yes, button_no)

    bot.send_message(message.chat.id,
                 'Хотите ли вы, чтобы наш оператор связался с вами?',
                 reply_markup=markup)
    # Отправляем сообщение диспетчеру в закрытый канал
    bot.send_message(YOUR_CHANNEL_ID, message_to_send2)

def process_contact_message(message):
    if message.text == 'Сообщение':
        bot.send_message(message.chat.id, 'Введите ваше сообщение')
        bot.register_next_step_handler(message, send_contact_message)
    elif message.text == '⬅️Назад':
        # Вернуться в главное меню
        start(message)

def send_contact_message(message):
    contact_message = message.text

    message_to_send3 = f'⚡️⚡️⚡️Срочно диспетчеру\n\n{contact_message}'

    bot.send_message(message.chat.id,
                     '🤝Спасибо за обращение!\n\nКнопка /start вернет вас в главное меню',
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_yes = types.KeyboardButton("Да")
    button_no = types.KeyboardButton("Нет")
    markup.add(button_yes, button_no)

    bot.send_message(message.chat.id,
                 'Хотите ли вы, чтобы наш оператор связался с вами?',
                 reply_markup=markup)
    # Отправляем сообщение диспетчеру в закрытый канал
    bot.send_message(YOUR_CHANNEL_ID, message_to_send3)

def process_counter_photo2(message, apartment2, owner_surname2):
    if message.content_type == 'photo':
        # Получите идентификатор фотографии
        photo_id = message.photo[-1].file_id

        # Сгенерируйте сообщение с подписью фотографии
        message_to_send4 = f'💧💧📷Показания с фотографией\n\nНомер квартиры: {apartment2}\nФамилия собственника: {owner_surname2}'

        # Отправьте фотографию и сообщение в закрытый канал
        bot.send_photo(YOUR_CHANNEL_ID, photo_id, caption=message_to_send4)

        bot.send_message(message.chat.id,
                         '🤝Спасибо за передачу показаний с фотографией!\n\nКнопка /start вернет вас в главное меню',
                         reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True))
    else:
        bot.send_message(message.chat.id,
                         'Придется начать все заново. Вы не прикрепили фотографию счетчика./start .')

def send_echo_message(message):
    users = load_users()
    for user_id in users:
        try:
            bot.send_message(user_id, message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {str(e)}")

def load_users():
    with open(DATABASE_FILE, 'r') as file:
        users = [line.strip() for line in file]
    return users

keep_alive()

bot.polling()
