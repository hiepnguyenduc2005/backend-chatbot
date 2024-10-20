import os
import json
import time
from dotenv import load_dotenv
import pdfplumber  
import openai
# from server.database_utils.retrieve_from_db import get_similarity_from_db
# from server.database_utils.update_database import update_database

from server.prompt import SYSTEM_ROLE, QUERY_WITH_HISTORY, SUMMARIZE_CHAT, SUMMARIZE_CONTEXT

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
CEBERAS_KEY = os.getenv("CEBERAS_KEY")
chat_history = []

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return text


def summarize_context(context):
    context_length = sum(len(context.split()) for context in context)
    if context_length > 300:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=API_KEY,
            # base_url="https://api.cerebras.ai/v1",
            # api_key=CEBERAS_KEY,
        )
        completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        # model="llama3.1-70b",
        messages=[
            {"role": "user", "content": SUMMARIZE_CONTEXT.format(context=context)}
        ])
        context = completion.choices[0].message.content
    return context

context_1 = summarize_context(extract_text_from_pdf("data/student_book.pdf"))
context_2 = summarize_context(extract_text_from_pdf("data/code_of_conduct.pdf"))

# context_1 = extract_text_from_pdf("data/student_book.pdf")
# context_2 = extract_text_from_pdf("data/code_of_conduct.pdf")

def generate_answer(user_message):
    #Chat history
    global chat_history, context_1, context_2
    
    #Get info from database as context
    # context, references = get_similarity_from_db(user_message)
    # reference_str = "".join(references)
    # reference_str = reference_str[:-2]
    
    #Calling GPT API to get answer
    client = openai.OpenAI(        
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
        # base_url="https://api.cerebras.ai/v1",
        # api_key=CEBERAS_KEY,
    )
    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        # model="llama3.1-70b",    
        messages=[
        {"role": "system", "content": SYSTEM_ROLE},
        {"role": "user", "content": QUERY_WITH_HISTORY.format(context_1=context_1, context_2=context_2,chat_history=chat_history,question=user_message)}
    ],
    stream=True
    )
    
    def stream_response():
        bot_mess = ""
        for chunk in completion:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                bot_mess += chunk_message
                yield(chunk_message)
            time.sleep(0.05)
        update_history(user_message,bot_mess)
    # bot_mess = completion.choices[0].message.content
    # ATTEMPT TO STREAM THE MESSAGE
    # stream_messages = []
    # bot_mess = ""
    # for idx,chunk in enumerate(completion):
    #     chunk_message = chunk.choices[0].delta.content
    #     if idx == 0:
    #         print(f"Bot: {chunk_message}",end='', flush=True)
    #     elif idx != 0 and chunk_message:
    #         print(chunk_message, end='', flush=True)
    #     stream_messages.append(chunk_message)
    # print(stream_messages)
    # for word in stream_messages:
    #     if word:
    #         bot_mess += word
    # print(bot_mess)
    return stream_response()

def update_history(user_message,bot_mess):
    #Chat history
    global chat_history
    chat_history.append({"role":"user","content":user_message}) 
    chat_history.append({"role":"bot","content":bot_mess})
    chat_history = summarize_chat_history(chat_history) # Summarize chat history if it is too long
    return
    

def summarize_chat_history(chat_history):
    history_length = sum(len(message["content"].split()) for message in chat_history)
    # print("chat_history before summarize: ", chat_history)

    if history_length > 300:
        
        #Formatting summary
        summary = ""
        for message in chat_history:
            role = message["role"].capitalize()
            content = message["content"]
            summary += f"{role}: {content}\n"
            
        #Calling GPT API
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=API_KEY,
            # base_url="https://api.cerebras.ai/v1",
            # api_key=CEBERAS_KEY,
        )
        completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct:free",
        # model="llama3.1-70b",        
        messages=[
            {"role": "user", "content": SUMMARIZE_CHAT.format(summary_prompt=summary)}
        ])
        summary = completion.choices[0].message.content
        
        #Processing summary
        summary_dict = json.loads(summary)
        chat_history = []
        if "user" in summary_dict:
            chat_history.append({"role": "user", "content": summary_dict["user"]})
        if "bot" in summary_dict:
            chat_history.append({"role": "bot", "content": summary_dict["bot"]})
        # print("new chat history: ",chat_history, "its type is: ", type(chat_history))
        
    return chat_history

def main():
    # update_database() #Update database if files are added
    while True:
        user_input = input("User: ")
        if user_input in ["q","quit","exit"]:
            print("Bot: End of Convo!")
            break
        bot_message, references = generate_answer(user_input)
        print(f"Bot: {bot_message}")
        print(f"\nReferences: {references}")
    
    
# if __name__ == "__main__" :
#     main()