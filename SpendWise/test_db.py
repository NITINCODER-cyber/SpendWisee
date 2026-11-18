
import mysql.connector
import db_config

# Connect to MySQL
mydb = mysql.connector.connect(
    host=db_config.host,
    user=db_config.user,
    password=db_config.password,
    database=db_config.database
)

# Check connection
if mydb.is_connected():
    print("SpendWise Database Connected!")

# Close connection
mydb.close()
