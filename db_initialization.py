import psycopg2
import csv
import config
from enum import Enum, auto

try:
    connection = psycopg2.connect(
        host="localhost",
        user="admin",
        password="root",
        database="bitelegramdb",
        port=6101
    )

    print('[INFO] PostgreSQL start')

    cur = connection.cursor()

    # cur.execute("CREATE TYPE role AS ENUM ('RESIDENT', 'ADMIN', 'EVENT_MANAGER', 'DOCUMENT_MANAGER', 'PROJECT_MANAGER', 'ROOT')")
    # cur.execute("CREATE TYPE categoryProject AS ENUM ('Креативные индустрии', 'Медицина и образование', 'Социальные', 'Технологические', 'Экологические')")
    # cur.execute("CREATE TYPE roleInProject AS ENUM ('AUTHOR', 'PARTNER')")

    # cur.execute("ALTER TYPE role ADD VALUE 'PROJECT_MANAGER';")
    # connection.commit()


    cur.execute('''CREATE TABLE users (id VARCHAR(100) PRIMARY KEY UNIQUE, 
                    username VARCHAR(255) UNIQUE, 
                    firstName VARCHAR(100), 
                    lastName VARCHAR(100), 
                    patronymic VARCHAR(100), 
                    fieldOfActivity TEXT, 
                    aboutMe TEXT,
                    educationalInstitution TEXT,
                    faculty TEXT,
                    course VARCHAR(1),
                    direction TEXT,
                    speciality TEXT,
                    "group" VARCHAR(30),
                    seriesPassport VARCHAR(4),
                    numberPassport VARCHAR(6),
                    phoneNum VARCHAR(12),
                    email VARCHAR(100),
                    status role[])''')
    
    cur.execute('''CREATE TABLE projects (id SERIAL NOT NULL PRIMARY KEY UNIQUE, 
                    name VARCHAR(255) UNIQUE, 
                    description TEXT, 
                    category categoryProject)''')
    
    cur.execute('''CREATE TABLE users_projects (id SERIAL NOT NULL PRIMARY KEY UNIQUE, 
                    projectId INT NOT NULL REFERENCES projects(id),
                    userId VARCHAR(100) NOT NULL REFERENCES users(id),
                    role roleInProject)''')
    
    cur.execute('''CREATE TABLE events (id VARCHAR(100) NOT NULL PRIMARY KEY UNIQUE, 
                    name TEXT,    
                    description TEXT,     
                    meetingDate TIMESTAMP,
                    isActive BOOLEAN,
                    pollDeadline TIMESTAMP)''')
    
    cur.execute('''CREATE TABLE events_users (id SERIAL NOT NULL PRIMARY KEY UNIQUE, 
                    eventId VARCHAR(100) NOT NULL REFERENCES events(id),
                    userId VARCHAR(100) NOT NULL REFERENCES users(id),
                    isGoingToCome BOOLEAN,
                    needMemo BOOLEAN,
                    needPass BOOLEAN,
                    unique(eventId, userId))''')
    
    cur.execute('''CREATE TABLE vacancies (id SERIAL NOT NULL PRIMARY KEY UNIQUE, 
                    post TEXT NOT NULL,
                    requirements TEXT,
                    job_description TEXT,
                    contacts TEXT,
                    isActive BOOLEAN,
                    newVacancy BOOLEAN,
                    projectId INT NOT NULL REFERENCES projects(id))''')

    with open('mytest.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
    
        for row in reader:
            user_id = row['user id']

            if user_id != config.BOT_ID:
                cur.execute('''INSERT INTO users (id, username, firstName, lastName, status) VALUES (%s, %s, %s, %s, '{RESIDENT}') 
                            On CONFLICT(id) DO UPDATE
                            SET (username, firstName, lastName, status) = (EXCLUDED.username, EXCLUDED.firstName, EXCLUDED.lastName, EXCLUDED.status);''',
                            (row['user id'], row['username'], row['first_name'], row['last_name']))
    connection.commit() 

    # with open('asdzxc.csv', newline='', encoding='utf-8') as csvfile:
    #     reader = csv.DictReader(csvfile)
    
    #     for row in reader:
    #         cur.execute('''INSERT INTO projects (name, description, category) VALUES ( %s, %s, %s) 
    #                     On CONFLICT(id) DO UPDATE
    #                     SET (name, description, category) = (EXCLUDED.name, EXCLUDED.description, EXCLUDED.category);''',
    #                     (row['name'], row['description'], row['category']))
    # connection.commit() 

except Exception as ex:
    print('[INFO] Error postgresql ', ex)