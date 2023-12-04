import psycopg2
import csv
import config
from enum import Enum, auto

# try:
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
cur.execute('''CREATE TABLE vacancies (id SERIAL NOT NULL PRIMARY KEY UNIQUE, 
            post TEXT NOT NULL,
            requirements TEXT,
            job_description TEXT,
            contacts TEXT,
            isActive BOOLEAN,
            newVacancy BOOLEAN,
            projectId INT NOT NULL REFERENCES projects(id))''')
connection.commit()