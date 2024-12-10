import re
from telebot import types

from databaseRequests import DatabaseRequests
from keyboards import Keyboards
from auxiliary import Auxiliary

class UsersController:
    def __init__(self, bot, connection):
        self.bot = bot

        self.connection = connection

        cursor = connection.cursor()
        self.cursor = cursor

        self.db = DatabaseRequests(connection)
        self.keyboard = Keyboards(connection)
        self.auxiliary = Auxiliary(bot, connection)


# -------------- Insert user info steps
    def updateFullname(self, chatId, userId):
        bot = self.bot

        msg = bot.send_message(chat_id=chatId, text=f"Введите ФИО через пробел\n(_Иванов Иван Иванович_)", parse_mode="Markdown", reply_markup=self.keyboard.exitBtn())
        bot.register_next_step_handler(msg, self.process_updateFullName_step, userId)

    def process_updateFullName_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection
            # surname = message.text.strip().split(' ')[0]
            # name = message.text.strip().replace(surname, "").strip().split(' ')[0]
            # patronymic = message.text.strip().replace(surname, "").replace(name, "").strip().split(' ')[0]

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
                
            pattern = r'([А-ЯЁа-яё]+)\s+([А-ЯЁа-яё]+)\s+([А-ЯЁа-яё]+)'
            match = re.search(pattern, message.text.strip())
            
            if match:
                surname, name, patronymic = match.groups()
            else:
                msg = bot.reply_to(message, f'Неверный формат, повторите ввод ФИО\n(Пример: _Иванов Иван Иванович_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateFullName_step, userId)
                return 

            cursor.execute(f'''UPDATE users SET firstname='{name}',
                                lastname='{surname}', patronymic='{patronymic}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.reply_to(message, f'Укажите сферу деятельности')

            bot.register_next_step_handler(msg, self.process_updateFieldOfActivity_step, userId)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateFieldOfActivity_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            fieldOfActivity = message.text

            if len(fieldOfActivity) <= 1:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод сферы деятельности\n(Пример: _Медицина и образование_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateFieldOfActivity_step, userId)
                return
            
            cursor.execute(f'''UPDATE users SET fieldofactivity='{fieldOfActivity}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.reply_to(message, 'Записано. Расскажите о себе: опишите свои области компетенций, укажите hard skills.')
            bot.register_next_step_handler(msg, self.process_updateAboutMe_step, userId)
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateAboutMe_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            aboutMe = message.text

            if len(aboutMe) <= 1:
                msg = bot.reply_to(message, 'Неверный формат, повторите')
                bot.register_next_step_handler(msg, self.process_updateAboutMe_step, userId)
                return
            
            cursor.execute(f'''UPDATE users SET aboutme='{aboutMe}'
                                WHERE id = '{userId}';''')
            connection.commit()

            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            reaBtn = types.KeyboardButton(text="РЭУ им. Г.В. Плеханова")
            hseBtn = types.KeyboardButton(text="НИУ ВШЭ")
            mftiBtn = types.KeyboardButton(text="МФТИ")
            goHomeBtn = types.KeyboardButton(text="↩ Выйти")
            keyboard.add(reaBtn, hseBtn, mftiBtn, goHomeBtn)

            msg = bot.send_message(message.chat.id, 'Выберите учебное заведение или укажите вручную', parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_updateEducationalInstitution_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateEducationalInstitution_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            educationalInstitution = message.text

            if len(educationalInstitution) < 3:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод учебного заведения', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateEducationalInstitution_step)
                return
        
            cursor.execute(f'''UPDATE users SET educationalinstitution='{educationalInstitution}'
                                WHERE id = '{userId}';''')
            connection.commit()

            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            keyboard.add(types.KeyboardButton(text="↩ Выйти"))

            if message.text == "РЭУ им. Г.В. Плеханова":
                msg = bot.send_message(message.chat.id, 'Укажите вашу Высшую школу/Институт/Факультет', parse_mode="Markdown", reply_markup=keyboard)
                bot.register_next_step_handler(msg, self.process_updateFaculty_step, userId) 
                return

            cursor.execute(f'''UPDATE users SET course=NULL, 
                                    faculty=NULL, direction=NULL, 
                                    speciality=NULL, "group"=NULL
                                    WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.send_message(message.chat.id, 'Отлично, оставьте свой *номер телефона*\n(_+79993332211_)', parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_updatePhoneNum_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateFaculty_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            faculty = message.text

            if len(faculty) < 3:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод ВШ/И/Ф', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.auxiliary.process_updateFaculty_step, userId)
                return
        
            cursor.execute(f'''UPDATE users SET faculty='{faculty}'
                                WHERE id = '{userId}';''')
            connection.commit()

            keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
            keyboard.add(types.KeyboardButton(text="1"), types.KeyboardButton(text="2"), types.KeyboardButton(text="3"), types.KeyboardButton(text="4"), types.KeyboardButton(text="5"))
            keyboard.add(types.KeyboardButton(text="↩ Выйти"))

            msg = bot.send_message(message.chat.id, 'На каком *курсе* вы обучаетесь?', parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_updateCourse_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateCourse_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            course = message.text

            if len(course) > 1 or not course.isdigit():
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод курса\n(Пример: 2)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateCourse_step, userId)
                return
        
            cursor.execute(f'''UPDATE users SET course={course}
                                WHERE id = '{userId}';''')
            connection.commit()

            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            keyboard.add(types.KeyboardButton(text="↩ Выйти"))

            msg = bot.send_message(message.chat.id, 'Укажите Ваше *направление подготовки*.', parse_mode="Markdown", reply_markup=keyboard)
            bot.register_next_step_handler(msg, self.process_updateDirection_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateDirection_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            direction = message.text

            if len(direction) < 5:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод направления подготовки', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateDirection_step, userId)
                return
        
            cursor.execute(f'''UPDATE users SET direction='{direction}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.send_message(message.chat.id, 'Укажите *специальность*', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_updateSpeciality_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateSpeciality_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            speciality = message.text

            if len(speciality) < 5:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод специальности', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateSpeciality_step, userId)
                return
        
            cursor.execute(f'''UPDATE users SET speciality='{speciality}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.send_message(message.chat.id, 'Укажите *группу*, в которой Вы обучаетесь', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_updateGroup_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateGroup_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
        
            group = message.text

            if len(group) < 4:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод группы', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateGroup_step, userId)
                return
        
            cursor.execute(f'''UPDATE users SET "group"='{group}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.send_message(message.chat.id, 'Отлично, оставьте свой номер телефона\n(_+79993332211_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_updatePhoneNum_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updatePhoneNum_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            phoneNum = message.text

            pattern = r'^\+\d{11}$'
            if not re.match(pattern, phoneNum):
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод номера\n(Пример: _+79993332211_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updatePhoneNum_step, userId)
                return
            
            cursor.execute(f'''UPDATE users SET phonenum='{phoneNum}'
                                WHERE id = '{userId}';''')
            connection.commit()

            msg = bot.reply_to(message, 'Осталось добавить почту\n(_ivanov.i.i@gmail.com_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_updateEmail_step, userId) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_updateEmail_step(self, message, userId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            email = message.text

            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(pattern, email):
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод почты\n(Пример: _ivanov.i.i@gmail.com_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_updateEmail_step, userId)
                return
            
            cursor.execute(f'''UPDATE users SET email='{email}'
                                WHERE id = '{userId}';''')
            connection.commit()

            cursor.execute(f'''SELECT name FROM users_projects
                                INNER JOIN projects ON users_projects.projectid = projects.id
                                WHERE userid = '{userId}';''')
            projects = cursor.fetchall()

            projectNames = ""
            for project in projects:
                projectNames += project[0] + ", "
            
            if projectNames.strip() != "":
                projectNames = f"*Участник проектов*: {projectNames}"[:-2]

            user = self.db.getUserById(userId)
            email = user['email'].replace("_", "\_")

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('🔴 Повторить ввод', '🟢 Все верно')

            additionInfo = ""
            if user['educationalinstitution'] == "РЭУ им. Г.В. Плеханова":
                additionInfo = f" ({user['course']} курс, {user['faculty']}, по направлению «{user['direction']}», специальность «{user['speciality']}», группа {user['group']})"
            bot.send_message(message.chat.id, f'''Данные обновлены, проверьте корректность:

*ФИО*: _{user['lastname'] if user['lastname'] != None else ""} {user['firstname'] if user['firstname'] != None else ""} {user['patronymic'] if user['patronymic'] != None else ""}_

*Сфера деятельности*: _{user['fieldofactivity']}_

*Учебное заведение*: _{user['educationalinstitution']}{additionInfo}_

*О себе*: _{user['aboutme']}_

*Телефон*: _{user['phonenum']}_

*Email*: {email}

{projectNames.strip()}''', 
            reply_markup=markup, 
            parse_mode="Markdown")
            
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Message with user info
    def userInfo(self, message, userId):
        try:
            cursor = self.cursor
            bot = self.bot

            cursor.execute(f'''SELECT name FROM users_projects
                                INNER JOIN projects ON users_projects.projectid = projects.id
                                WHERE userid = '{userId}';''')
            projects = cursor.fetchall()

            projectNames = ""
            for project in projects:
                projectNames += project[0] + ", "
            
            if projectNames.strip() != "":
                projectNames = f"*Участник проектов*\: {self.auxiliary.filter(projectNames)}"[:-2]
            user = self.db.getUserById(userId)

            additionInfo = ""
            if user['educationalinstitution'] == "РЭУ им. Г.В. Плеханова":
                additionInfo = f" ({user['course']} курс, {user['faculty']}, по направлению «{user['direction']}», специальность «{user['speciality']}» в группе {user['group']})"
            bot.send_message(message.chat.id, f'''__Информация по пользователю @{self.auxiliary.filter(user['username'])}__\:

*ФИО*: _{user['lastname'] if user['lastname'] != None else ""} {user['firstname'] if user['firstname'] != None else ""} {user['patronymic'] if user['patronymic'] != None else ""}_

*Сфера деятельности*: _{self.auxiliary.filter(user['fieldofactivity']) if user['fieldofactivity'] is not None else self.auxiliary.filter("---")}_

*Учебное заведение*: _{self.auxiliary.filter(user['educationalinstitution']) if user['educationalinstitution'] is not None else self.auxiliary.filter("---")}{self.auxiliary.filter(additionInfo) if user['educationalinstitution'] is not None else ""}_

*О себе*: _{self.auxiliary.filter(user['aboutme']) if user['aboutme'] is not None else self.auxiliary.filter("---")}_

*Телефон*: _{self.auxiliary.filter(user['phonenum']) if user['phonenum'] is not None else self.auxiliary.filter("---")}_

*Email*: {self.auxiliary.filter(user['email']) if user['email'] is not None else self.auxiliary.filter("---")}

{projectNames.strip()}''', 
            reply_markup=self.keyboard.genMainKeyboard(message.from_user.id),
            parse_mode="MarkdownV2")
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Search user by @username / Surname Name / Surname
    def getUsernameForSelect(self, chatId):
        bot = self.bot

        msg = bot.send_message(chatId, "Введите данные пользователя в одном из форматов для вывода информации:\n(Пример: *@username*)\n(Пример: *Фамилия*)\n(Пример: *Фамилия Имя*)", reply_markup=self.keyboard.exitBtn(), parse_mode="Markdown")        
        bot.register_next_step_handler(message=msg, callback=self.process_getUsernameForSelect_step)

    def process_getUsernameForSelect_step(self, message):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            userInfoMsg = message.text.strip()

            dataFormat = ""
            if userInfoMsg.startswith('@'):
                userInfoMsg = userInfoMsg.strip('@')
                dataFormat = "userName"
            elif len(userInfoMsg.split(' ')) == 1:
                dataFormat = "lastName"
            elif len(userInfoMsg.split(' ')) == 2:
                dataFormat = "lastName_firstName"
            else:
                msg = bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден. Повторите ввод")
                bot.register_next_step_handler(msg, self.process_getUsernameForSelect_step)
                return

            userId = self.db.getUserIdByUsernameAndFIO(userInfoMsg, dataFormat)

            if userId == "-":
                msg = bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден. Повторите ввод")
                bot.register_next_step_handler(msg, self.process_getUsernameForSelect_step)
                return
            
            
            if not isinstance(userId, str):  
                for user in userId:
                    self.userInfo(message, user[0])
            else:
                self.userInfo(message, userId)        
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Update user info steps
    def getUsernameForUpdate(self, chatId):
        bot = self.bot

        msg = bot.send_message(chatId, "Введите никнейм пользователя для редактирования данных\n(Пример: @volodin)", reply_markup=self.keyboard.exitBtn())        
        bot.register_next_step_handler(message=msg, callback=self.process_getUsernameForUpdate_step)

    def process_getUsernameForUpdate_step(self, message):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            if self.db.getUserById(message.from_user.id)['status'].find("ADMIN") == -1:
                bot.send_message(chat_id=message.chat.id, text= f"Недостаточно прав")
                return 
            
            username = message.text.strip('@')
            userId = self.db.getUserIdByUsernameAndFIO(username, "userName")
            if userId == "-":
                msg = bot.send_message(chat_id=message.chat.id, text= f"Пользователь не найден. Повторите ввод")
                bot.register_next_step_handler(msg, self.process_getUsernameForUpdate_step)
            else:
                bot.send_message(chat_id=message.chat.id, text= f"Обновление данных пользователя @{username}")
                
                self.updateFullname(message.chat.id, userId)
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Fill passport info for pass to rea
    def fillPassportInfo(self, chatId, eventId):
        bot = self.bot

        msg = bot.send_message(chat_id=chatId, text=f"Введите серию и номер паспорта через пробел:\n(_1122 334455_)", parse_mode="Markdown", reply_markup=self.keyboard.exitBtn())
        bot.register_next_step_handler(msg, self.process_fillPassportInfo_step, eventId)

    def process_fillPassportInfo_step(self, message, eventId):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "notCompleted")
                return

            pattern = r'^\d{4} \d{6}$'
            if not re.match(pattern, message.text.strip()):
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод данных\n(Пример: _2233 445566_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_fillPassportInfo_step, eventId)
                return
            
            series = message.text.strip().split(' ')[0]
            number = message.text.strip().split(' ')[1]

            cursor.execute(f'''UPDATE users SET seriesPassport='{series}', numberPassport='{number}'
                                WHERE id = '{message.from_user.id}';''')
            connection.commit()

            cursor.execute(f'''UPDATE events_users SET needpass = {True} 
                            WHERE eventid = '{eventId}' and userid = '{message.from_user.id}';''')
            connection.commit()

            bot.send_message(message.from_user.id, "Данные сохранены, запрос на пропуск оформлен.", reply_markup=self.keyboard.genMainKeyboard(message.from_user.id))
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")
