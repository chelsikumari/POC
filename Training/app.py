from fastapi import FastAPI, UploadFile, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.pydantic_v1 import BaseModel
import PdfLoader
from io import BytesIO
from fastapi import FastAPI, UploadFile
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
import boto3
import boto3
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
s3_client = boto3.client(
        's3',
        aws_access_key_id='',
        aws_secret_access_key='',
        region_name='us-east-1'
    )
# S3 client and bucket details
# s3_client = boto3.client('s3')
BUCKET_NAME = "skillup-dev-content"
session_storage = {}

@app.post("/upload")
async def upload_file(file: UploadFile):
    folder_path = "abc/media_bytes/"
    FileName=file.filename
    try:
        print("hello")
        print(file.filename)
        # Read the file contents into memory
        file_content = await file.read()

        # Create a file-like object from the bytes
        file_stream = BytesIO(file_content)

        # Upload file to S3
        s3_client.upload_fileobj(file_stream, BUCKET_NAME, f"{folder_path}{file.filename}")
        
        return JSONResponse(
            content={"message": "File uploaded successfully", "session_id": FileName},
            status_code=200
        )
    except Exception as e:
        print(f"Error uploading file: {e}")
        return JSONResponse(
            content={"message": f"Failed to upload file: {e}"},
            status_code=500
        )

@app.get("/Response")
def read_root(
    session_id: str = Query(..., description="Session ID to retrieve file context"),
    query_param: str = Query(..., description="Additional query parameter to process")
):
    """
    Processes the query_param and reuses the uploaded file context based on session_id.
    """
    print("session_id",session_id)
    file_name=session_id
    # Pass the query_param to PdfLoader or any other function as needed
    print("file name setted in a session",file_name)
    response = PdfLoader.set_input(query_param,file_name)
    # response=PdfLoader.set_input(query_param)
    return {"response": response}

class Message(BaseModel):
    text: str
    


    