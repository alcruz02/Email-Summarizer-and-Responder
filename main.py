import streamlit as st
import os
from email import policy
from email.parser import BytesParser
from langchain.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage

# Initialize model
llm = ChatOllama(model="mistral")


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
def suggest_reply(email_text):
    messages = [
        SystemMessage(content="You are an assistant that drafts professional email replies."),
        HumanMessage(content=f"Suggest a reply to this email:\n\n{email_text}")
    ]
    return llm(messages).content


# Streamlit UI
st.title("📧 EML Email Summarizer & Responder")

eml_file = st.file_uploader("Upload an .eml email file", type=["eml"])

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
        reply = suggest_reply(email_text)
        st.success("📬 Suggested Reply:")
        st.write(reply)
