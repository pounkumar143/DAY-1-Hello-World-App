import streamlit as st
import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

# --- Load the API key from .env ---
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
except ImportError:
    Groq = None

# --- Excel logging utility ---
def log_conversation(username, question, answer, file_path="conversations.xlsx"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "User Name": username,
        "Timestamp": timestamp,
        "User Question": question,
        "AI Answer": answer
    }
    try:
        df = pd.read_excel(file_path)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([entry])
    df.to_excel(file_path, index=False)

# --- PDF export utility ---
def create_pdf(username, chat_history, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"{username}'s AI Friend Conversation", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.ln(5)
    for i, (q, a, t) in enumerate(chat_history, 1):
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 8, f"[{t}]\nQ{i}: {q}")
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, f"A{i}: {a}")
        pdf.ln(3)
    pdf.output(filename)

# --- Session State initialization ---
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR (always visible) ---
with st.sidebar:
    st.markdown("### AI Conversation")
    st.session_state.username = st.text_input("Your Name", value=st.session_state.username, placeholder="Enter your name")

# --- MAIN AREA dynamic content ---
if not st.session_state.username.strip():
    st.markdown("## Hello World Example")
    st.write("This app demonstrates:")
    st.markdown("""
- **Displaying text**
- **Markdown formatting**
- **Groq Llama 3 (8B) AI model integration**
""")
    st.code('print("Hello, Streamlit world")', language='python')
else:
    # Chat interface!
    st.markdown('# 🤖 Talk to your AI Friend')
    st.markdown("Ask your question below. Every conversation is logged and you can download your full chat as a PDF!")

    # Question input form
    with st.form(key="ask_ai_form"):
        user_question = st.text_area("What's your question?", key="question_input", placeholder="Type your question here…")
        submitted = st.form_submit_button("Ask AI")
    if submitted and user_question.strip():
        if not groq_api_key:
            st.error("GROQ_API_KEY not found. Please add it to your .env file.")
        elif not Groq:
            st.error("The 'groq' library is not installed. Please run: pip install groq")
        else:
            with st.spinner("Groq Llama 3 (8B) is thinking..."):
                try:
                    client = Groq(api_key=groq_api_key)
                    response = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "user", "content": user_question}],
                    )
                    ai_reply = response.choices[0].message.content
                except Exception as e:
                    ai_reply = f"Error: {e}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.chat_history.append((user_question, ai_reply, timestamp))
            log_conversation(st.session_state.username, user_question, ai_reply)

    # Show session history
    if st.session_state.chat_history:
        st.markdown("### Your Chat History")
        for idx, (q, a, t) in enumerate(st.session_state.chat_history, 1):
            with st.expander(f"[{t}] Q{idx}: {q}"):
                st.write(f"**AI Answer:** {a}")

        # Download as PDF
        import tempfile
        curr_dt = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        pdf_filename = f"{st.session_state.username}_chat_{curr_dt}.pdf"
        if st.button("Download Conversation as PDF"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_filename = tmp_file.name
            create_pdf(st.session_state.username, st.session_state.chat_history, tmp_filename)
            with open(tmp_filename, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )

# Optional: footer time
now = datetime.now().strftime("Current date: %A, %B %d, %Y, %I:%M %p")
st.markdown(f"<div style='text-align:right;color:grey;font-size:small;'>Current date: {now}</div>", unsafe_allow_html=True)
