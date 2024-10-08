import os
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import pytesseract
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image, ExifTags
import requests

# Define the path to the .env file relative to the current file's location
env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from the .env file
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")

# Image URL to be downloaded and processed
image_url = "https://yhsverification.rugby/uploads/1725228038_img_2398.jpg"

# Initialize an empty list to store all the extracted text
all_text = []

# Function to download an image from a URL
def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the download failed

        # Save the image to a temporary file
        temp_file_path = Path("/tmp") / Path(url).name
        with open(temp_file_path, "wb") as f:
            f.write(response.content)
        
        return temp_file_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

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

# Download the image first
file_path = download_image(image_url)

if file_path:
    # Correct the image orientation
    corrected_image = correct_image_orientation(file_path)

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

    else:
        print("Error: Could not correct the image orientation.")
else:
    print("Error: Could not download the image.")
