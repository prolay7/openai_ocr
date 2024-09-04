import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path
import requests
import openai  # Ensure you have the openai package installed

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

# Set OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")  # Make sure your .env file has this key set


def extract_date_of_birth(extracted_text):
    """
    Extracts the date of birth from the extracted text using the GPT-4 API.
    The date of birth will be formatted as yyyy-mm-dd.
    """
    try:

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # Call the GPT-4 API to extract the date of birth
        

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract only Date of Birth from the following text:\n\n{extracted_text}. do not give any extra detail just reply date in given format  yyyy-mm-dd  you need to give response in this format only do not add any other details or any other thing."
                        }
                    ]
                }
            ]
        }
    
    
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        # Extract the response text
        extracted_dob = response['choices'][0]['message']['content'].strip()
        print(f"Extracted Date of Birth: {extracted_dob}")
        return extracted_dob

    except Exception as e:
        print(f"Error extracting date of birth: {e}")
        return None

def connect_and_read():
    connection = None  # Initialize connection before the try block
    cursor = None      # Initialize cursor to ensure it's defined if used in finally block

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
            SELECT * FROM `ocr_logs` WHERE `read_status`='completed' ORDER BY `doc_id` ASC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            for row in rows:

                extracted_text=row[3]

                dob=extract_date_of_birth(extracted_text);
            

                # If the data is found, update the response_data with the extracted text
                if row:
                    update_query = """
                    UPDATE `ocr_logs` 
                    SET `dob` = %s ,`read_status`='completed'
                    WHERE `id` = %s
                    """
                    cursor.execute(update_query, (dob,row[0]))
                    connection.commit()
                    print(f"Updated response_data for doc_id {row[0]}.")
                else:
                    print(f"No data found for doc_id {row[0]}.")

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Close the cursor if it exists
        if cursor:
            cursor.close()
        # Close the database connection
        if connection and connection.is_connected():
            connection.close()
            print("Connection closed")


connect_and_read()