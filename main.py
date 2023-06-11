import streamlit as st
import os

from custom_agent import search_for_advice

# api
os.environ["OPENAI_API_KEY"] = st.secrets['apikey']

st.title("Chat with an A.I. Medical Advisor")
st.caption("**This is for informational purposes only, if needed please consult a medical professional.")

with st.sidebar:
    st.title('About')
    st.markdown('''
        The goal is to ask questions to  WebMD using natural language.
        - OpenAI's GPT API queries WebMD
        - LangChain connects to WebMD
        
        This is a Proof Of Concept (POC). 

     ''')
    st.title('Technology')
    st.markdown('''
        Developed by Jorge Duenas using:
        - [OpenAI GPT-3.5 API](https://openai.com/product)
        - [Streamlit.io](https://streamlit.io/)
        - [LangChain](https://python.langchain.com/en/latest/index.html)
        - [Python](https://www.python.org/)
        - [Anaconda](https://www.anaconda.com/)   
        - [Pycharm IDE](https://www.jetbrains.com/pycharm/) 
      ''')
user_input = st.text_input("What is medical question you wish to ask?")
if user_input:
    response =search_for_advice(user_input)
    st.write(response)



