import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import pytesseract
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

api_key = os.getenv("OPENAI_API_KEY")

# Print environment variables for debugging
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_USERNAME: {os.getenv('DB_USERNAME')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_DATABASE: {os.getenv('DB_DATABASE')}")
print(f"APP_URL: {os.getenv('APP_URL')}")  # Print APP_URL to ensure it's loaded
print(f"FILE_DIRECTORY: {os.getenv('FILE_DIRECTORY')}")  # Print FILE_DIRECTORY to ensure it's loaded

# Initialize an empty list to store all the extracted text
all_text = []

# Function to correct image orientation using Pillow
def correct_image_orientation(image_path):
    try:
        image = Image.open(image_path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = image._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)

            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)

        return image

    except Exception as e:
        print(f"Error correcting image orientation: {e}")
        return None
    

import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

def extract_text_from_image(corrected_image, file_path, doc_id):
    if corrected_image:
        # Save the corrected image to a temporary file
        temp_file_path = file_path.with_name("corrected_" + file_path.name)
        corrected_image.save(temp_file_path)

        # Use the doctr library primarily
        # Create an OCR predictor
        predictor = ocr_predictor(pretrained=True)

        # Load the corrected image
        image = DocumentFile.from_images(str(temp_file_path))

        # Perform OCR on the image
        result = predictor(image)

        # Variables to track the number of words detected
        total_detected_words = 0
        all_text = []  # Initialize list to collect extracted text

        # Iterate through the pages and collect text from blocks
        for page in result.pages:
            for block in page.blocks:
                # Collect text from lines within each block
                for line in block.lines:
                    # Join the text from each word in the line and append it to the list
                    line_text = " ".join([word.value for word in line.words])
                    all_text.append(line_text)

                    # Increment the detected word count
                    total_detected_words += len(line.words)

        # Join all collected lines into a single string
        extracted_text = "\n".join(all_text)

        # Print the entire extracted text
        print(extracted_text)

        # Optionally, remove the temporary file after processing
        os.remove(temp_file_path)

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

                # Define the query to read data from the ocr_logs table using the given doc_id
                select_query = """
                SELECT * FROM `ocr_logs` WHERE doc_id = %s
                """
                cursor.execute(select_query, (doc_id))

                # Fetch the row matching the doc_id
                row = cursor.fetchone()

                # If the data is found, update the response_data with the extracted text
                if row:
                    update_query = """
                    UPDATE `ocr_logs` 
                    SET `response_data` = %s 
                    WHERE `doc_id` = %s
                    """
                    cursor.execute(update_query, (extracted_text, doc_id))
                    connection.commit()
                    print(f"Updated response_data for doc_id {doc_id}.")
                else:
                    print(f"No data found for doc_id {doc_id}.")

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

    else:
        print("Error: Could not correct the image orientation.")



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

            # Define the query to read data from the ocr_logs table
            query = """
            SELECT * FROM `ocr_logs` WHERE `file_type`!='application/pdf' AND `read_status`='pending' ORDER BY `doc_id` ASC
            """

            # Execute the query
            cursor.execute(query)

            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            # Iterate through the fetched rows
            for row in rows:
                # Use proper string formatting to print the file path
                print(f"File path: {row[6]}")

                # Image URL to be downloaded and processed
                file_path = row[7]

                # Correct the image orientation
                corrected_image = correct_image_orientation(file_path)

            # Commit the transaction if necessary (typically for updates, not for selects)
            connection.commit()

            extract_text_from_image(corrected_image, file_path, 2)
    
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

# Run the function
connect_and_read()
