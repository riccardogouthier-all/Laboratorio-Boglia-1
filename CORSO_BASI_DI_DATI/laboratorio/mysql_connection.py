import mysql.connector
import json

db = mysql.connector.connect(
host = 'localhost',
user = 'host',
password = 'root',
database = 'its2026'
)


cursor = db.cursor()

cursor.execute("SHOW TABLES")

for database in cursor.fetchall():
    print(database)

cursor.execute("select * from games")

games = cursor.fetchall()



for game in games:
    print(game[1])

db.commit()