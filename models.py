import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="jiyabharti"
)

print(mydb)


mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

for x in mycursor:
  print(x)



