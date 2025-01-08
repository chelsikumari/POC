import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

def getDoc(query):
    # Folder containing all PDF files
    pdf_folder = "Pdf"
    documents = []
    
    # Iterate through all PDF files in the folder
    for file_name in os.listdir(pdf_folder):
        if file_name.endswith(".pdf"):  # Check if the file is a PDF
            pdf_path = os.path.join(pdf_folder, file_name)
            pdf_loader = PyPDFLoader(pdf_path)
            documents.extend(pdf_loader.load())  # Load and append documents
    
    # Split the documents into smaller chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    text_chunks = text_splitter.split_documents(documents)
    
    # Generate embeddings and create a vector store
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_documents(text_chunks, embeddings)
    
    # Perform a search on the extracted text
     # Replace with the actual query
    result = docsearch.similarity_search(query)
    
    return result
