import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# Define the path to the .env file relative to the current file's location
env_path = Path(__file__).resolve() / '.env'
print(f"Loading .env file from: {env_path}")

# Load environment variables from the .env file
if load_dotenv(dotenv_path=env_path):
    print("Environment variables loaded successfully.")
else:
    print("Failed to load environment variables.")

# Print environment variables for debugging
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_USERNAME: {os.getenv('DB_USERNAME')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_DATABASE: {os.getenv('DB_DATABASE')}")

def connect_and_read():
    connection = None  # Initialize connection before the try block
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),           # e.g., 'localhost' or the server's IP
            user=os.getenv("DB_USERNAME"),       # e.g., 'root'
            password=os.getenv("DB_PASSWORD"),   # your MySQL password
            database=os.getenv("DB_DATABASE")    # the database name
        )

        if connection.is_connected():
            print("Connected to the database")

            # Create a cursor object
            cursor = connection.cursor()

            # Define the query to read data from the users table
            query = """
            SELECT `users`.`id`, `avsdocs`.`doc_url`, `avsdocs`.`doc_file_type`
            FROM `avsdocs`
            LEFT JOIN `users` ON `users`.`id` = `avsdocs`.`user_id`
            WHERE `users`.`age_verified` <> 'YES'
            ORDER BY `avsdocs`.`id` DESC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            # Display the results
            for row in rows:
                print(row)

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the database connection
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Connection closed")

# Run the function
connect_and_read()
