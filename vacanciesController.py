import re
from telebot import types
import datetime

import config
from databaseRequests import DatabaseRequests
from keyboards import Keyboards
from auxiliary import Auxiliary

class VacanciesController:
    def __init__(self, bot, connection):
        self.bot = bot

        self.connection = connection

        cursor = connection.cursor()
        self.cursor = cursor

        self.db = DatabaseRequests(connection)
        self.keyboard = Keyboards(connection)
        self.auxiliary = Auxiliary(bot, connection)

# -------------- Insert new vacancy steps
    def addNewVacancy(self, chatId, projectId):
        bot = self.bot

        projectName = self.db.getProjectNameById(projectId)

        msg = bot.send_message(chat_id=chatId, text=f"Введите наименование должности для проекта *{self.auxiliary.filter(projectName)}*\:\n\(_Стажёр\-маркетолог_\)", parse_mode="MarkdownV2", reply_markup=self.keyboard.exitBtn())
        bot.register_next_step_handler(msg, self.process_nameOfPostVacancy_step, projectId)

    def process_nameOfPostVacancy_step(self, message, projectId):
        try:
            bot = self.bot

            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            post = message.text

            if len(post) < 3:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод наименования должности:', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_nameOfPostVacancy_step, projectId)
                return

            msg = bot.reply_to(message, f'Требования вакансии *«{self.auxiliary.filter(post)}»*\:', parse_mode="MarkdownV2")
            bot.register_next_step_handler(msg, self.process_requirementsVacancy_step, projectId, post) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_requirementsVacancy_step(self, message, projectId, post):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            requirements = message.text

            if len(requirements) < 8:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод требований вакансии:', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_requirementsVacancy_step, projectId, post)
                return

            msg = bot.reply_to(message, f'Описание вакансии *«{self.auxiliary.filter(post)}»*\:', parse_mode="MarkdownV2")
            bot.register_next_step_handler(msg, self.process_descriptionVacancy_step, projectId, post, requirements)  
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_descriptionVacancy_step(self, message, projectId, post, requirements):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            description = message.text

            if len(description) < 8:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод описание вакансии:', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_descriptionVacancy_step, projectId, post, requirements)
                return

            msg = bot.reply_to(message, f'Введите контактные данные, по которым будут связываться по данной вакансии\:\n\(_TG\: \@username\; mail\: exmpl@gmail\.com\; \+79993457676\; Иванов Иван_\)', parse_mode="MarkdownV2")
            bot.register_next_step_handler(msg, self.process_contactsVacancy_step, projectId, post, requirements, description)  
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_contactsVacancy_step(self, message, projectId, post, requirements, description):
        try:
            bot = self.bot
            
            if message.text == "↩ Выйти":
                self.auxiliary.exitStepHandler(message, "ok")
                return

            contacts = message.text

            if len(contacts) < 4:
                msg = bot.reply_to(message, 'Неверный формат, повторите ввод контактных данных:\n\(_TG\: \@username\; mail\: exmpl@mail\.ru\; \+79993457676\; Иванов Иван_\)', parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_contactsVacancy_step, projectId, post, requirements, description)
                return

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('🔴 Повторить ввод', '🟢 Все верно')

            projectName = self.db.getProjectNameById(projectId)

            msg = bot.send_message(message.chat.id, f'''Проверьте правильность заполнения данных:
                                
Вакансия в стартап *«{self.auxiliary.filter(projectName)}»*\:

_Наименование должности:_ *{self.auxiliary.filter(post)}*

_Требования:_ *{self.auxiliary.filter(requirements)}*

_Описание:_ *{self.auxiliary.filter(description)}* 

_Контакты:_ *{self.auxiliary.filter(contacts)}*''', parse_mode="MarkdownV2", reply_markup=markup)
            bot.register_next_step_handler(msg, self.process_isRepeatFillingVacancy_step, projectId, post, requirements, description, contacts) 
        except Exception as e:
            print(e)
            self.auxiliary.exitStepHandler(message, "error")

    def process_isRepeatFillingVacancy_step(self, message, projectId, post, requirements, description, contacts):
        try:
            if message.text == "🔴 Повторить ввод":
                self.addNewVacancy(message.chat.id, projectId)
            elif message.text == "🟢 Все верно":
                bot = self.bot
                cursor = self.cursor
                connection = self.connection

                cursor.execute(f'''INSERT INTO vacancies (post, requirements, job_description, contacts, projectid, isActive, newVacancy) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id''', 
                            (post, requirements, description, contacts, projectId, True, True))
                newVacancyId = cursor.fetchone()[0]
                connection.commit()
                
                cursor.execute("SELECT id FROM users WHERE status && '{PROJECT_MANAGER}';")
                projectManagerId = cursor.fetchone()[0]

                bot.send_message(projectManagerId, f"Новая вакансия в проекте *«{self.auxiliary.filter(self.db.getProjectNameById(projectId))}»*", parse_mode="Markdown", reply_markup=self.keyboard.markupExcelVacancies())

                self.auxiliary.exitStepHandler(message, "ok")
            else:   
                msg = bot.send_message(chat_id=message.chat.id, text="Проверьте данные и сделайте выбор", parse_mode="Markdown")
                bot.register_next_step_handler(msg, self.process_isRepeatFillingVacancy_step, projectId, post, requirements, description, contacts)

        except Exception as ex:
            print("Error: ", ex)
            self.auxiliary.exitStepHandler(message, "error")


