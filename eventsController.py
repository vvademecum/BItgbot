import re
from telebot import types
import datetime

import config
from databaseRequests import DatabaseRequests
from keyboards import Keyboards
from auxiliary import Auxiliary

class EventsController:
    def __init__(self, bot, connection):
        self.bot = bot

        self.connection = connection

        cursor = connection.cursor()
        self.cursor = cursor

        self.db = DatabaseRequests(connection)
        self.keyboard = Keyboards(connection)
        self.auxiliary = Auxiliary(bot, connection)

# -------------- Insert new event steps
    def createNewEvent(self, chatId):
        bot = self.bot

        msg = bot.send_message(chat_id=chatId, text=f"Введите дату проведения мероприятия:\n(_День.Месяц.Год Час:Мин_)", parse_mode="Markdown", reply_markup=self.keyboard.exitBtn())
        bot.register_next_step_handler(msg, self.process_meetingDate_step)
    
    def process_meetingDate_step(self, message):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            meetingDate = message.text
            
            now = datetime.datetime.now()
            try:
                dt = datetime.datetime.strptime(meetingDate, "%d.%m.%y %H:%M")
                if dt <= now:
                    msg = bot.reply_to(message, 'Неверный формат, повторите ввод даты и времени мероприятия:\n(Пример: _18.11.23 17:00_)', parse_mode="Markdown")
                    bot.register_next_step_handler(msg, self.process_meetingDate_step)                
                    return
            except Exception as e:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод даты и времени мероприятия:\n(Пример: _18.11.23 17:00_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_meetingDate_step)
                return
        
            msg = bot.reply_to(message, 'Наименование мероприятия:', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_nameEvent_step, meetingDate) 
            
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_nameEvent_step(self, message, meetingDate):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            nameEvent = message.text

            if len(nameEvent) < 5:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод наименования мероприятия', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_nameEvent_step, meetingDate)
                return

            msg = bot.reply_to(message, 'Информация о мероприятии и описание:', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_descriptionEvent_step, meetingDate, nameEvent) 
            
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_descriptionEvent_step(self, message, meetingDate, nameEvent):
        try:
            bot = self.bot

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            description = message.text

            if len(description) < 8:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод информации о мероприятии и описания', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_descriptionEvent_step, meetingDate, nameEvent)
                return

            msg = bot.reply_to(message, 'Дедлайн голосования:\n(_День.Месяц.Год Час:Мин_)', parse_mode="Markdown")
            bot.register_next_step_handler(msg, self.process_deadlineEvent_step, meetingDate, nameEvent, description) 
            
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_deadlineEvent_step(self, message, meetingDate, nameEvent, description):
        try:
            bot = self.bot

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return
            
            deadline = message.text

            now = datetime.datetime.now()
            try:
                dt = datetime.datetime.strptime(deadline, "%d.%m.%y %H:%M")
                deadlineMin = int(dt.strftime('%M'))

                if dt <= now or dt >= datetime.datetime.strptime(meetingDate, "%d.%m.%y %H:%M") or deadlineMin % 5 != 0:
                    msg = bot.reply_to(message, 'Неверный формат, повторите ввод даты и времени окончания голосования\n(Пример: _17.11.23 21:00_)', parse_mode="Markdown")
                    bot.register_next_step_handler(msg, self.process_deadlineEvent_step, meetingDate, nameEvent, description)
                    return
                
            except Exception as e:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод даты и времени окончания голосования\n(Пример: _17.11.23 21:00_)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_deadlineEvent_step, meetingDate, nameEvent, description)
                return

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('🔴 Повторить ввод', '🟢 Все верно')

            msg = bot.send_message(message.chat.id , f'''__Опрос будет выглядеть следующим образом\. Отправляем?__
                            
    *{self.auxiliary.filter(meetingDate)}* состоится новое мероприятие\!
    __{self.auxiliary.filter(nameEvent)}__
    {self.auxiliary.filter(description)}

    _*Дедлайн по голосованию:* {self.auxiliary.filter(deadline)}_''', parse_mode="MarkdownV2", reply_markup=markup)
            bot.register_next_step_handler(msg, self.process_isRepeatFillingEvent_step, meetingDate, nameEvent, description, deadline) 
            
        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")

    def process_isRepeatFillingEvent_step(self, message, meetingDate, nameEvent, description, deadline):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection

            if message.text == "🔴 Повторить ввод":
                self.createNewEvent(message.chat.id)
            elif message.text == "🟢 Все верно":

                question = f"{nameEvent} - {meetingDate}"
                options = ["Приду", "Не смогу"]
                bot.send_message(chat_id=config.RESIDENT_GROUP_ID, text=f'''*{self.auxiliary.filter(meetingDate)}* состоится новое мероприятие\!
    __{self.auxiliary.filter(nameEvent)}__
    {self.auxiliary.filter(description)}

    _*Дедлайн по голосованию:* {self.auxiliary.filter(deadline)}_''', parse_mode="MarkdownV2")
                pollMessage = bot.send_poll(chat_id=config.RESIDENT_GROUP_ID, question=question, options=options, is_anonymous=False)

                meetingDate = f"{meetingDate.split('.')[1]}.{meetingDate.split('.')[0]}.{meetingDate[6:]}"
                deadline = f"{deadline.split('.')[1]}.{deadline.split('.')[0]}.{deadline[6:]}"

                cursor.execute(f'''INSERT INTO events (id, name, description, meetingdate, isactive, polldeadline) VALUES (%s, %s, %s, %s, %s, %s)''', 
                            (pollMessage.json['poll']['id'], nameEvent, description, meetingDate, True, deadline))
                connection.commit()
                
                self.auxiliary.exitStepHandler(message, "ok")
            else:   
                msg = bot.send_message(chat_id=message.chat.id, text="Проверьте данные и сделайте выбор", parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_isRepeatFillingEvent_step, meetingDate, description, deadline)

        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


# -------------- Newsletters in poll deadline
    def eventDeadlineNewsletter(self, events):
        try:
            bot = self.bot
            cursor = self.cursor
            connection = self.connection
            
            cursor.execute("SELECT id FROM users WHERE status && '{DOCUMENT_MANAGER}';")
            docManagerId = cursor.fetchone()[0]

            for id in events:
                cursor.execute(f"UPDATE events SET isactive = false WHERE id = '{id[0]}';")
                connection.commit()

                cursor.execute(f'''SELECT COUNT(*) FROM events_users WHERE eventid='{id[0]}' AND isgoingtocome = true;''')
                countOfPlanningToCome = cursor.fetchone()[0]

                cursor.execute(f'''SELECT COUNT(*) FROM events_users 
                            INNER JOIN users ON events_users.userid=users.id
                            WHERE eventid='{id[0]}' AND isgoingtocome=true AND educationalinstitution='РЭУ им. Г.В. Плеханова';''')
                countOfFromREA = cursor.fetchone()[0]
                countOfFromAnother = countOfPlanningToCome - countOfFromREA

                cursor.execute(f'''SELECT COUNT(*) FROM events_users WHERE eventid='{id[0]}' AND isgoingtocome = true AND needmemo = true;''')
                countOfneedMemo = cursor.fetchone()[0]

                cursor.execute(f'''SELECT COUNT(*) FROM events_users WHERE eventid='{id[0]}' AND isgoingtocome = true AND needpass = true;''')
                countOfneedPass = cursor.fetchone()[0]

                NameAndMeetingDate = self.db.getEventNameAndMeetingDateById(id[0])

                bot.send_message(docManagerId, f'''На мероприятие *«{self.auxiliary.filter(NameAndMeetingDate[0])}»* \- _{self.auxiliary.filter(str(NameAndMeetingDate[1].strftime('%d.%m.%Y %H:%M')))}_:

    *Зарегистрировалось:* {countOfPlanningToCome} чел\.
    *Резиденты из РЭУ:* {countOfFromREA} чел\.
    *Резиденты из других ВУЗов:* {countOfFromAnother} чел\.
    *Запросили служебную записку:* {countOfneedMemo} чел\.
    *Запросили пропуск на территорию:* {countOfneedPass} чел\.''', parse_mode="MarkdownV2")
                
                if countOfneedMemo > 0:
                    query_string = f'''SELECT users.id, CONCAT('@', username) AS username, lastname, firstname, patronymic, faculty, course, direction, speciality, "group" 
                                        FROM events_users 
                                        INNER JOIN users ON events_users.userid=users.id
                                        WHERE eventid='{id[0]}' AND isgoingtocome = true AND needmemo = true;'''
                    filepath = "needMemoList.xlsx"

                    self.auxiliary.export_to_excel(query_string,("Имя пользователя tg", "Фамилия", "Имя", "Отчество", "Факультет", "Курс", "Направление", "Специальность", "Группа"), filepath)
                    with open('needMemoList.xlsx', 'rb') as tmp:
                        bot.send_document(chat_id=docManagerId, document=tmp, caption="Список запросивших служебное освобождение")

                if countOfneedPass > 0:
                    query_string = f'''SELECT users.id, CONCAT('@', username) AS username, lastname, firstname, patronymic, seriespassport, numberpassport
                                        FROM events_users 
                                        INNER JOIN users ON events_users.userid=users.id
                                        WHERE eventid='{id[0]}' AND isgoingtocome = true AND needpass = true;'''
                    filepath = "needPassList.xlsx"

                    self.auxiliary.export_to_excel(query_string,("Имя пользователя tg", "Фамилия", "Имя", "Отчество", "Серия паспорта", "Номер паспорта"), filepath)
                    with open('needPassList.xlsx', 'rb') as tmp:
                        bot.send_document(chat_id=docManagerId, document=tmp, caption="Список запросивших пропуск")

                self.eventDeadlineNewsletterForResidents(id[0])
        except Exception as e:
            print("Error in Newsletter For DocManager: ", e)

    def eventDeadlineNewsletterForResidents(self, eventId):
        try:
            bot = self.bot
            cursor = self.cursor
            
            cursor.execute(f'''SELECT userid FROM events_users WHERE eventid='{eventId}' AND isgoingtocome = true;''')
            isGoingToComeUserIds = cursor.fetchall()
            nameAndMeetingDate = self.db.getEventNameAndMeetingDateById(eventId)

            for userId in isGoingToComeUserIds:
                bot.send_message(userId[0], f'''Привет\! Мы ждем тебя на мероприятии *«{self.auxiliary.filter(nameAndMeetingDate[0])}»*, на которое ты записался\! Оно состоится _{self.auxiliary.filter(str(self.NameAndMeetingDate[1].strftime('%d.%m.%Y %H:%M')))}_\.''', parse_mode="MarkdownV2")
        except Exception as e:
            print("Error in Newsletter For Residents: ", e)

    def isTimeToNewsletterForDocManager(self):
        try:
            cursor = self.cursor
            
            now = datetime.datetime.now() 
            current_time = now.strftime("%Y-%m-%d %H:%M")
            print(current_time)

            cursor.execute(f'''SELECT id, polldeadline FROM events WHERE 
                                EXISTS (SELECT polldeadline FROM events 
                                WHERE isactive=true and polldeadline='{current_time}') 
                                and isactive=true and polldeadline='{current_time}';''')
            events = cursor.fetchall()

            if len(events) > 0:
                self.eventDeadlineNewsletter(events)
        except Exception as e:
            print("Error in isTimeToNewsletterForDocManager(): " + e)