from telebot import types

from databaseRequests import DatabaseRequests
from keyboards import Keyboards
from auxiliary import Auxiliary

class ProjectsController:
    def __init__(self, bot, connection):
        self.bot = bot

        self.connection = connection

        cursor = connection.cursor()
        self.cursor = cursor

        self.db = DatabaseRequests(connection)
        self.keyboard = Keyboards(connection)
        self.auxiliary = Auxiliary(bot, connection)


# -------------- Insert new project steps
    def announceProject(self, chatId):
        bot = self.bot

        msg = bot.send_message(chatId, f"Введите *наименование* проекта", parse_mode="MarkdownV2", reply_markup=self.keyboard.exitBtn())
        bot.register_next_step_handler(msg, self.process_insertProjectName_step)

    def process_insertProjectName_step(self, message):
        try:
            bot = self.bot
            cursor = self.cursor

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
                
            projectName = message.text
            if len(projectName) < 3:
                msg = bot.reply_to(message, f'Неверный формат, повторите ввод наименования', parse_mode="Markdown")
                bot.register_next_step_handler(message=msg, callback=self.process_insertProjectName_step)
                return 
            
            cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM projects
                                    WHERE name = '{projectName.strip()}');''')
            isAlreadyExists = cursor.fetchone()
            
            if isAlreadyExists[0]:
                msg = bot.reply_to(message, f'Проект с таким наименованием уже существет, повторите ввод', parse_mode="Markdown")
                bot.register_next_step_handler(message=msg, callback=self.process_insertProjectName_step)
                return 

            msg = bot.reply_to(message, f'Составьте *описание* проекта {projectName}:', parse_mode="Markdown")

            bot.register_next_step_handler(msg, self.process_insertProjectDescription_step, projectName)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_insertProjectDescription_step(self, message, projectName):
        try:
            bot = self.bot

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
                
            projectDescription = message.text

            if len(projectDescription) < 3:
                msg = bot.reply_to(message, f'Неверный формат, повторите ввод описания', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_insertProjectDescription_step, projectName)
                return 

            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            goHomeBtn = types.KeyboardButton(text="↩ Выйти")
            keyboard.add(types.KeyboardButton(text='Креативные индустрии'), types.KeyboardButton(text='Медицина и образование'), types.KeyboardButton(text='Социальные'), types.KeyboardButton(text='Технологические'), types.KeyboardButton(text='Экологические'), goHomeBtn)

            msg = bot.send_message(message.from_user.id, f'Укажите *категорию* вашего проекта', parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_insertProjectCategory_step, projectName, projectDescription)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_insertProjectCategory_step(self, message, projectName, projectDescription):
        try:
            bot = self.bot

            projectCategory = ""

            if message.text == '↩ Выйти':
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            Categories = ['Креативные индустрии', 'Медицина и образование', 'Социальные', 'Технологические', 'Экологические']
            if message.text not in Categories:
                msg = bot.reply_to(message, f'Неверный формат, повторите ввод категории', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_insertProjectCategory_step, projectName, projectDescription)
                return 

            projectCategory = message.text

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('🔴 Повторить ввод', '🟢 Все верно')
            
            user = self.db.getUserById(message.from_user.id)
            fioUser = self.auxiliary.filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')
            
            msg = bot.send_message(message.chat.id, f''' Новый проект добавлен, проверьте правильность заполнения данных:
                                
*Наименование проекта*: _{self.auxiliary.filter(projectName)}_

*Описание*: _{self.auxiliary.filter(projectDescription)}_

*Категория*: _{self.auxiliary.filter(projectCategory)}_

*Заявитель*: {fioUser}
        ''', parse_mode="MarkdownV2", reply_markup=markup)
            bot.register_next_step_handler(msg, self.process_isRepeatFillingProject_step, projectName, projectDescription, projectCategory)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_isRepeatFillingProject_step(self, message, projectName, projectDescription, projectCategory):
        try:
            bot = self.bot
            connection = self.connection
            cursor = self.cursor
            
            if message.text == "🔴 Повторить ввод":
                self.announceProject(message.chat.id)
            elif message.text == "🟢 Все верно":
                cursor.execute(f'''INSERT INTO projects (name, description, category) VALUES (%s, %s, %s) RETURNING id;''', (projectName, projectDescription, projectCategory))
                newProjectId = cursor.fetchone()[0]
                connection.commit()
                cursor.execute(f'''INSERT INTO users_projects (projectid, userid, role) VALUES (%s, %s, %s);''', (newProjectId, message.from_user.id, 'AUTHOR'))
                connection.commit()
                
                self.auxiliary.exitStepHandler(message, "ok")
            else:   
                msg = bot.send_message(chat_id=message.chat.id, text="Проверьте корректность данных", parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_isRepeatFillingProject_step, projectName, projectDescription, projectCategory)

        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Message with project info
    def projectInfo(self, message, projectId):
        try:
            bot = self.bot
            cursor = self.cursor

            cursor.execute(f'''SELECT * FROM users_projects
                                INNER JOIN projects ON users_projects.projectid = projects.id
                                WHERE projectid = {projectId} and role = 'AUTHOR';''')
            columns = [desc[0] for desc in cursor.description]
            items = cursor.fetchall()
            author = dict(zip(columns, items[0]))

            cursor.execute(f'''SELECT username, lastname, firstname, patronymic, userid FROM users_projects
                                INNER JOIN users ON users_projects.userid = users.id
                                WHERE projectid = {projectId} and role = 'PARTNER';''')
            items = cursor.fetchall()
            partners = ""

            for partner in items:
                partners += self.auxiliary.filter(f'{partner[1] if partner[1] != None else ""} {partner[2] if partner[2] != None else ""} {partner[3] if partner[3] != None else ""} (@{partner[0]});\n')
            
            if partners.strip() != "":
                partners = f"*Партнеры*: \n{partners}"[:-2] + "\."

            user = self.db.getUserById(author['userid'])
            fioUser = self.auxiliary.filter(f'{user["lastname"] if user["lastname"] != None else ""} {user["firstname"] if user["firstname"] != None else ""} {user["patronymic"] if user["patronymic"] != None else ""} (@{user["username"]})')

            aboutProject = "__Информация о проекте:__"
            keyboard = self.keyboard.genMainKeyboard(message.from_user.id)

            if partners.strip() != "" and self.db.getUserById(message.from_user.id)['status'].find("ADMIN") != -1:
                bot.send_message(message.chat.id, "__Информация о проекте:__", parse_mode="MarkdownV2", reply_markup=keyboard)

                aboutProject = ""
                keyboard = self.keyboard.editCommandBtn(projectId)
                
            bot.send_message(message.chat.id, f'''{aboutProject}
                        
*Наименование проекта*: _{self.auxiliary.filter(author['name'])}_

*Описание*: _{self.auxiliary.filter(author['description'])}_

*Категория*: _{self.auxiliary.filter(author['category'])}_

*Заявитель*: {fioUser}

{partners}
        ''', parse_mode="MarkdownV2", reply_markup=keyboard)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Search project by projectName
    def getProjectnameForSelect(self, chatId):
        bot = self.bot

        msg = bot.send_message(chatId, "Введите наименование проекта для отображения данных\n(Пример: TimeTrace)", reply_markup=self.keyboard.exitBtn())        
        bot.register_next_step_handler(message=msg, callback=self.process_getProjectnameForSelect_step)

    def process_getProjectnameForSelect_step(self, message):
        try:
            bot = self.bot

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            projectName = message.text.strip()
            projectId = self.db.getProjectIdByProjectname(projectName)
            if projectId == "-":
                msg = bot.send_message(chat_id=message.chat.id, text= f"Проект не найден. Повторите ввод")
                bot.register_next_step_handler(msg, self.process_getProjectnameForSelect_step)
                return
            self.projectInfo(message, projectId)
            
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")
    
    
# -------------- Delete partner from project group steps
    def getUserNumForDeleteFromProject(self, chatId, projectId):
        try:
            cursor = self.cursor
            bot = self.bot

            keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
            cursor.execute(f'''SELECT CONCAT(lastname, ' ', firstname, ' ', patronymic, ' (@', username, ')') FROM users_projects
                                INNER JOIN users ON users_projects.userid = users.id
                                WHERE projectid = {projectId} and role = 'PARTNER';''')
            partnersList = cursor.fetchall()

            partners = {}
            partnersStr = ""
            for i in range(0, len(partnersList)):
                partners[str(i+1)] = partnersList[i][0]
                keyboard.add(types.KeyboardButton(text=f"{i+1}"))
                partnersStr += f"{i+1}\. {self.auxiliary.filter(partnersList[i][0])}\n"

            goHomeBtn = types.KeyboardButton(text="↩ Выйти")
            keyboard.add(goHomeBtn)

            msg = bot.send_message(chatId, f"{partnersStr}\n_Введите *номер пользователя*, чтобы исключить его из проекта_ \n\(\-\-\> *1\.* Иванов Иван Иванович \(@username\)\)", parse_mode="MarkdownV2", reply_markup=keyboard)        
            bot.register_next_step_handler(msg, self.process_getUserNumForDeleteFromProject_step, projectId, partners)
        except Exception as e:
            print("Error in getUserNumForDeleteFromProject: ", e)

    def process_getUserNumForDeleteFromProject_step(self, message, projectId, partners):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            numOfUser = message.text.strip()

            if partners.get(str(numOfUser)) is None or not numOfUser.isdigit():
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод номера\n(Пример: 1)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_getUserNumForDeleteFromProject_step, projectId, partners)
                return
        
            userFioUsernameString = str(partners[str(numOfUser)])
            userId = self.db.getUserIdByUsernameAndFIO(userFioUsernameString[userFioUsernameString.find('(') + 1 : userFioUsernameString.find(')')].strip('@'), "userName")

            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            rejectBtn = types.KeyboardButton("🔴 Отмена")
            acceptBtn = types.KeyboardButton("🟢 Удалить")
            keyboard.add(rejectBtn, acceptBtn)

            msg = bot.send_message(message.chat.id, f"Удалить пользователя *«{userFioUsernameString}»* из проекта *«{self.db.getProjectById(projectId)['name']}»*?", parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_deletePartner_step, projectId, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_deletePartner_step(self, message, projectId, userId):
        try:
            connection = self.connection
            cursor = self.cursor
            bot = self.bot

            if message.text == "🔴 Отмена":
                self.auxiliary.exitStepHandler(message, "ok")
            elif message.text == "🟢 Удалить":
                cursor.execute(f'''DELETE FROM users_projects WHERE 
                                    projectid={projectId} and userid='{userId}';''')
                connection.commit()

                bot.send_message(message.chat.id, f"Пользователь был исключен из команды проекта.", parse_mode="Markdown", reply_markup=self.keyboard.genMainKeyboard(message.from_user.id))
            else:
                msg = bot.reply_to(message, 'Вы можете *отменить* удаление или *подтвердить* его.', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_deletePartner_step, projectId, userId)
            return
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")