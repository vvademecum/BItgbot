from telebot import types, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import csv
import psycopg2
import re
import config


bot = telebot.TeleBot(config.BOT_TOKEN)

connection = psycopg2.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
        port=config.PORT
    )
cursor = connection.cursor()

print('[INFO] PostgreSQL start')


def process_updateFullName_step(message):
    try:
        # surname = message.text.strip().split(' ')[0]
        # name = message.text.strip().replace(surname, "").strip().split(' ')[0]
        # patronymic = message.text.strip().replace(surname, "").replace(name, "").strip().split(' ')[0]

        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
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
        exitStepHandler(message, "error")

def process_updateFieldOfActivity_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
            return

        fieldOfActivity = message.text

        if len(fieldOfActivity) <= 1:
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод сферы деятельности\n(Пример: _Медицина и образование_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updateFieldOfActivity_step)
            return
        
        cursor.execute(f'''UPDATE users SET fieldofactivity='{fieldOfActivity}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Записано. Расскажите о себе: опишите свои области компетенций, укажите hard skills.')
        bot.register_next_step_handler(msg, process_updateAboutMe_step)
    except Exception as e:
        print(e)
        exitStepHandler(message, "error")

def process_updateAboutMe_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
            return
        
        aboutMe = message.text

        if len(aboutMe) <= 1:
            msg = bot.reply_to(message, 'Неверный формат, повторите')
            bot.register_next_step_handler(msg, process_updateAboutMe_step)
            return
        
        cursor.execute(f'''UPDATE users SET aboutme='{aboutMe}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Укажите учебное заведение в виде аббревиатуры\n(Пример: _РЭУ им. Г.В. Плеханова_)', parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_updateEducationalInstitution_step) 
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_updateEducationalInstitution_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
            return
        
        educationalInstitution = message.text

        if len(educationalInstitution) < 3:
            msg = bot.reply_to(message, 'Неверный формат, повторите ввод учебного заведения\n(Пример: _НИУ ВШЭ_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_updateEducationalInstitution_step)
            return
        
        cursor.execute(f'''UPDATE users SET educationalinstitution='{educationalInstitution}'
                            WHERE id = '{message.from_user.id}';''')
        connection.commit()

        msg = bot.reply_to(message, 'Отлично, оставьте свой номер телефона\n(_+79993332211_)', parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_updatePhoneNum_step) 
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')

def process_updatePhoneNum_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
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
        print(e)
        bot.reply_to(message, 'oooops')

def process_updateEmail_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
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


        cursor.execute(f'''SELECT name FROM users_projects
                            INNER JOIN projects ON users_projects.projectid = projects.id
                            WHERE userid = '{message.from_user.id}';''')
        projects = cursor.fetchall()


        projectNames = ""
        for project in projects:
            projectNames += project[0] + ", "
        
        if projectNames.strip() != "":
            projectNames = f"*Участник проектов*: {projectNames}"[:-2]

        user = getUserById(message.from_user.id)
        email = user['email'].replace("_", "\_")

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('🔴 Повторить ввод', '🟢 Все верно')
        bot.send_message(message.chat.id, f'''Данные обновлены, проверьте корректность:

*ФИО*: _{user['lastname'] if user['lastname'] != None else ""} {user['firstname'] if user['firstname'] != None else ""} {user['patronymic'] if user['patronymic'] != None else ""}_

*Сфера деятельности*: _{user['fieldofactivity']}_

*Учебное заведение*: _{user['educationalinstitution']}_

*О себе*: _{user['aboutme']}_

*Телефон*: _{user['phonenum']}_

*Email*: {email}

{projectNames.strip()}''', 
        reply_markup=markup, 
        parse_mode="Markdown")
        
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')


# -------------------------------------------------- Create project steps -----------------------

def process_insertProjectName_step(message):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
            return
            
        projectName = message.text
        if len(projectName) < 3:
            msg = bot.reply_to(message, f'Неверный формат, повторите ввод наименования', parse_mode="Markdown")
            bot.register_next_step_handler(message=msg, callback=process_insertProjectName_step)
            return 
        
        cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM projects
                                WHERE name = '{projectName.strip()}');''')
        isAlreadyExists = cursor.fetchone()
        
        if isAlreadyExists[0]:
            msg = bot.reply_to(message, f'Проект с таким наименованием уже существет, повторите ввод', parse_mode="Markdown")
            bot.register_next_step_handler(message=msg, callback=process_insertProjectName_step)
            return 

        msg = bot.reply_to(message, f'Составьте *описание* проекта {projectName}:', parse_mode="Markdown")

        bot.register_next_step_handler(msg, process_insertProjectDescription_step, projectName)
    except Exception as ex:
        print("Error: ", ex)
        exitStepHandler(message, "error")

def process_insertProjectDescription_step(message, projectName):
    try:
        if message.text == "↩ Выйти":
            exitStepHandler(message, "ok")
            return
            
        projectDescription = message.text

        if len(projectDescription) < 3:
            msg = bot.reply_to(message, f'Неверный формат, повторите ввод описания', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_insertProjectDescription_step, projectName)
            return 

        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        goHomeBtn = types.KeyboardButton(text="↩ Выйти")
        keyboard.add(types.KeyboardButton(text='Креативные индустрии'), types.KeyboardButton(text='Медицина и образование'), types.KeyboardButton(text='Социальные'), types.KeyboardButton(text='Технологические'), types.KeyboardButton(text='Экологические'), goHomeBtn)

        msg = bot.send_message(message.from_user.id, f'Укажите *категорию* вашего проекта', parse_mode="Markdown", reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_insertProjectCategory_step, projectName, projectDescription)
    except Exception as ex:
        print("Error: ", ex)
        exitStepHandler(message, "error")

def process_insertProjectCategory_step(message, projectName, projectDescription):
    try:
        projectCategory = ""

        if message.text == '↩ Выйти':
            exitStepHandler(message, "ok")
            return
        
        Categories = ['Креативные индустрии', 'Медицина и образование', 'Социальные', 'Технологические', 'Экологические']
        if message.text not in Categories:
            msg = bot.reply_to(message, f'Неверный формат, повторите ввод категории', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_insertProjectCategory_step, projectName, projectDescription)
            return 

        projectCategory = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('🔴 Повторить ввод', '🟢 Все верно')
        
        user = getUserById(message.from_user.id)
        fioUser = filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')
        
        msg = bot.send_message(message.chat.id, f''' Новый проект добавлен, проверьте правильность заполнения данных:
                            
*Наименование проекта*: _{filter(projectName)}_

*Описание*: _{filter(projectDescription)}_

*Категория*: _{filter(projectCategory)}_

*Заявитель*: {fioUser}
    ''', parse_mode="MarkdownV2", reply_markup=markup)
        bot.register_next_step_handler(msg, process_isRepeatFillingProject_step, projectName, projectDescription, projectCategory)
    except Exception as ex:
        print("Error: ", ex)
        exitStepHandler(message, "error")

def process_isRepeatFillingProject_step(message, projectName, projectDescription, projectCategory):
    try:
        if message.text == "🔴 Повторить ввод":
            announceProject(message.chat.id)
        elif message.text == "🟢 Все верно":
            cursor.execute(f'''INSERT INTO projects (name, description, category) VALUES (%s, %s, %s) RETURNING id;''', (projectName, projectDescription, projectCategory))
            newProjectId = cursor.fetchone()[0]
            connection.commit()
            cursor.execute(f'''INSERT INTO users_projects (projectid, userid, role) VALUES (%s, %s, %s);''', (newProjectId, message.from_user.id, 'AUTHOR'))
            connection.commit()
            
            exitStepHandler(message, "ok")
        else:   
            msg = bot.send_message(chat_id=message.chat.id, text="Проверьте корректность данных", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_isRepeatFillingProject_step, projectName, projectDescription, projectCategory)

    except Exception as ex:
        print("Error: ", ex)
        exitStepHandler(message, "error")

def exitStepHandler(message, status):
    text = "👌"
    if status == "error": 
        text = "Произошла ошибка, попробуйте позже."

    bot.send_message(chat_id=message.chat.id, text=text, parse_mode="Markdown", reply_markup=genKeyboard(message.from_user.id))
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    return

def filter(text):
    text = text.replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)').replace('~', '\~').replace('`', '\`').replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('-', '\-').replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}').replace('.', '\.').replace('!', '\!')
    return text

def getProjects(page):
    buttons_per_page = 8
    cursor.execute(f'''SELECT name, id FROM projects
                        ORDER BY name
                        LIMIT {buttons_per_page} OFFSET {page-1} * {buttons_per_page};''')
    items = cursor.fetchall()
    cursor.execute(f'''SELECT COUNT(*) FROM projects;''')
    countOfProjects = cursor.fetchone()[0]
    return items, countOfProjects

def getUserById(userId):
    cursor.execute(f'''SELECT * FROM users 
                        WHERE id = '{userId}';''')

    columns = [desc[0] for desc in cursor.description]
    items = cursor.fetchone()
    user = dict(zip(columns, items))
    return user

def getProjectById(projectId):
    cursor.execute(f'''SELECT * FROM projects 
                        WHERE id = '{projectId}';''')
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
    elif page == 1 and leftBtn <= buttons_per_page:
        announceProject_button = types.InlineKeyboardButton('✉ Заявить о новом проекте', callback_data=f'announce_project')
        keyboard.add(announceProject_button)
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

def announceProject(chatId):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    goHomeBtn = types.KeyboardButton(text="↩ Выйти")
    keyboard.add(goHomeBtn)

    msg = bot.send_message(chatId, f"Введите *наименование* проекта", parse_mode="MarkdownV2", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_insertProjectName_step)

@bot.callback_query_handler(func=lambda call: call.data == 'announce_project')
def handle_announceProject(call):
    try:
        announceProject(call.message.chat.id)
    except Exception as e:
            print(e)
            exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('project_'))
def handle_project_selection(call):
    try:
        idProject = call.data[8:]

        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        cancelReqBtn = types.KeyboardButton(text="🔴 Отмена")
        approveReqBtn = types.KeyboardButton(text="🔵 Отправить запрос")
        keyboard.row(cancelReqBtn, approveReqBtn)

        cursor.execute(f'''SELECT * FROM users_projects
                            INNER JOIN projects ON users_projects.projectid = projects.id
                            WHERE projectid = {idProject} and role = 'AUTHOR';''')

        columns = [desc[0] for desc in cursor.description]
        items = cursor.fetchall()
        author = dict(zip(columns, items[0]))

        cursor.execute(f'''SELECT username, lastname, firstname, patronymic, userid FROM users_projects
                            INNER JOIN users ON users_projects.userid = users.id
                            WHERE projectid = {idProject} and role = 'PARTNER';''')

        items = cursor.fetchall()
        partners = ""
        alreadyMember = False 

        if str(author['userid']) == str(call.from_user.id):
            alreadyMember = True

        for partner in items:
            if (str(partner[4]) == str(call.from_user.id) or str(author['userid']) == str(call.from_user.id)):
                alreadyMember = True
            partners += filter(f'{partner[1] if partner[1] != None else ""} {partner[2] if partner[2] != None else ""} {partner[3] if partner[3] != None else ""} (@{partner[0]});\n')
        
        if partners.strip() != "":
            partners = f"*Партнеры*: \n{partners}"[:-2] + "\."

        user = getUserById(author['userid'])
        fioUser = filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')
        
        aboutProject = f"__Вы можете подать запрос на вступление в команду проекта «{filter(author['name'])}»\.__"
        if alreadyMember:
            aboutProject = "__Вы уже состоите в команде этого проекта\.__"
            keyboard = genKeyboard(call.from_user.id)

        msg = bot.send_message(call.message.chat.id, f''' {aboutProject}
                            
*Наименование проекта*: _{filter(author['name'])}_

*Описание*: _{filter(author['description'])}_

*Категория*: _{filter(author['category'])}_

*Заявитель*: {fioUser}

{partners}
    ''', parse_mode="MarkdownV2", reply_markup=keyboard)
        
        if alreadyMember: return
        bot.register_next_step_handler(msg, process_requestToJoin_step, idProject, author['userid'])

    except Exception as e:
            print(e)
            exitStepHandler(call.message, "error")

def process_requestToJoin_step(message, projectId, authorId):
    try:
        if message.text == "🔴 Отмена":
            exitStepHandler(message, "ok")
        elif message.text == "🔵 Отправить запрос":

            user = getUserById(message.from_user.id)
            fioUser = filter(f'{user[3] if user[3] != None else ""} {user[2] if user[2] != None else ""} {user[4] if user[4] != None else ""} (@{user[1]})')

            keyboard = types.InlineKeyboardMarkup(row_width=2)
            rejectBtn = types.InlineKeyboardButton("🔴 Отклонить", callback_data=f'rejectRequest_{projectId}_{message.from_user.id}')
            acceptBtn = types.InlineKeyboardButton("🟢 Принять", callback_data=f'acceptRequest_{projectId}_{message.from_user.id}')
            keyboard.row(rejectBtn, acceptBtn)

            bot.send_message(authorId, f"Пользователь {fioUser} отправил запрос на вступление в команду проекта *«{filter(getProjectById(projectId)[1])}»*", 
                            reply_markup=keyboard, 
                            parse_mode="MarkdownV2")
            
            bot.send_message(message.from_user.id, f"Ваша заявка на вступление в команду проекта *«{filter(getProjectById(projectId)[1])}»* была отправлена\. Скоро заявитель её рассмотрит и мы уведомим Вас о результате\.", 
                            reply_markup=genKeyboard(message.from_user.id), 
                            parse_mode="MarkdownV2")
        else:
            msg = bot.reply_to(message, 'Вы можете *подать заявку* на присоединение к команде выбранного проекта или *отменить* действие.', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_requestToJoin_step, projectId, authorId)
        return
    except Exception as e:
        print(e)
        exitStepHandler(message, "error")
        # bot.reply_to(message, f'oooops')

@bot.callback_query_handler(func=lambda call: call.data.startswith('rejectRequest_') or call.data.startswith('acceptRequest_'))
def handle_acceptRejectRequest(call):
    try:
        projectId = str(call.data).split('_')[1]
        userId = str(call.data).split('_')[2]
        
        if(call.data.startswith('rejectRequest_')):
            bot.send_message(userId, f"🔴 Ваша заявка на вступленние в проект *«{getProjectById(projectId)[1]}»* была отклонена.", 
                                parse_mode="Markdown")
            bot.send_message(call.from_user.id, f"Заявка отклонена.", 
                                parse_mode="Markdown")

        elif (call.data.startswith('acceptRequest_')):
            isAlreadyMember = False
            cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM users_projects
                                WHERE projectid = {projectId} and userid = '{userId}');''')
            isAlreadyMember = cursor.fetchone()

            if isAlreadyMember[0]:
                return
            
            cursor.execute(f"INSERT INTO users_projects (projectid, userid, role) VALUES (%s, %s, %s);", (projectId, userId, 'PARTNER'))
            connection.commit()

            bot.send_message(userId, f"🟢 Ваша заявка на вступленние в проект *«{getProjectById(projectId)[1]}»* была одобрена.", 
                                parse_mode="Markdown")
            
            bot.send_message(call.from_user.id, f"Заявка одобрена.", 
                                parse_mode="Markdown")
    except Exception as e:
            print(e)


@bot.message_handler(commands=['start'])
def start(message):
    
    # user_id = message.from_user.id
    # username = message.from_user.username
    # firstName = message.from_user.first_name
    # lastName = message.from_user.last_name

    # cursor.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, %s) 
    #                         On CONFLICT(id) DO UPDATE
    #                         SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''', 
    #                         (user_id, username, firstName, lastName, 'RESIDENT'))

    # connection.commit()

    bot.send_message(chat_id=message.chat.id, text= f"Привет.", reply_markup=genKeyboard(message.from_user.id))


@bot.message_handler(func=lambda message: message.text == "📝 Заполнить информацию о себе" or message.text == "🔴 Повторить ввод" or message.text == "📝 Редактировать информацию о себе")
def updateFullName(message):

    user = getUserById(message.from_user.id)
    if (user['status'] != "RESIDENT"):
        return

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    goHomeBtn = types.KeyboardButton(text="↩ Выйти")
    keyboard.add(goHomeBtn)

    msg = bot.send_message(chat_id=message.chat.id, text=f"Введите ФИО через пробел\n(_Иванов Иван Иванович_)", parse_mode="Markdown", reply_markup=keyboard)
    bot.register_next_step_handler(message=msg, callback=process_updateFullName_step)

@bot.message_handler(func=lambda message: message.text == "🗂 Добавить информацию о проекте")
def selectionProjectGroup(message):

    user = getUserById(message.from_user.id)
    if (user['status'] != "RESIDENT"):
        return

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

    if (user['status'] == "RESIDENT"):
        editInfoBtnText = "📝 Заполнить информацию о себе"
        if user['fieldofactivity'] != None and str(user['fieldofactivity']).strip() != "":
            editInfoBtnText = "📝 Редактировать информацию о себе"
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        updateProfileBtn = types.KeyboardButton(text=editInfoBtnText)
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