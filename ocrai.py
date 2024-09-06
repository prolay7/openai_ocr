import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from openai import OpenAI
import tiktoken
from datetime import datetime

# Define the path to the .env file relative to the current file's location
env_path = Path(__file__).resolve().parent / '.env'
print(f"Loading .env file from: {env_path}")

# Load environment variables from the .env file
if load_dotenv(dotenv_path=env_path):
    print("Environment variables loaded successfully.")
else:
    print("Failed to load environment variables.")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def count_tokens(messages, model="gpt-4"):
    """
    Counts the number of tokens in a list of messages for the specified model using tiktoken.
    """
    # Initialize the encoder with the model name
    encoding = tiktoken.encoding_for_model(model)

    # Calculate the total tokens
    total_tokens = 0
    for message in messages:
        # Calculate tokens for role and content
        total_tokens += len(encoding.encode(message['role']))
        total_tokens += len(encoding.encode(message['content']))

    return total_tokens

def calculate_cost(tokens, model="gpt-4"):
    """
    Calculates the cost of the API call based on the token count.
    """
    # Example pricing per 1,000 tokens - update with the latest pricing
    cost_per_1000_tokens = float(os.environ.get("TOKEN_COST", 0.03))  # Use a default value if not set

    # Calculate the total cost
    cost = (tokens / 1000) * cost_per_1000_tokens
    return cost

def insert_cost_to_db(file_id, cost):
    """
    Inserts the cost of the API call into the ocr_api_cost table.
    """
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE")
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Define the query to insert the cost into ocr_api_cost table
            insert_query = """
            INSERT INTO `ocr_api_cost` (`id`, `file_id`, `cost`, `created_at`) 
            VALUES (NULL, %s, %s, %s)
            """
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(insert_query, (file_id, cost, created_at))
            connection.commit()
            print(f"Inserted cost for file_id {file_id} with cost ${cost:.4f}.")

    except Error as e:
        print(f"Error inserting cost: {e}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def extract_dob_from_text(text, file_id):
    """
    Sends extracted text to GPT-4 to identify the DOB and calculates the cost of the request.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that extracts dates of birth from the provided text.",
        },
        {
            "role": "user",
            "content": f"Extract the date of birth or DOB or Date of birth or Dale de naissance Fechi de oicimiento from the following text:\n\n{text} in yyyy-mm-dd format only and do not send any other data along with the DOB.",
        },
    ]
    
    try:
        # Count the tokens for the messages
        tokens = count_tokens(messages, model="gpt-4o")
        cost = calculate_cost(tokens, model="gpt-4o")

        print(f"Tokens used: {tokens}")
        print(f"Estimated cost: ${cost:.4f}")

        # Insert the cost into the database
        insert_cost_to_db(file_id, cost)

        # Send request to OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
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
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE")
        )

        if connection.is_connected():
            print("Connected to the database")

            # Create a cursor object
            cursor = connection.cursor()

            # Define the query to read data from the ocr_logs table
            query = """
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
                    file_id = row[0]  # Assuming the first column is the file ID
                    dob = extract_dob_from_text(extracted_text, file_id)
                    
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
                    cursor.execute(update_query, (dob if dob else '', status, file_id))
                    connection.commit()
                    print(f"Updated record for doc_id {file_id}.")
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

# Uncomment these lines to run the main function
print("Starting connect_and_read_ocai...")
connect_and_read_ocai()
print("connect_and_read_ocai completed.")
