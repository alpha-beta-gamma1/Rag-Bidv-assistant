import streamlit as st
import sys
import os

# Add project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from src.rag_system import RAGSystem
except ModuleNotFoundError:
    st.error("Error: Could not find 'rag_system' module. Please ensure 'rag_system.py' is in the project directory (D:\\rag-project).")
    st.stop()

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

# Initialize RAGSystem
@st.cache_resource
def init_rag_system():
    try:
        return RAGSystem(config_path="config.yaml")  # Adjust config path as needed
    except Exception as e:
        st.error(f"Error initializing RAGSystem: {str(e)}")
        st.stop()

rag_system = init_rag_system()

# Streamlit app layout
st.title("RAG System Chat Interface")
st.write("Chat with the RAG system by entering your question below.")

# Display chat history
for i, chat in enumerate(st.session_state.chat_history):
    # Display user question
    with st.chat_message("user"):
        st.write(f"**You**: {chat['question']}")
    
    # Display system response and contexts
    with st.chat_message("assistant"):
        st.write(f"**RAG System**: {chat['response']}")
        if chat.get('contexts'):
            with st.expander("View Retrieved Contexts"):
                for j, context in enumerate(chat['contexts'], 1):
                    st.write(f"**Context {j}**: {context}")

# Input field for the query
question = st.text_input("Your Question:", 
                        placeholder="Type your question here...", 
                        key=f"question_{len(st.session_state.chat_history)}")

# Button to submit the query
if st.button("Send"):
    if question.strip():
        with st.spinner("Processing your query..."):
            try:
                # Query the RAG system
                result = rag_system.query(question)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "response": result["response"],
                    "contexts": result["contexts"]
                })
                
                # Clear the current input by rerunning the app
                st.session_state.current_question = ""
                st.rerun()
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
    else:
        st.warning("Please enter a question.")

# Display system stats
if st.button("Show System Stats"):
    try:
        stats = rag_system.get_system_stats()
        st.subheader("System Statistics")
        st.json(stats)
    except Exception as e:
        st.error(f"Error retrieving system stats: {str(e)}")