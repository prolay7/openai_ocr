import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# Define the path to the .env file relative to the current file's location
env_path = Path(__file__).resolve().parent / '.env'
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
print(f"APP_URL: {os.getenv('APP_URL')}")  # Print APP_URL to ensure it's loaded
print(f"FILE_DIRECTORY: {os.getenv('FILE_DIRECTORY')}")  # Print FILE_DIRECTORY to ensure it's loaded

def connect_and_read():
    connection = None  # Initialize connection before the try block
    try:
        # Fetch APP_URL and FILE_DIRECTORY from environment variables
        app_url = os.getenv("APP_URL")
        file_directory = os.getenv("FILE_DIRECTORY")  # Directory where files are expected
        if not app_url or not file_directory:
            print("Error: APP_URL or FILE_DIRECTORY is not set in the environment variables.")
            return

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

            # Define the query to read data from the avsdocs and users tables
            query = f"""
            SELECT `avsdocs`.`id`, `users`.`id` AS user_id, CONCAT('{app_url}', `avsdocs`.`doc_url`) AS doc_url, `avsdocs`.`doc_file_type`
            FROM `avsdocs`
            LEFT JOIN `users` ON `users`.`id` = `avsdocs`.`user_id`
            WHERE `users`.`age_verified` <> 'YES'
            ORDER BY `avsdocs`.`id` DESC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            # Insert the fetched data into the ocr_logs table if the file exists
            insert_query = """
            INSERT INTO ocr_logs (doc_id, user_id, file_path, file_type, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            for row in rows:
                file_path = os.path.join(file_directory, row[2].replace(f'{app_url}/', ''))
                
                # Check if the file exists in the specified directory
                if os.path.exists(file_path):
                    cursor.execute(insert_query, (row[0], row[1], row[2], row[3], '0'))
                else:
                    print(f"File not found: {file_path}")

            # Commit the transaction
            connection.commit()
            print("Data inserted into ocr_logs table")

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
