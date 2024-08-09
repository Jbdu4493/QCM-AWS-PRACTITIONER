from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import pytesseract
from PIL import Image
import boto3
import os
import json
from botocore.exceptions import ClientError
import logging
from tempfile import NamedTemporaryFile
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class Question(BaseModel):
    question: str
    options: List[str]
    answer: str
    theme: Optional[str] = Field(default='')
    embedding: Optional[List[float]] = Field(default=None)
    img_path: Optional[str] = Field(default=None)

    @model_validator(mode='after')
    def correct_must_be_in_responses(self):
        if self.answer not in self.options:
            raise ValueError('The correct answer must be in the options list')
        return self


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Initialize ChatOpenAI
chat_model = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)


def extract_text_from_image(image_path: str) -> str:
    try:
        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        raise HTTPException(
            status_code=500, detail="Error extracting text from image")


def get_langchain_response(prompt: str) -> str:
    try:
        messages = [HumanMessage(content=prompt)]
        response = chat_model(messages)
        return response.content
    except Exception as e:
        logger.error(f"LangChain API error: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting response from LangChain")


def parse_question(text: str) -> Question:
    prompt = """
    I extract the data from this question:
    Question 4:

    Which of the following is an IAM best practice?

    O Create several IAM Users for one physical person

    © Don't use the root user account

    O Share your AWS account credentials with your colleague, so (s)he can perform a task for you

    O Do not enable MFA for easier access

    And I return only the data in JSON format in this form:
    #######
    {
        "question": "Which of the following is an IAM best practice?",
        "options": [
            "Create several IAM Users for one physical person",
            "Don't use the root user account",
            "Share your AWS account credentials with your colleague, so (s)he can perform a task for you",
            "Do not enable MFA for easier access"
        ],
        "answer": "Don't use the root user account"
    }
    other exemple:
    Question 2:

    You have enabled versioning in your S3 bucket which already contains a lot of files. Which version will the
    existing files have?

    O 1

    O 0

    O -1

    © null
    #######
    '{"question":"You have enabled versioning in your S3 bucket which already contains a lot of files. Which version will the existing files have?","options":["1","0","-1","null"],"answer":"null"}'

    In some questions, it is asked to find the "incorrect" answer or "Except" and the data should be put in the "answer" field
    answer is a str not a list
    Be careful that the "answer" must be in list "options"
    Correct any typos while respecting the previous constraints
    Remove unnecessary line breaks
    please base only on the text in order avoid halucination

    Respond without an introductory phrase like "Here is the JSON data corresponding to the question"
    """
    try:
        response = get_langchain_response(prompt)
        question_data = json.loads(response)
        question = Question(**question_data)
        return question
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        raise HTTPException(
            status_code=500, detail="Error parsing LangChain response")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/get-question-json-s3")
async def get_question_json_s3(bucket: str, file_name: str):
    try:
        with NamedTemporaryFile(delete=False) as temp_file:
            s3.download_fileobj(bucket, file_name, temp_file)
            temp_file_path = temp_file.name

        text = extract_text_from_image(temp_file_path)
        question = parse_question(text)
        question.img_path = f"s3://{bucket}/{file_name}"
        question.theme = file_name.split('/')[-2]
        return question
    except ClientError as e:
        logger.error(f"S3 error: {e}")
        raise HTTPException(status_code=500, detail="Error accessing S3 file")
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)


@app.get("/get-question-json-base64")
async def get_question_json_base64(base64_data: str):
    try:
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(base64.b64decode(base64_data))
            temp_file_path = temp_file.name

        text = extract_text_from_image(temp_file_path)
        question = parse_question(text)
        return question
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)


@app.get("/get-question-json-file")
async def get_question_json_file(file: UploadFile = File(...)):
    try:
        with NamedTemporaryFile(delete=False) as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

        text = extract_text_from_image(temp_file_path)
        question = parse_question(text)
        return question
    finally:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)


@app.get("/")
async def root():
    return {"message": "Welcome to the QCM API!"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
