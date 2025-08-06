from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import json
import os

# Load HuggingFace embedding model
HUGGINGFACE_EMBEDDING_MODEL = HuggingFaceEmbeddings()

# Path to the cleaned JSON file
JSON_FILE_PATH: str = "data/mah_bank_cleaned_loan_data.json"

# Ensure the cleaned JSON data file exists
if not os.path.exists(JSON_FILE_PATH):
    raise FileNotFoundError("Cleaned loan data file not found.")

# Load cleaned documents from JSON
with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
    cleaned_documents = json.load(file)

# Flatten the documents into strings: "url: content"
# Comment this line if your data is already in a different format
cleaned_documents = [
    f"{doc['page_url']}: {doc['data']}" for doc in cleaned_documents
]

# Split documents into chunks using recursive character splitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.create_documents(flattened_documents)

# Create FAISS vector index from documents
FAISS_DB = FAISS.from_documents(docs, HUGGINGFACE_EMBEDDING_MODEL)

# Save the FAISS index locally
FAISS_DB.save_local("data/faiss_index")
print(f"[+] FAISS index file saved successfully")
