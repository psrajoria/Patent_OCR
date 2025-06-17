import pandas as pd
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


# Function to extract text from a PDF file using OCR
def extract_text_from_pdf(pdf_path, dpi=300):
    pages = convert_from_path(pdf_path, dpi)
    text_data = ""
    for page in pages:
        text_data += pytesseract.image_to_string(page)
    return text_data


# Function to clean and structure the extracted text
def process_patent_text(text):
    # Normalize the text by removing extra spaces and line breaks
    normalized_text = re.sub(r"\s+", " ", text.strip())

    # Extract key fields using improved regex patterns
    patent_number = re.search(
        r"(?:Patent(?:ed)?|Des\.)\s*(\d{1,3},\d{3})", normalized_text
    )  # Match patterns like 155,564
    title = re.search(
        r"(?<=COMBINATION\s).*?(?=\sFiled)", normalized_text, re.IGNORECASE
    )  # Extract title before "Filed"
    applicant = re.search(
        r"(?:Be it known that I, )(.*?)(?=, a citizen)", normalized_text, re.IGNORECASE
    )  # Match applicant name
    application_date = re.search(
        r"Filed (.*?),", normalized_text, re.IGNORECASE
    )  # Match filed date
    patent_date = re.search(
        r"Patented (.*?)(?=\sUNITED|Des)", normalized_text, re.IGNORECASE
    )  # Match patented date
    claims = re.search(
        r"I claim:(.*?)(?=REFERENCES|$)", normalized_text, re.IGNORECASE
    )  # Match claims before "REFERENCES"
    references = re.search(
        r"REFERENCES CITED(.*?)$", normalized_text, re.IGNORECASE
    )  # Match references section

    # Create a dictionary of the structured data
    structured_data = {
        "Patent Number": patent_number.group(1) if patent_number else None,
        "Title": title.group(0).strip() if title else None,
        "Applicant": applicant.group(1).strip() if applicant else None,
        "Application Date": (
            application_date.group(1).strip() if application_date else None
        ),
        "Patent Date": patent_date.group(1).strip() if patent_date else None,
        "Claims": claims.group(1).strip() if claims else None,
        "References": references.group(1).strip() if references else None,
        "Description": text.strip(),  # Keep the full OCR text for reference
    }

    return structured_data


# Function to convert structured data to a DataFrame
def create_dataframe_from_patent(data):
    df = pd.DataFrame([data])
    return df


# Main function to handle the entire process
def process_patent_file(pdf_path):
    raw_text = extract_text_from_pdf(pdf_path)
    structured_data = process_patent_text(raw_text)
    df = create_dataframe_from_patent(structured_data)
    return df


# Path to the patent PDF file
pdf_file_path = "02488002.pdf"

# Process the file and display the DataFrame
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)
patent_df = process_patent_file(pdf_file_path)
print(patent_df)

# Save the DataFrame to a CSV file
patent_df.to_csv("patent_data_with_description_1.csv", index=False)
