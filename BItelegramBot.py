from telebot import types, telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
import time
from threading import Thread
import schedule
import datetime
import calendar

import config
from projectsController import ProjectsController  
from databaseRequests import DatabaseRequests
from usersController import UsersController
from auxiliary import Auxiliary
from eventsController import EventsController
from vacanciesController import VacanciesController
from keyboards import Keyboards

bot = telebot.TeleBot(config.BOT_TOKEN)

connection = psycopg2.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
        port=config.PORT
    )
cursor = connection.cursor()

projectsController = ProjectsController(bot, connection) 
usersController = UsersController(bot, connection)
eventsController = EventsController(bot, connection)
db = DatabaseRequests(connection)
auxiliary = Auxiliary(bot, connection)
vacanciesController = VacanciesController(bot, connection)
keyboards = Keyboards(connection)

print('[INFO] PostgreSQL start')


# -------------------------------------------------- Join to project group -----------------------

def process_requestToJoin_step(message, projectId, authorId):
    try:
        if message.text == "🔴 Отмена":
            auxiliary.exitStepHandler(message, "ok")
        elif message.text == "🔵 Отправить запрос":

            user = getUserById(message.from_user.id)
            fioUser = auxiliary.filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')

            keyboard = types.InlineKeyboardMarkup(row_width=2)
            rejectBtn = types.InlineKeyboardButton("🔴 Отклонить", callback_data=f'rejectRequest_{projectId}_{message.from_user.id}')
            acceptBtn = types.InlineKeyboardButton("🟢 Принять", callback_data=f'acceptRequest_{projectId}_{message.from_user.id}')
            keyboard.row(rejectBtn, acceptBtn)

            bot.send_message(authorId, f"Пользователь {fioUser} отправил запрос на вступление в команду проекта *«{auxiliary.filter(getProjectById(projectId)['name'])}»*", 
                            reply_markup=keyboard, 
                            parse_mode="MarkdownV2")
            
            bot.send_message(message.from_user.id, f"Ваша заявка на вступление в команду проекта *«{auxiliary.filter(getProjectById(projectId)['name'])}»* была отправлена\. Скоро заявитель её рассмотрит и мы уведомим Вас о результате\.", 
                            reply_markup=keyboards.genMainKeyboard(message.from_user.id), 
                            parse_mode="MarkdownV2")
        else:
            msg = bot.reply_to(message, 'Вы можете *подать заявку* на присоединение к команде выбранного проекта или *отменить* действие.', parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_requestToJoin_step, projectId, authorId)
        return
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(message, "error")



# -------------------------------------------------- Requests -----------------------

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
    
    columns = [desc[0] for desc in cursor.description]
    items = cursor.fetchone()
    project = dict(zip(columns, items))
    return project

def getUserIdByUsernameAndFIO(userInfoMsg, dataFormat):
    match dataFormat:
        case "userName":
            cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM users
                                    WHERE username = '{userInfoMsg}');''')
            exists = cursor.fetchone()[0]
            if not exists: return "-"

            cursor.execute(f'''SELECT id FROM users 
                        WHERE username = '{userInfoMsg}';''')
            userId = cursor.fetchone()[0]
            return userId 
        case "lastName":
            cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM users
                                    WHERE lastname = '{userInfoMsg}');''')
            exists = cursor.fetchone()[0]
            if not exists: return "-"

            cursor.execute(f'''SELECT id FROM users 
                        WHERE lastName = '{userInfoMsg}';''')
            userId = cursor.fetchall()
            return userId 
        case "lastName_firstName":
            cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM users
                        WHERE lastname = '{userInfoMsg.split(' ')[0]}' and firstname = '{userInfoMsg.split(' ')[1]}');''')
            exists = cursor.fetchone()[0]
            if not exists: return "-"

            cursor.execute(f'''SELECT id FROM users 
                        WHERE lastname = '{userInfoMsg.split(' ')[0]}' and firstname = '{userInfoMsg.split(' ')[1]}';''')
            userId = cursor.fetchone()[0]
            return userId 
    
def getProjectIdByProjectname(name):
    cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM projects
                                WHERE name = '{name}');''')
    exists = cursor.fetchone()[0]
    if not exists:
        return "-"

    cursor.execute(f'''SELECT id FROM projects 
                        WHERE name = '{name}';''')
    projectId = cursor.fetchone()[0]
    return projectId 

def getEventNameAndMeetingDateById(eventId):
    cursor.execute(f"SELECT name, meetingdate FROM events WHERE id='{eventId}'")
    
    NameAndMeetingDate = cursor.fetchone()
    return NameAndMeetingDate

def pollIsActive(poll_id):
    cursor.execute(f"SELECT EXISTS (SELECT id FROM events WHERE id='{poll_id}' and isactive=true);")
    isActive = cursor.fetchone()[0]

    return isActive




# -------------------------------------------------- Callback handlers -----------------------

@bot.callback_query_handler(func=lambda call: call.data.startswith('prev_') or call.data.startswith('next_'))
def handle_navigation(call):
    try:
        countOfProjects = db.getCountOfAllProjects()
        action, page = call.data.split('_')

        if action == 'prev':
            current_page = max(1, int(page) - 1)
        elif action == 'next':
            current_page = min((countOfProjects - 1) // 8 + 1, int(page) + 1)

        projects = db.getProjectsInPage(current_page)

        keyboard = keyboards.create_inline_keyboard(projects, current_page, False, "")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print("Error in handle_navigation project keyboard: ", e)

@bot.callback_query_handler(func=lambda call: call.data.startswith('project_'))
def handle_project_selection(call):
    try:
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

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
        isAuthor = False 

        if str(author['userid']) == str(call.from_user.id):
            alreadyMember = True
            isAuthor = True

        for partner in items:
            if (str(partner[4]) == str(call.from_user.id) or str(author['userid']) == str(call.from_user.id)):
                alreadyMember = True
            partners += auxiliary.filter(f'{partner[1] if partner[1] != None else ""} {partner[2] if partner[2] != None else ""} {partner[3] if partner[3] != None else ""} (@{partner[0]});\n')
        
        if partners.strip() != "":
            partners = f"*Партнеры*: \n{partners}"[:-2] + "\."

        user = db.getUserById(author['userid'])
        fioUser = auxiliary.filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')
        
        aboutProject = f"__Вы можете подать запрос на вступление в команду проекта «{auxiliary.filter(author['name'])}»\.__"
        if alreadyMember:
            aboutProject = "__Вы уже состоите в команде этого проекта\.__"
            keyboard = keyboards.genMainKeyboard(call.from_user.id)
            if partners.strip() != "" and (isAuthor or db.getUserById(call.from_user.id)['status'].find("ADMIN") != -1):
                aboutProject = ""
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                kickPartnerBtn = types.InlineKeyboardButton('Редактировать команду', callback_data=f'deletePartnerFrom_{idProject}')
                keyboard.add(kickPartnerBtn)
                bot.send_message(call.message.chat.id,"__Вы уже состоите в команде этого проекта\.__", parse_mode="MarkdownV2", reply_markup=keyboards.genMainKeyboard(call.from_user.id))
        msg = bot.send_message(call.message.chat.id, f'''{aboutProject}
                            
*Наименование проекта*: _{auxiliary.filter(author['name'])}_

*Описание*: _{auxiliary.filter(author['description'])}_

*Категория*: _{auxiliary.filter(author['category'])}_

*Заявитель*: {fioUser}

{partners}
    ''', parse_mode="MarkdownV2", reply_markup=keyboard)
        
        if alreadyMember: return
        bot.register_next_step_handler(msg, process_requestToJoin_step, idProject, author['userid'])

    except Exception as e:
            print(e)
            auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('prevVac_') or call.data.startswith('nextVac_'))
def handle_navigation_vacancy(call):
    try:
        countOfProjects = db.getCountOfProjectsForAuthor(call.from_user.id)
        action, page = call.data.split('_')

        if action == 'prevVac':
            current_page = max(1, int(page) - 1)
        elif action == 'nextVac':
            current_page = min((countOfProjects - 1) // 8 + 1, int(page) + 1)

        projects = db.getProjectsForVacancyInPage(current_page, call.from_user.id)

        keyboard = keyboards.create_inline_keyboard(projects, current_page, True, call.from_user.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print("Error in handle_navigation_vacancy project keyboard: ", e)

@bot.callback_query_handler(func=lambda call: call.data.startswith('projectVac_'))
def handle_project_selection_vacancy(call):
    try:
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        idProject = call.data[11:]
       
        vacanciesController.addNewVacancy(call.message.chat.id, idProject)
    except Exception as e:
            print(e)
            auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'announce_project')
def handle_announceProject(call):
    try:
        # announceProject(call.message.chat.id)
        projectsController.announceProject(call.message.chat.id)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'update_user_info')
def handle_updateUserInfo(call):
    try:
        usersController.getUsernameForUpdate(call.message.chat.id)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'get_user_info')
def handle_getUserInfo(call):
    try:
        usersController.getUsernameForSelect(call.message.chat.id)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'get_project_info')
def handle_getProjectInfo(call):
    try:
        projectsController.getProjectnameForSelect(call.message.chat.id)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'get_users_excel')
def handle_getUsersExcel(call):
    try:
        query_string = '''SELECT id, username, lastname, firstname, patronymic, 
                                fieldofactivity, aboutme, educationalinstitution, faculty, course, direction, 
                                speciality, "group", seriespassport, numberpassport, phonenum, email, status FROM users ORDER BY lastname'''
        filepath = "usersList.xlsx"

        auxiliary.export_to_excel(query_string,("Имя пользователя", "Фамилия", "Имя", "Отчество", 
                                        "Род деятельности", "О себе", "Образовательное учреждение", "Факультет", "Курс", "Направление", 
                                        "Специальность", "Группа", "Серия паспорта", "Номер паспорта", "Номер тел.", "Email", "Роли", "Участник проектов"), filepath)

        with open('usersList.xlsx', 'rb') as tmp:
            bot.send_document(call.from_user.id, tmp)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'get_projects_excel')
def handle_getProjectsExcel(call):
    try:
        query_string = '''SELECT * FROM projects ORDER BY name'''
        filepath = "projectsList.xlsx"

        auxiliary.export_to_excel(query_string,("Наименование", "Описание", "Категория", "Заявитель", "Партнеры"), filepath)

        with open('projectsList.xlsx', 'rb') as tmp:
            bot.send_document(call.from_user.id, tmp)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data == 'get_vacancies_excel')
def handle_getVacanciesExcel(call):
    try:
        query_string = '''SELECT id, newvacancy, isactive, post, requirements, job_description, contacts, projectid 
                            FROM vacancies 
                            ORDER BY newvacancy DESC'''
        filepath = "vacanciesList.xlsx"

        auxiliary.export_to_excel(query_string,("Статус", "Актуальность", "Должность", "Требования", "Описание", "Контакты", "Проект"), filepath)

        with open('vacanciesList.xlsx', 'rb') as tmp:
            bot.send_document(call.from_user.id, tmp, caption="Список всех подаваемых вакансий\n(Статус: «Новое» - вакансия еще не просматривалась и отсутствовала при прошлой выгрузке таблицы)")
    
        cursor.execute("UPDATE vacancies SET newvacancy = false;")
        connection.commit()

    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('rejectRequest_') or call.data.startswith('acceptRequest_'))
def handle_acceptRejectRequest(call):
    try:
        projectId = str(call.data).split('_')[1]
        userId = str(call.data).split('_')[2]
        
        if(call.data.startswith('rejectRequest_')):
            bot.send_message(userId, f"🔴 Ваша заявка на вступленние в проект *«{getProjectById(projectId)['name']}»* была отклонена.", 
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

            bot.send_message(userId, f"🟢 Ваша заявка на вступленние в проект *«{getProjectById(projectId)['name']}»* была одобрена.", 
                                parse_mode="Markdown")
            
            bot.send_message(call.from_user.id, f"Заявка одобрена.", 
                                parse_mode="Markdown")
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('need_memo_'))
def handle_setNeedMemo(call):
    try:
        userId = str(call.data).split('_')[2]
        eventId = str(call.data).split('_')[3]

        if not pollIsActive(eventId): 
            return

        cursor.execute(f'''UPDATE events_users SET needmemo = {True} 
                       WHERE eventid = '{eventId}' and userid = '{userId}';''')
        connection.commit()
        
        bot.send_message(userId, "Запрос на служебную записку оформлен.")
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('need_pass_'))
def handle_setNeedPass(call):
    try:
        userId = str(call.data).split('_')[2]
        eventId = str(call.data).split('_')[3]

        if not pollIsActive(eventId): 
            return

        cursor.execute(f'''SELECT (seriesPassport IS NOT NULL AND numberPassport IS NOT NULL) AS indicatedData 
                            FROM users WHERE id = '{userId}';''')
        indicatedData = cursor.fetchone()[0]

        if not indicatedData:
            usersController.fillPassportInfo(call.message.chat.id, eventId)
        else:
            cursor.execute(f'''UPDATE events_users SET needpass = {True} 
                        WHERE eventid = '{eventId}' and userid = '{userId}';''')
            connection.commit()

            bot.send_message(userId, "Запрос на пропуск оформлен.")
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('deletePartnerFrom_'))
def handle_deletePartnerFrom(call):
    try:
        projectId = str(call.data).split('_')[1]

        projectsController.getUserNumForDeleteFromProject(call.message.chat.id, projectId)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_vacancy_active'))
def handle_setVacancyActive(call):
    try:
        setActive = True if str(call.data).split('_')[3] == "True" else False
        vacancyId = str(call.data).split('_')[4]
        authorId = str(call.data).split('_')[5]

        if setActive: 
            return
        
        cursor.execute(f'''UPDATE vacancies SET isactive = {False}, newvacancy = {True}
                    WHERE id = '{vacancyId}';''')
        connection.commit()

        bot.send_message(authorId, "Вакансия снята с публикации.")
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(call.message, "error")




# -------------------------------------------------- Commands -----------------------

@bot.message_handler(commands=['start'])
def start(message):

    # user_id = message.from_user.id
    # username = message.from_user.username
    # firstName = message.from_user.first_name
    # lastName = message.from_user.last_name

    # cursor.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, '{RESIDENT}') 
    #                         On CONFLICT(id) DO UPDATE
    #                         SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''', 
    #                         (user_id, username, firstName, lastName))

    # connection.commit()

    user = db.getUserById(message.from_user.id)

    helloTxt = "🐝 Привет\!"

    if user['status'].find("RESIDENT") != -1:
        helloTxt = "🐝 Привет, резидент\!"
    if user['status'].find("ADMIN") != -1:
        helloTxt = '''🐝 Привет\! Быстрые команды:
*Обновить информацию о пользователе*: 
`\/updateUserInfo @username`
*Просмотреть информацию о пользователе*: 
`\/getUserInfo @username / Фамилия / Фамилия Имя`
*Просмотреть информацию о проекте*: 
`\/getProjectInfo projectName`'''
    if user['status'].find("PROJECT_MANAGER") != -1:
        helloTxt = ""
    bot.send_message(chat_id=message.chat.id, text= helloTxt, reply_markup=keyboards.genMainKeyboard(message.from_user.id), parse_mode="MarkdownV2")

@bot.message_handler(commands=['updateUserInfo'])
def updateResidentInfo(message):
    try: 
        if db.getUserById(message.from_user.id)['status'].find("ADMIN") == -1:
            bot.send_message(chat_id=message.chat.id, text= f"Недостаточно прав")
            return 
        
        username = auxiliary.extract_arg(message.text)[0].strip('@')
        userId = getUserIdByUsernameAndFIO(username, "userName")
        if userId == "-":
            bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден")
        else:
            bot.send_message(chat_id=message.chat.id, text= f"Обновление данных пользователя @{username}")
            usersController.updateFullname(message.chat.id, userId)

    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(message, "error")

@bot.message_handler(commands=['getUserInfo'])
def getUserInfo(message):
    try:
        if db.getUserById(message.from_user.id)['status'].find("ADMIN") == -1:
            bot.send_message(chat_id=message.chat.id, text= f"Недостаточно прав")
            return 

        userInfoMsg = message.text[13:].strip()

        dataFormat = ""
        if userInfoMsg.startswith('@'):
            userInfoMsg = userInfoMsg.strip('@')
            dataFormat = "userName"
        elif len(userInfoMsg.split(' ')) == 1:
            dataFormat = "lastName"
        elif len(userInfoMsg.split(' ')) == 2:
            dataFormat = "lastName_firstName"
        else:
            bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден")
            return

        userId = getUserIdByUsernameAndFIO(userInfoMsg, dataFormat)
        if userId == "-":
            bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден")
            return
        
        if not isinstance(userId, str):
            for user in userId:
                usersController.userInfo(message, user[0])
        else:
            usersController.userInfo(message, userId)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(message, "error")

@bot.message_handler(commands=['getProjectInfo'])
def getProjectInfo(message):
    try:
        if getUserById(message.from_user.id)['status'].find("ADMIN") == -1:
            bot.send_message(chat_id=message.chat.id, text= f"Недостаточно прав")
            return 
        
        projectName = auxiliary.extract_arg(message.text)[0].strip()
        projectId = getProjectIdByProjectname(projectName)
        if projectId == "-":
            bot.send_message(chat_id=message.chat.id, text= f"Проект не найден")
        projectsController.projectInfo(message, projectId)
    except Exception as e:
        print(e)
        auxiliary.exitStepHandler(message, "error")


# -------------------------------------------------- Message handlers -----------------------

@bot.message_handler(func=lambda message: message.text == "📝 Заполнить информацию о себе" or message.text == "🔴 Повторить ввод" or message.text == "📝 Редактировать информацию о себе")
def updateFullName_handler(message):

    user = getUserById(message.from_user.id)
    if (user['status'].find("RESIDENT") == -1):
        return
    usersController.updateFullname(message.chat.id, message.from_user.id)
   
@bot.message_handler(func=lambda message: message.text == "🗂 Добавить информацию о проекте")
def selectionProjectGroup(message):

    user = getUserById(message.from_user.id)
    if (user['status'].find("RESIDENT") == -1):
        return

    page = 1
    inlineKeyboard = keyboards.create_inline_keyboard(db.getProjectsInPage(page), page, False, "")
    bot.send_message(chat_id=message.chat.id, text=f"Выберите проект, в команде которого Вы состоите или добавьте свой", parse_mode="Markdown", reply_markup=inlineKeyboard)

@bot.message_handler(func=lambda message: message.text == "🟢 Все верно" or message.text == "↩ Выйти")
def goMainMenu(message):
    keyboard = keyboards.genMainKeyboard(message.from_user.id)
    match message.text:
        case "🟢 Все верно":
            bot.send_message(chat_id=message.chat.id, text=f"👍", parse_mode="Markdown", reply_markup=keyboard)
        case "↩ Выйти":
            bot.send_message(chat_id=message.chat.id, text=f"👌", parse_mode="Markdown", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "🛠️ Панель администратора")
def getAdminPanel(message):

    user = getUserById(message.from_user.id)
    if (user['status'].find("ADMIN") == -1):
        return

    bot.send_message(chat_id=message.chat.id, text=f'''__Возможности администратора__''', parse_mode="MarkdownV2", reply_markup=keyboards.inlineAdminPanel())

@bot.message_handler(func=lambda message: message.text == "🎟️ Новое мероприятие")
def newEvent(message):
    user = getUserById(message.from_user.id)

    if (user['status'].find("EVENT_MANAGER") == -1):
        return

    eventsController.createNewEvent(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📃 Добавить вакансию для своего проекта")
def newVacancy(message):
    user = getUserById(message.from_user.id)

    if user['status'].find("RESIDENT") == -1:
        return
    if db.getCountOfProjectsForAuthor(message.from_user.id) < 1:
        bot.send_message(chat_id=message.chat.id, text=f"Пока что вы не числитетесь заявителем ни в одном проекте, попробуйте добавить информацию о проекте.", parse_mode="Markdown", reply_markup=inlineKeyboard)
        return

    page = 1
    inlineKeyboard = keyboards.create_inline_keyboard(db.getProjectsForVacancyInPage(page, message.from_user.id), page, True, message.from_user.id)
    bot.send_message(chat_id=message.chat.id, text=f"Выберите проект, для которого надо добавить новую вакансию:", parse_mode="Markdown", reply_markup=inlineKeyboard)

@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):
    try:
        user_id = message.new_chat_members[0].id
        username = message.new_chat_members[0].username
        firstName = message.new_chat_members[0].first_name
        lastName = message.new_chat_members[0].last_name

        if(str(message.chat.id) == config.RESIDENT_GROUP_ID):
            cursor.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, '{RESIDENT}') 
                            On CONFLICT(id) DO UPDATE
                            SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''', 
                            (user_id, username, firstName, lastName))

        connection.commit()

        bot.send_message(message.chat.id, f"Привет, {firstName}")

    except Exception as ex:
        print('[INFO] Error postgresql ', ex)

@bot.message_handler(commands=['send'])
def send_message_to_group(message):

    chat_id = message.chat.id
    # members_count = bot.get_chat_members_count(chat_id)
    print(chat_id)

    # poll_message.json
    # with open('mytest.csv', newline='', encoding='utf-8') as csvfile:
    #     reader = csv.DictReader(csvfile)
    
    #     for row in reader:
    #         user_id = row['user id']
    #         if user_id != '6370696970':
    #             try:
    #                 bot.send_message(user_id, message.text.replace('/send ', ''))
    #             except telebot.apihelper.ApiTelegramException as e:
    #                 print(f"Not delivered. User {row['username']} hasnt yet started a conversation.")

@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    try:
        isGoingToCome = False
        needMemo = False
        needPass = False

        if not pollIsActive(pollAnswer.poll_id): 
            return

        match str(pollAnswer.option_ids):
            case '[0]':
                isGoingToCome = True
                markup = types.InlineKeyboardMarkup(row_width=1)
                needMemoBtn = types.InlineKeyboardButton('📄 Запросить служебную записку', callback_data=f'need_memo_{pollAnswer.user.id}_{pollAnswer.poll_id}')
                needPassBtn = types.InlineKeyboardButton('🎫 Нужен пропуск на территорию', callback_data=f'need_pass_{pollAnswer.user.id}_{pollAnswer.poll_id}')

                user = getUserById(pollAnswer.user.id)
                if user['educationalinstitution'] == 'РЭУ им. Г.В. Плеханова':
                    markup.add(needMemoBtn)
                else:
                    markup.add(needPassBtn)

                NameAndMeetingDate = getEventNameAndMeetingDateById(pollAnswer.poll_id)
                bot.send_message(chat_id=pollAnswer.user.id, text=f"Не забудь про мероприятие *«{auxiliary.filter(NameAndMeetingDate[0])}»* \- _{auxiliary.filter(str(NameAndMeetingDate[1].strftime('%d.%m.%Y %H:%M')))}_\.", parse_mode="MarkdownV2", reply_markup=markup)

            case '[1]':
                isGoingToCome = False
            case '[]':
                isGoingToCome = False

        cursor.execute(f'''INSERT INTO events_users (eventid, userid, isgoingtocome, needmemo, needpass) VALUES (%s, %s, %s,%s, %s) 
                            ON CONFLICT (eventid, userid)
                            DO UPDATE SET (isgoingtocome, needmemo, needpass) = (EXCLUDED.isgoingtocome, EXCLUDED.needmemo, EXCLUDED.needpass);''', 
                        (pollAnswer.poll_id, pollAnswer.user.id, isGoingToCome, needMemo, needPass))
        connection.commit()
    except Exception as e:
        print("Error in poll answer handler: ", e)





def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def newsletterForProjectManager():
    try:
        cursor.execute("SELECT id FROM users WHERE status && '{PROJECT_MANAGER}';")
        projectManagerId = cursor.fetchone()[0]
        
        bot.send_message(projectManagerId, "Проверьте таблицу вакансий на наличие новых записей.", reply_markup=keyboards.markupExcelVacancies())
    except Exception as e:
        print("Error in newsletter for projectManager: ", e)

def newsletterForResidentVacancy():
    try:
        cursor.execute('''SELECT users_projects.userid, vacancies.id, vacancies.post, projects.name FROM vacancies 
                            INNER JOIN users_projects ON vacancies.projectid = users_projects.projectid
                            INNER JOIN projects ON vacancies.projectid = projects.id
                            WHERE vacancies.isactive = true and users_projects.role = 'AUTHOR'
                            ORDER BY newvacancy DESC;''')
        vacancies = cursor.fetchall()
        
        for vacancy in vacancies:
            authorId = vacancy[0]
            vacancyId = vacancy[1]
            postName = vacancy[2]
            projectName = vacancy[3]
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            setVacansyActiveFalse = types.InlineKeyboardButton('❌ Снять с публикации', callback_data=f'set_vacancy_active_False_{vacancyId}_{authorId}')
            setVacansyActiveTrue = types.InlineKeyboardButton('✅ Актуально', callback_data=f'set_vacancy_active_True_{vacancyId}_{authorId}')
            markup.add(setVacansyActiveFalse, setVacansyActiveTrue)
            bot.send_message(authorId, f"Обновите данные для таблицы вакансий!\nОтветьте, актуальна ли ещё вакансия на должность *«{postName}»* в проект *«{projectName}»*?", parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print("Error in newsletter for projectManager: ", e)

if __name__ == '__main__':
    for fiveMin in range(0, 60, 5):
        everyFive = ""
        if fiveMin < 10 or fiveMin == 0:
            everyFive = ":0" + str(fiveMin)
        else:
            everyFive = ":" + str(fiveMin)
        schedule.every().hour.at(everyFive).do(eventsController.isTimeToNewsletterForDocManager)

    today = datetime.date.today()
    if calendar.monthrange(today.year, today.month)[1] == today.day:
        newsletterForProjectManager()
        newsletterForResidentVacancy()

    Thread(target=schedule_checker).start()
    bot.infinity_polling()
