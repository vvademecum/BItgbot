from telebot import types

from databaseRequests import DatabaseRequests

class Keyboards:
    def __init__(self, connection):

        self.connection = connection
        self.db = DatabaseRequests(connection)

    def create_inline_keyboard(self, items, page, forVacancy, userId):
        try:
            callbackProject = "project_"
            callbackPrev = "prev_"
            callbackNext = "next_" 
            
            countOfProjects = self.db.getCountOfAllProjects()

            if forVacancy:
                callbackProject = "projectVac_"
                callbackPrev = "prevVac_"
                callbackNext = "nextVac_"
                countOfProjects = self.db.getCountOfProjectsForAuthor(userId)

            buttons_per_page = 8  
            start_idx = (page - 1) * buttons_per_page
            
            leftBtn = countOfProjects - start_idx
            end_idx = start_idx + leftBtn if leftBtn < buttons_per_page else start_idx + buttons_per_page

            keyboard = types.InlineKeyboardMarkup(row_width=2)

            for i in range(0, len(items), 2):
                button1 = types.InlineKeyboardButton(items[i][0], callback_data=f'{callbackProject}{items[i][1]}')
                if i + 1 == len(items):
                    keyboard.add(button1)
                    break
                button2 = types.InlineKeyboardButton(items[i+1][0], callback_data=f'{callbackProject}{items[i+1][1]}')
                keyboard.row(button1, button2)

            if page > 1 and end_idx < countOfProjects:
                prev_button = types.InlineKeyboardButton('⬅', callback_data=f'{callbackPrev}{page}')
                next_button = types.InlineKeyboardButton('➡', callback_data=f'{callbackNext}{page}')
                keyboard.row(prev_button, next_button)
            elif page == 1 and leftBtn <= buttons_per_page and not forVacancy:
                announceProject_button = types.InlineKeyboardButton('✉ Заявить о новом проекте', callback_data=f'announce_project')
                keyboard.add(announceProject_button)
            elif end_idx < countOfProjects:
                next_button = types.InlineKeyboardButton('➡', callback_data=f'{callbackNext}{page}')
                keyboard.add(next_button)
            elif page > 1:
                if not forVacancy:
                    announceProject_button = types.InlineKeyboardButton('✉ Заявить о новом проекте', callback_data=f'announce_project')
                    keyboard.add(announceProject_button)
                prev_button = types.InlineKeyboardButton('⬅', callback_data=f'{callbackPrev}{page}')
                keyboard.add(prev_button)

            return keyboard
        except Exception as e:
            print("Error in generate inline keyboard (projects):" + e)

    def genMainKeyboard(self, userId):
        user = self.db.getUserById(userId)

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        if user['status'].find("RESIDENT") != -1:
            editInfoBtnText = "📝 Заполнить информацию о себе"
            if user['fieldofactivity'] != None and str(user['fieldofactivity']).strip() != "":
                editInfoBtnText = "📝 Редактировать информацию о себе"
            
            updateProfileBtn = types.KeyboardButton(text=editInfoBtnText)
            updateProjectGroupBtn = types.KeyboardButton(text="🗂 Добавить информацию о проекте")
            addVacancyBtn = types.KeyboardButton(text="📃 Добавить вакансию для своего проекта")

            keyboard.add(updateProfileBtn, updateProjectGroupBtn, addVacancyBtn)
        if user['status'].find("ADMIN") != -1:
            adminPanelBtn = types.KeyboardButton(text="🛠️ Панель администратора")
            keyboard.add(adminPanelBtn)
        if user['status'].find("EVENT_MANAGER") != -1:
            newEventBtn = types.KeyboardButton(text="🎟️ Новое мероприятие")
            keyboard.add(newEventBtn)
        if user['status'].find("PROJECT_MANAGER") != -1:
            getVacanciesBtn = types.KeyboardButton(text="🎟️ Выгрузить вакансии")
            keyboard.add(getVacanciesBtn)
        return keyboard

    def inlineAdminPanel(self):
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        updateUserInfoBtn = types.InlineKeyboardButton('✏️ Обновить информацию о пользователе', callback_data=f'update_user_info')
        getUserInfoBtn = types.InlineKeyboardButton('👤 Информация о пользователе ', callback_data=f'get_user_info')
        getProjectInfoBtn = types.InlineKeyboardButton('📗 Информация о проекте', callback_data=f'get_project_info')
        getUsersExcelBtn = types.InlineKeyboardButton('📁 Выгрузить Excel по пользователям', callback_data=f'get_users_excel')
        getProjectsExcelBtn = types.InlineKeyboardButton('🗃 Выгрузить Excel по проектам', callback_data=f'get_projects_excel')

        keyboard.add(updateUserInfoBtn, getUserInfoBtn, getProjectInfoBtn, getUsersExcelBtn, getProjectsExcelBtn)
        return keyboard

    def markupExcelVacancies(self):
        markup = types.InlineKeyboardMarkup(row_width=1)
        getVacanciesExcelBtn = types.InlineKeyboardButton('🗃 Выгрузить Excel всем вакансиям', callback_data=f'get_vacancies_excel')
        
        markup.add(getVacanciesExcelBtn)
        return markup
    
    def exitBtn(self):
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        goHomeBtn = types.KeyboardButton(text="↩ Выйти")
        
        keyboard.add(goHomeBtn)
        return keyboard
    
    def editCommandBtn(self, projectId):
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kickPartnerBtn = types.InlineKeyboardButton('Редактировать команду', callback_data=f'deletePartnerFrom_{projectId}')
        
        keyboard.add(kickPartnerBtn)
        return keyboard