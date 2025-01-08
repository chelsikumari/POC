import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import VideoLink
import AWSS3
from dotenv import load_dotenv 

load_dotenv()
 
 
os.environ["OPENAI_API_KEY"]
print("OPENAI_API_KEY set.")
 
interaction_history = []
 
 
def split_documents(bucket_name,folder_path_image):
    print("Splitting documents.")
    document=AWSS3.fetch_and_process_pdf(bucket_name,folder_path_image)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    print("###################", document)
    splits = text_splitter.split_documents(document)
    print(f"Documents split into {len(splits)} parts.")
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
    print("vectorstore created")
    return vectorstore.as_retriever()
 
 
def create_prompt():
    print("Creating prompt.")
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise. Stay updated with the calendar."
        "\n\n"
        "{context}"
    )
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
 
 
def create_chain(llm, prompt, retriever):
    print("Creating chain.")
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    print(f"Retrieval chain: {create_retrieval_chain(retriever, question_answer_chain)}")
    return create_retrieval_chain(retriever, question_answer_chain)
 
 
def generate_related_questions(question, llm):
    print(f"Generating related questions for: {question}")
    prompt = f"Based on the question '{question}', suggest three related questions a user might ask."
    response = llm.predict(prompt)
    return response.strip()
 
 
def get_answer(rag_chain, query_param):
    print(f"Getting answer for query: {query_param}")
    answer = {"input": query_param}
    results = rag_chain.invoke(answer)
    print(f"Answer obtained: {results}")
    return results
 
 
def set_input(query_param: str,filename:str):
    """
    Processes the query_param and returns an answer based on the PDF content.
    The query_param is used to retrieve relevant information and provide an answer.
    """
    print(f"Processing input: {query_param}")
    bucket_name = "skillup-dev-content"
    folder_path_image = f"abc/media_bytes/{filename}"
    retriever = split_documents(bucket_name,folder_path_image)
    prompt = create_prompt()
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    rag_chain = create_chain(llm, prompt, retriever)
 
    results = get_answer(rag_chain, query_param)
    print(f"Results obtained: {results}")
   
    # Process video links related to the query
    db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Harshi@06",
    "database": "skillupdb" 
    }

    video_links = VideoLink.videosLinks(query_param, db_config)
    print(f"Video links: {video_links}")
   
    # Format the video links
    video_links_text = "\n".join([f"- {link}" for link in video_links])
   
    # Combine the original answer with the video links
    full_answer = f"{results['answer']}\n\nRelated Video Links:\n{video_links_text}" if video_links else results['answer']
    related_questions = generate_related_questions(query_param, llm)
    full_answer += f"\n\n--- Related Questions ---\n{related_questions}"
    print(f"Full answer: {full_answer}")
   
    d = {"Answer": results, "Video_url": video_links, "Related_Questions": related_questions}
   
    return d
 
