import streamlit as st
import os
import base64
from email import policy
from email.parser import BytesParser
from langchain_ollama import ChatOllama
from langchain.schema import SystemMessage, HumanMessage
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Initialize model
llm = ChatOllama(model="mistral")

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Create Gmail service using OAuth
def get_gmail_service():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    return service

# Fetch most recent Gmail email
def fetch_latest_email():
    service = get_gmail_service()
    result = service.users().messages().list(userId='me', maxResults=1).execute()
    message_id = result['messages'][0]['id']
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

    headers = message['payload']['headers']
    subject = sender = date = "N/A"
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        elif header['name'] == 'From':
            sender = header['value']
        elif header['name'] == 'Date':
            date = header['value']

    # Decode plain text body
    body = "[No plain text body found]"
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break

    return subject, sender, date, body

# Function to parse .eml file
def extract_email_body(eml_file):
    msg = BytesParser(policy=policy.default).parse(eml_file)
    subject = msg['subject']
    sender = msg['from']
    date = msg['date']

    # Get plain text body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors='ignore')
                break
        else:
            body = "[No plain text body found]"
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore')

    return subject, sender, date, body

# LangChain wrapper to summarize
def summarize_email(email_text):
    messages = [
        SystemMessage(content="You are an assistant that summarizes email content."),
        HumanMessage(content=f"Summarize the following email:\n\n{email_text}")
    ]
    return llm(messages).content

# LangChain wrapper to suggest reply
def suggest_reply(subject, sender, email_text):
    messages = [
        SystemMessage(content=(
            "You are an AI assistant that writes professional, helpful, and polite email replies."
            " You respond as if you're the recipient of the following email."
            " Be clear, courteous, and directly address the content in the email."
        )),
        HumanMessage(content=(
            f"You received the following email from {sender} with the subject '{subject}':\n\n"
            f"{email_text}\n\n"
            "Please write a concise and professional reply in the same style."
        ))
    ]
    return llm(messages).content


# Streamlit UI
st.title("📧 Email Summarizer & Responder")

# --- Upload .eml section ---
st.subheader("📂 Upload an .eml Email File")
eml_file = st.file_uploader("Choose a .eml file", type=["eml"])

if eml_file is not None:
    subject, sender, date, email_text = extract_email_body(eml_file)

    st.subheader("📨 Email Metadata")
    st.write(f"**From:** {sender}")
    st.write(f"**Subject:** {subject}")
    st.write(f"**Date:** {date}")

    st.subheader("📄 Email Body")
    st.text_area("Email Content", email_text, height=300)

    if st.button("Summarize Email"):
        summary = summarize_email(email_text)
        st.success("✏️ Email Summary:")
        st.write(summary)

    if st.button("Suggest Reply"):
        reply = suggest_reply(subject, sender, email_text)
        st.success("📬 Suggested Reply:")
        st.write(reply)

# --- Gmail section ---
st.subheader("📥 Or Fetch Latest Gmail Email")

# Initialize session state
if "gmail_email_text" not in st.session_state:
    st.session_state["gmail_email_text"] = None
    st.session_state["gmail_subject"] = None
    st.session_state["gmail_sender"] = None
    st.session_state["gmail_date"] = None

if st.button("Fetch Email from Gmail"):
    subject, sender, date, email_text = fetch_latest_email()
    st.session_state["gmail_subject"] = subject
    st.session_state["gmail_sender"] = sender
    st.session_state["gmail_date"] = date
    st.session_state["gmail_email_text"] = email_text

if st.session_state["gmail_email_text"]:
    st.subheader("📨 Email Metadata")
    st.write(f"**From:** {st.session_state['gmail_sender']}")
    st.write(f"**Subject:** {st.session_state['gmail_subject']}")
    st.write(f"**Date:** {st.session_state['gmail_date']}")

    st.subheader("📄 Email Body")
    st.text_area("Email Content", st.session_state["gmail_email_text"], height=300)

    if st.button("Summarize Gmail Email"):
        summary = summarize_email(st.session_state["gmail_email_text"])
        st.success("✏️ Gmail Email Summary:")
        st.write(summary)

    if st.button("Suggest Gmail Reply"):
        reply = suggest_reply(
            st.session_state["gmail_subject"],
            st.session_state["gmail_sender"],
            st.session_state["gmail_email_text"]
        )
        st.success("📬 Suggested Gmail Reply:")
        st.write(reply)


