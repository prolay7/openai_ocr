import os
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import pytesseract
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from PIL import Image, ExifTags
import requests

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
            SELECT * FROM `ocr_logs` WHERE `read_status`='pending' ORDER BY `doc_id` ASC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            for row in rows:
                print("File path:{row[6]}")
                 # Commit the transaction
                connection.commit()
    
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