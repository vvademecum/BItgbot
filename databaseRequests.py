

class DatabaseRequests:
    def __init__(self, connection):
        self.connection = connection

        cursor = connection.cursor()
        self.cursor = cursor

    def getProjectNameById(self, projectId):
        cursor = self.cursor

        cursor.execute(f'''SELECT name FROM projects WHERE id={projectId}''')
        return cursor.fetchone()[0]

    def getCountOfAllProjects(self):
        cursor = self.cursor
        
        cursor.execute(f'''SELECT COUNT(*) FROM projects;''')
        return cursor.fetchone()[0]

    def getCountOfProjectsForAuthor(self, userId):
        cursor = self.cursor

        cursor.execute(f'''SELECT COUNT(*) FROM projects 
                            INNER JOIN users_projects ON projects.id = users_projects.projectid
                            WHERE users_projects.userid = '{userId}' and users_projects.role = 'AUTHOR';''')
        return cursor.fetchone()[0]

    def getProjectsInPage(self, page):
        cursor = self.cursor

        buttons_per_page = 8
        cursor.execute(f'''SELECT name, id FROM projects
                            ORDER BY name
                            LIMIT {buttons_per_page} OFFSET {page-1} * {buttons_per_page};''')
        items = cursor.fetchall()
        return items

    def getProjectsForVacancyInPage(self, page, userId):
        cursor = self.cursor

        buttons_per_page = 8

        cursor.execute(f'''SELECT projects.name, projects.id FROM projects
                            INNER JOIN users_projects ON projects.id = users_projects.projectid
                            WHERE users_projects.userid = '{userId}' and users_projects.role = 'AUTHOR'
                            ORDER BY projects.name
                            LIMIT {buttons_per_page} OFFSET {page-1} * {buttons_per_page};''')    
        items = cursor.fetchall()
        return items

    def getUserById(self, userId):
        cursor = self.cursor

        cursor.execute(f'''SELECT * FROM users 
                            WHERE id = '{userId}';''')

        columns = [desc[0] for desc in cursor.description]
        items = cursor.fetchone()
        user = dict(zip(columns, items))
        return user

    def getProjectById(self, projectId):
        cursor = self.cursor

        cursor.execute(f'''SELECT * FROM projects 
                            WHERE id = '{projectId}';''')
        
        columns = [desc[0] for desc in cursor.description]
        items = cursor.fetchone()
        project = dict(zip(columns, items))
        return project

    def getUserIdByUsernameAndFIO(self, userInfoMsg, dataFormat):
        cursor = self.cursor

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
        
    def getProjectIdByProjectname(self, name):
        cursor = self.cursor

        cursor.execute(f'''SELECT EXISTS(SELECT 1 FROM projects
                                    WHERE name = '{name}');''')
        exists = cursor.fetchone()[0]
        if not exists:
            return "-"

        cursor.execute(f'''SELECT id FROM projects 
                            WHERE name = '{name}';''')
        projectId = cursor.fetchone()[0]
        return projectId 

    def getEventNameAndMeetingDateById(self, eventId):
        cursor = self.cursor

        cursor.execute(f"SELECT name, meetingdate FROM events WHERE id='{eventId}'")
        
        NameAndMeetingDate = cursor.fetchone()
        return NameAndMeetingDate

    def pollIsActive(self, poll_id):
        cursor = self.cursor

        cursor.execute(f"SELECT EXISTS (SELECT id FROM events WHERE id='{poll_id}' and isactive=true);")
        isActive = cursor.fetchone()[0]

        return isActive
    
