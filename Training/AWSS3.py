# import os
# import boto3
# from langchain.schema import Document
# from dotenv import load_dotenv 
# import io
# import pytesseract
# import boto3
# import fitz  # PyMuPDF
# from PIL import Image
# from langchain.schema import Document  
# import os

# # Set TESSDATA_PREFIX environment variable
# os.environ['TESSDATA_PREFIX'] = 'eng.trainedata'  # Adjust path based on your Tesseract installation



# load_dotenv()

# # Retrieve values from the environment
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# region_name = os.getenv('REGION_NAME')

# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     region_name=region_name
# )


# def fetch_and_process_pdf(bucket_name, file_key):
#     """
#     Fetch the PDF from S3 and extract both the raw text and image-based text.
#     """
#     # Download the file from S3
#     print(f"Fetching file: {file_key}")
#     temp_file_path = "/tmp/" + os.path.basename(file_key)
#     local_pdf_path = download_file_from_s3(bucket_name, file_key,temp_file_path)
#     print("local path downloaded",local_pdf_path)

#     if local_pdf_path is None:
#         raise Exception("Failed to download PDF from S3.")

#     # Extract text (text layer + OCR)
#     extracted_text = extract_text_from_pdf_with_ocr(local_pdf_path)

    
#     if not extracted_text.strip():
#         print("No text found in the PDF.")
#         return [], None

#     # Create LangChain documents
#     document = [Document(page_content=extracted_text, metadata={"source": file_key})]

#     # Clean up the temporary file
#     os.remove(local_pdf_path)
#     print(f"Temporary file {local_pdf_path} removed.")

#     return document

# def download_file_from_s3(bucket_name, file_key,temp_file_path):
#     """
#     Downloads a file from S3 and returns its local path.
#     """
#     try:
#         # Use a temporary file path
#         s3_client.download_file(bucket_name, file_key, temp_file_path)
#         print(f"File downloaded to: {temp_file_path}")
#         return temp_file_path
#     except Exception as e:
#         print(f"Error downloading file from S3: {e}")
#         return None
    
# def extract_text_from_pdf_with_ocr(pdf_path):
#     """
#     Extracts text from both the text layer and images within a PDF file.
#     """
#     try:
#         # Set the path to the Tesseract executable
#         pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
#         print("able to acces tessract")
        
#         doc = fitz.open(pdf_path)
#         print("able to generate document using fitz")
#         text = ""
#         # import pdb;pdb.set_trace()
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)

#             # Extract text from the text layer
#             text += page.get_text()

#             # Extract images and perform OCR
#             for img_index, img in enumerate(page.get_images(full=True)):
#                 xref = img[0]
#                 base_image = doc.extract_image(xref)
#                 image_bytes = base_image["image"]
#                 image = Image.open(io.BytesIO(image_bytes))
#                 pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#                 ocr_text = pytesseract.image_to_string(image)
#                 text += ocr_text

#         return text
#     except Exception as e:
#         print(f"Error extracting text with OCR: {e}")
#         return None


import os
import boto3
from langchain.schema import Document
from dotenv import load_dotenv
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Validate and fetch AWS credentials
aws_access_key_id = ''
aws_secret_access_key = ''
region_name = 'us-east-1'

# if not all([aws_access_key_id, aws_secret_access_key, region_name]):
#     raise EnvironmentError("AWS credentials or region are not set in the environment variables.")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

def fetch_and_process_pdf(bucket_name, file_key):
    """
    Fetch the PDF from S3 and extract text (text layer + OCR).
    Returns a list of LangChain `Document` objects.
    """
    print(f"Fetching file: {file_key} from bucket: {bucket_name}")
    temp_dir = "/tmp"
    os.makedirs(temp_dir, exist_ok=True)  # Ensure the temporary directory exists
    temp_file_path = os.path.join(temp_dir, os.path.basename(file_key))

    # Download the PDF from S3
    local_pdf_path = download_file_from_s3(bucket_name, file_key, temp_file_path)
    if not local_pdf_path:
        raise FileNotFoundError("Failed to download PDF from S3.")

    # Extract text from the PDF using multithreading
    extracted_text = extract_text_from_pdf_with_ocr(local_pdf_path)

    if not extracted_text.strip():
        print("No text found in the PDF.")
        return []

    # Create LangChain documents
    documents = [Document(page_content=extracted_text, metadata={"source": file_key})]

    # Clean up temporary file
    os.remove(local_pdf_path)
    print(f"Temporary file {local_pdf_path} removed.")

    return documents

def download_file_from_s3(bucket_name, file_key, temp_file_path):
    """
    Downloads a file from S3 and returns its local path.
    """
    try:
        s3_client.download_file(bucket_name, file_key, temp_file_path)
        print(f"File downloaded to: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        print(f"Error downloading file from S3: {e}")
        return None

def extract_text_from_pdf_with_ocr(pdf_path):
    """
    Extracts text from both the text layer and images in a PDF using multithreading.
    """
    try:
        # Set Tesseract executable path
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        text = ""
        with fitz.open(pdf_path) as doc:
            # Use a thread pool for parallel processing of pages
            with ThreadPoolExecutor() as executor:
                future_to_page = {
                    executor.submit(process_page, doc, page_num): page_num
                    for page_num in range(len(doc))
                }

                for future in as_completed(future_to_page):
                    page_text = future.result()
                    if page_text:
                        text += page_text

        return text
    except Exception as e:
        print(f"Error extracting text with OCR: {e}")
        return None

def process_page(doc, page_num):
    """
    Processes a single page to extract text and perform OCR on images.
    """
    try:
        page = doc.load_page(page_num)
        text = page.get_text()

        # Process images on the page
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))

            # Perform OCR on the image
            ocr_text = pytesseract.image_to_string(image)
            text += ocr_text

        return text
    except Exception as e:
        print(f"Error processing page {page_num}: {e}")
        return ""











