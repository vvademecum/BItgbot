from telebot import types, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import csv
import psycopg2
import re

BOT_TOKEN = '6370696970:AAGCxyyM5Cavutux4UW17dgROLIil6eHp44'

bot = telebot.TeleBot(BOT_TOKEN)

connection = psycopg2.connect(
        host="localhost",
        user="admin",
        password="root",
        database="bitelegramdb",
        port=6101
    )
cursor = connection.cursor()

print('[INFO] PostgreSQL start')


def exitStepHandler(message):
    if message.text == "↩ Выйти":
        bot.send_message(chat_id=message.chat.id, text=f"👌", parse_mode="Markdown", reply_markup=genKeyboard(message.from_user.id))
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    return

def process_updateFullName_step(message):
    try:
        # surname = message.text.strip().split(' ')[0]
        # name = message.text.strip().replace(surname, "").strip().split(' ')[0]
        # patronymic = message.text.strip().replace(surname, "").replace(name, "").strip().split(' ')[0]

        if message.text == "↩ Выйти":
            exitStepHandler(message)
            return
            
        pattern = r'([А-ЯЁа-яё]+)\s+([А-ЯЁа-яё]+)\s+([А-ЯЁа-яё]+)'
        match = re.search(pattern, message.text.strip())
        
        if match:
            surname, name, patronymic = match.groups()
        else:
            msg = bot.reply_to(message, f'Неверный формат, повторите ввод ФИО\n(Пример: _Иванов Иван Иванович_)', parse_mode="Markdown")
            bot.register_next_step_handler(message=msg, callback=process_updateFullName_step)
            return 

        cursor.execute(f'''UPDATE users SET firstname='{name}',
                            lastname='{surname}', patronymic='{patronymic}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, f'Укажите Вашу сферу деятельности, {name}')

        bot.register_next_step_handler(msg, process_updateFieldOfActivity_step)
    except Exception as ex:
        print("Error: ", ex)
        bot.reply_to(message, "ooppps")
        exitStepHandler(message)

def process_updateFieldOfActivity_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message)
            return

        fieldOfActivity = message.text

        if len(fieldOfActivity) <= 1:
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод сферы деятельности\n(Пример: _Медицина и образование_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updateFieldOfActivity_step)
            return
        
        cursor.execute(f'''UPDATE users SET fieldofactivity='{fieldOfActivity}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Записано. Расскажите о себе')
        bot.register_next_step_handler(msg, process_updateAboutMe_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')
        exitStepHandler(message)

def process_updateAboutMe_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message)
            return
        
        aboutMe = message.text

        if len(aboutMe) <= 1:
            msg = bot.reply_to(message, 'Неверный формат, повторите')
            bot.register_next_step_handler(msg, process_updateAboutMe_step)
            return
        
        cursor.execute(f'''UPDATE users SET aboutme='{aboutMe}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Отлично, оставьте свой номер телефона\n(_+79993332211_)', parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_updatePhoneNum_step) 
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_updatePhoneNum_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message)
            return

        phoneNum = message.text

        pattern = r'^\+\d{11}$'
        if not re.match(pattern, phoneNum):
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод номера\n(Пример: _+79993332211_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updatePhoneNum_step)
            return
        
        cursor.execute(f'''UPDATE users SET phonenum='{phoneNum}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Осталось добавить почту\n(_ivanov.i.i@gmail.com_)', parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_updateEmail_step) 
    except Exception as e:
        bot.reply_to(message, 'oooops')

def process_updateEmail_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message)
            return
        email = message.text

        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод почты\n(Пример: _ivanov.i.i@gmail.com_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updateEmail_step)
            return
        
        cursor.execute(f'''UPDATE users SET email='{email}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()


        user = getUserById(message.from_user.id)
        email = user[8].replace("_", "\_")

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('🔴 Повторить ввод', '🟢 Все верно')
        bot.send_message(message.chat.id, f'''Данные обновлены, проверьте корректность:
*ФИО*: _{user[3] if user[3] != None else ""} {user[2] if user[2] != None else ""} {user[4] if user[4] != None else ""}_
*Сфера деятельности*: _{user[5]}_
*О себе*: _{user[6]}_
*Телефон*: _{user[7]}_
*Email*: {email}''', 
        reply_markup=markup, 
        parse_mode="Markdown")
        
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')



# def process_checkCorrect_step(message):
#     try:
#         correct = message.text

#         keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
#         updateFullNameBtn = types.KeyboardButton(text="📝 Заполнить информацию о себе")
#         keyboard.add(updateFullNameBtn)
#         if (correct == u'🔴 Повторить ввод'):
#             return
#         elif (correct == u'🟢 Все верно'):
#             return
            

#     except Exception as e:
#         bot.reply_to(message, 'oooops')



def getProjects(page):
    buttons_per_page = 8
    cursor.execute(f'''SELECT name, id FROM projects
                        ORDER BY id
                        LIMIT {buttons_per_page} OFFSET {page-1} * {buttons_per_page};''')
    items = cursor.fetchall()
    cursor.execute(f'''SELECT COUNT(*) FROM projects;''')
    countOfProjects = cursor.fetchone()[0]
    return items, countOfProjects

def getUserById(userId):
    cursor.execute(f'''SELECT * FROM users 
                        WHERE id = '{userId}';''')
    return cursor.fetchone();

def create_inline_keyboard(items, page):
    countOfProjects = getProjects(1)[1]

    buttons_per_page = 8  
    start_idx = (page - 1) * buttons_per_page
    
    leftBtn = countOfProjects - start_idx
    end_idx = start_idx + leftBtn if leftBtn < buttons_per_page else start_idx + buttons_per_page

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for i in range(0, len(items), 2):
        button1 = types.InlineKeyboardButton(items[i][0], callback_data=f'project_{items[i][1]}')

        if i + 1 == len(items):
            keyboard.add(button1)
            break
        
        button2 = types.InlineKeyboardButton(items[i+1][0], callback_data=f'project_{items[i+1][1]}')
        keyboard.row(button1, button2)

    if page > 1 and end_idx < countOfProjects:
        prev_button = types.InlineKeyboardButton('⬅', callback_data=f'prev_{page}')
        next_button = types.InlineKeyboardButton('➡', callback_data=f'next_{page}')
        keyboard.row(prev_button, next_button)
    elif end_idx < countOfProjects:
        next_button = types.InlineKeyboardButton('➡', callback_data=f'next_{page}')
        keyboard.add(next_button)
    elif page > 1:
        announceProject_button = types.InlineKeyboardButton('✉ Заявить о новом проекте', callback_data=f'announce_project')
        prev_button = types.InlineKeyboardButton('⬅', callback_data=f'prev_{page}')
        keyboard.add(announceProject_button)
        keyboard.add(prev_button)

    return keyboard


@bot.callback_query_handler(func=lambda call: call.data.startswith('prev_') or call.data.startswith('next_'))
def handle_navigation(call):
    countOfProjects = getProjects(1)[1]

    action, page = call.data.split('_')

    if action == 'prev':
        current_page = max(1, int(page) - 1)
    elif action == 'next':
        current_page = min((countOfProjects - 1) // 8 + 1, int(page) + 1)

    projects = getProjects(current_page)[0]

    keyboard = create_inline_keyboard(projects, current_page)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    # bot.register_next_step_handler(call.message, handle_next_step, user_data)

@bot.callback_query_handler(func=lambda call: call.data == 'announce_project')
def handle_announceProject(call):
    item = call.data[8:]
    bot.send_message(call.message.chat.id, f"Вы выбрали элемент: {item}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('project_'))
def handle_project_selection(call):
    idProject = call.data[8:]
    
    # cursor.execute(f'''SELECT * FROM projects 
    #                     WHERE id = '{idProject}';''')
    # project = cursor.fetchone();

    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    cancelReqBtn = types.KeyboardButton(text="🔴 Отмена")
    approveReqBtn = types.KeyboardButton(text="🔵 Отправить запрос")

    keyboard.row(cancelReqBtn, approveReqBtn)

    
    cursor.execute(f'''SELECT * FROM users_projects
INNER JOIN projects ON users_projects.projectid = projects.id
WHERE projectid = {idProject} and role = 'AUTOR';''')

    columns = [desc[0] for desc in cursor.description]
    items = cursor.fetchall()
    autor = dict(zip(columns, items[0]))
    

    cursor.execute(f'''SELECT username, lastname, firstname, patronymic FROM users_projects
INNER JOIN users ON users_projects.userid = users.id
WHERE projectid = {idProject} and role = 'PARTNER';''')

    items = cursor.fetchall()
    partners = ""
    for partner in items:
        partners += f'_{partner[1] if partner[1] != None else ""} {partner[2] if partner[2] != None else ""} {partner[3] if partner[3] != None else ""}_ (@{partner[0]})\n'
    


    print(filter(autor['description']))

    user = getUserById(autor['userid'])
    fioUser = filter(f'{user[3] if user[3] != None else ""} {user[2] if user[2] != None else ""} {user[4] if user[4] != None else ""}')
    msg = bot.send_message(call.message.chat.id, f'''*Наименование проекта*: _{autor['name']}_
*Описание*: _{filter(autor['description'])}_
*Категория*: _{filter(autor['category'])}_
*Заявитель*: {fioUser}
*Партнеры*: {filter(partners)}
''', parse_mode="MarkdownV2", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_requestToJoin_step)


def filter(text):
    text = text.replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)').replace('~', '\~').replace('`', '\`').replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('-', '\-').replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}').replace('.', '\.').replace('!', '\!')
    return text

def process_requestToJoin_step(message):
    try:
        if message.text == "🔴 Отмена":
            exitStepHandler(message)
            return
        elif message.text == "🔵 Отправить запрос":
            
        
            email = message.text

        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод почты\n(Пример: _ivanov.i.i@gmail.com_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updateEmail_step)
            return
        
        cursor.execute(f'''UPDATE users SET email='{email}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()


        user = getUserById(message.from_user.id)
        email = user[8].replace("_", "\_")

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('🔴 Повторить ввод', '🟢 Все верно')
        bot.send_message(message.chat.id, f'''Данные обновлены, проверьте корректность:
*ФИО*: _{user[3] if user[3] != None else ""} {user[2] if user[2] != None else ""} {user[4] if user[4] != None else ""}_
*Сфера деятельности*: _{user[5]}_
*О себе*: _{user[6]}_
*Телефон*: _{user[7]}_
*Email*: {email}''', 
        reply_markup=markup, 
        parse_mode="Markdown")
        
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')

# def process_updateProjectGroup_step(message):
#     try:
#         keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
#         goHomeBtn = types.KeyboardButton(text="↩ Выйти")
#         keyboard.add(goHomeBtn)
#         bot.send_message(chat_id=message.chat.id, text='хех', reply_markup=keyboard)

#         if message.text == "↩ Выйти":
#             exitStepHandler(message)
#             return

#         phoneNum = message.text
#         if message.call.data.startswith('project_'):
#             item = message.call.data[5:]
#             print(item)

#         # pattern = r'^\+\d{11}$'
#         # if not re.match(pattern, phoneNum):
#         #     msg = bot.reply_to(message, 'Неверный формат, повторите ввод номера\n(Пример: _+79993332211_)', parse_mode="Markdown")
#         #     bot.register_next_step_handler(msg, process_updatePhoneNum_step)
#         #     return
        
#         # cursor.execute(f'''UPDATE users SET phonenum='{phoneNum}'
#         #                     WHERE id = '{message.from_user.id}';''')
#         # connection.commit()

#         # msg = bot.reply_to(message, 'Осталось добавить почту\n(_ivanov.i.i@gmail.com_)', parse_mode="Markdown")
#         # bot.register_next_step_handler(msg, process_updateEmail_step) 
#     except Exception as e:
#         bot.reply_to(message, 'oooops')




@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text= f"Привет.", reply_markup=genKeyboard(message.from_user.id))
    

    # page = 1
    # keyboard = create_inline_keyboard(getProjects(page)[0], page)

    # bot.send_message(message.chat.id, "Выберите элемент:", reply_markup=keyboard)




@bot.message_handler(func=lambda message: message.text == "📝 Заполнить информацию о себе" or message.text == "🔴 Повторить ввод")
def updateFullName(message):

    user = getUserById(message.from_user.id)
    if (user[9] != "RESIDENT"):
        return

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    goHomeBtn = types.KeyboardButton(text="↩ Выйти")
    keyboard.add(goHomeBtn)

    msg = bot.send_message(chat_id=message.chat.id, text=f"Введите ФИО через пробел\n(_Иванов Иван Иванович_)", parse_mode="Markdown", reply_markup=keyboard)
    bot.register_next_step_handler(message=msg, callback=process_updateFullName_step)

@bot.message_handler(func=lambda message: message.text == "🗂 Добавить информацию о проекте")
def selectionProjectGroup(message):

    user = getUserById(message.from_user.id)
    if (user[9] != "RESIDENT"):
        return

    # keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    # goHomeBtn = types.KeyboardButton(text="↩ Выйти")
    # keyboard.add(goHomeBtn)
    # bot.send_message(chat_id=message.chat.id, reply_markup=keyboard)

    page = 1
    inlineKeyboard = create_inline_keyboard(getProjects(page)[0], page)
    msg = bot.send_message(chat_id=message.chat.id, text=f"Выберите проект, в команде которого Вы состоите или добавьте свой", parse_mode="Markdown", reply_markup=inlineKeyboard)
    # bot.register_next_step_handler(message=msg, callback=process_updateProjectGroup_step)



@bot.message_handler(func=lambda message: message.text == "🟢 Все верно" or message.text == "↩ Выйти")
def goMainMenu(message):

    keyboard = genKeyboard(message.from_user.id)
    match message.text:
        case "🟢 Все верно":
            bot.send_message(chat_id=message.chat.id, text=f"👍", parse_mode="Markdown", reply_markup=keyboard)
        case "↩ Выйти":
            
            bot.send_message(chat_id=message.chat.id, text=f"👌", parse_mode="Markdown", reply_markup=keyboard)


def genKeyboard(userId):
    user = getUserById(userId)

    if (user[9] == "RESIDENT"):
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        updateProfileBtn = types.KeyboardButton(text="📝 Заполнить информацию о себе")
        updateProjectGroupBtn = types.KeyboardButton(text="🗂 Добавить информацию о проекте")
        keyboard.add(updateProfileBtn, updateProjectGroupBtn)
    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        updateFullNameBtn = types.KeyboardButton(text="📃 Таблица вакансий")
        keyboard.add(updateFullNameBtn)
    return keyboard



# def genMarkup():
#     keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
#     updateFullNameBtn = types.KeyboardButton(text="📝 Заполнить информацию о себе")
#     keyboard.add(updateFullNameBtn) 
    
#     return keyboard













@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):

    user_id = message.new_chat_members[0].id
    username = message.new_chat_members[0].username
    firstName = message.new_chat_members[0].first_name
    lastName = message.new_chat_members[0].last_name

    try:
        if(str(message.chat.id) == '-4066956508'):
            cursor.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, %s) 
                            On CONFLICT(id) DO UPDATE
                            SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''', 
                            (user_id, username, firstName, lastName, 'RESIDENT'))

        connection.commit()

        bot.send_message(message.chat.id, f"Привет, {firstName}")

    except Exception as ex:
        print('[INFO] Error postgresql ', ex)


@bot.message_handler(commands=['send'])
def send_message_to_group(message):

    chat_id = message.chat.id
    members_count = bot.get_chat_members_count(chat_id)
    print(chat_id)
    # 809778477
   

    # with open('mytest.csv', newline='', encoding='utf-8') as csvfile:
    #     reader = csv.DictReader(csvfile)
    
    #     for row in reader:
    #         user_id = row['user id']
    #         if user_id != '6370696970':
    #             try:
    #                 bot.send_message(user_id, message.text.replace('/send ', ''))
    #             except telebot.apihelper.ApiTelegramException as e:
    #                 print(f"Not delivered. User {row['username']} hasnt yet started a conversation.")


bot.infinity_polling()