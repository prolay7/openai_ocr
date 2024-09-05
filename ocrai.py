import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from openai import OpenAI  # Ensure you have the openai package installed

# Define the path to the .env file relative to the current file's location
env_path = Path(__file__).resolve().parent / '.env'
print(f"Loading .env file from: {env_path}")

# Load environment variables from the .env file
if load_dotenv(dotenv_path=env_path):
    print("Environment variables loaded successfully.")
else:
    print("Failed to load environment variables.")

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def extract_dob_from_text(text):
    """
    Sends extracted text to GPT-4 to identify the DOB.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts dates of birth from the provided text.",
                },
                {
                    "role": "user",
                    "content": f"Extract the date of birth or DOB or Date of birth or Dale de naissance Fechi de oicimiento from the following text:\n\n{text} in yyyy-mm-dd format only and do not send any other data alongwith the DOB.",
                },
            ],
        )
        
        # Extract DOB from the response
        dob = response.choices[0].message.content.strip()
        # Check if the extracted DOB matches the YYYY-MM-DD format
        if dob and len(dob) == 10 and dob[4] == '-' and dob[7] == '-':
            print(f"Extracted DOB: {dob}")
            return dob

        print("Error: DOB extraction failed or format is incorrect.")
        return None

    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return None

def connect_and_read_ocai():
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

            # Define the query to read data from the ocr_logs table
            query = f"""
            SELECT * FROM `ocr_logs` WHERE `read_status`='completed' ORDER BY `doc_id` ASC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            for row in rows:
                # Check if status is '0' before extracting DOB
                if row[5] == '0':  # Assuming the status is in the 6th column (index 5)
                    extracted_text = row[3]
                    dob = extract_dob_from_text(extracted_text)
                    
                    # Determine the appropriate status based on the result of DOB extraction
                    if dob:
                        status = 'dob_extracted'
                    else:
                        status = "Error: Failed to extract DOB"

                    # Update the record in the ocr_logs table
                    update_query = """
                    UPDATE `ocr_logs` 
                    SET `dob` = %s, `status` = %s
                    WHERE `id` = %s
                    """
                    cursor.execute(update_query, (dob if dob else '', status, row[0]))
                    connection.commit()
                    print(f"Updated record for doc_id {row[0]}.")
                else:
                    print(f"Skipping doc_id {row[0]} with status {row[5]}.")

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

print("Starting connect_and_read_ocai...")
connect_and_read_ocai()
print("connect_and_read_ocai completed.")