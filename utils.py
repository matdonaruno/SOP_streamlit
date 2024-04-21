import pdfplumber
from pdf2image import convert_from_path
import re
import streamlit as st

def extract_text(file, file_type):
    text = ""
    if file_type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ''
    else:
        text = file.getvalue().decode("utf-8")
    return text

def display_pdf_as_images(pdf_file_path, subtitle):
    images = convert_from_path(pdf_file_path)
    for i, image in enumerate(images, start=1):
        with st.expander(f"{subtitle} page {i}", expanded=False):  # Sub Title with page number
            st.image(image, width=800)  # Display with specified width

def extract_revision_history(text):
    #pattern = r'[\*]*\s*\d{4}年\s*\d{1,2}月\s*(改訂|作成).*'
    pattern = r'[\*]*\s*\d{4}年\s*\d{1,2}月\s*改訂.*?）'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None