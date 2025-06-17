import os
import re
import csv
from pdf2image import convert_from_path
from pytesseract import image_to_string
from concurrent.futures import (
    ThreadPoolExecutor,
)  # Using ThreadPoolExecutor instead of ProcessPoolExecutor

# Precompiled regex patterns for efficiency
REGEX_PATTERNS = {
    "Patent Number": re.compile(
        r"(?:Plant Pat\.|Des\.|Patent(?:ed)?|Patent Number)\s*(\d{1,3}[,\.]?\d{3})"
    ),
    "Title": re.compile(
        r"(\d{1,6}\s)([A-Z][A-Z0-9 ,.\-]+)(?=\sFiled|\sPatented|\sApplication)",
        re.IGNORECASE,
    ),
    "Applicant": re.compile(
        r"(?:Be it known that I, )(.*?)(?=, a citizen| of the)", re.IGNORECASE
    ),
    "Application Date": re.compile(r"Filed (.*?),", re.IGNORECASE),
    "Patent Date": re.compile(r"Patented (.*?)(?=\sUNITED|\sDes|\n)", re.IGNORECASE),
    # "References": re.compile(r'(REFERENCES CITED|no reference cited)(.*?)(?=Claims|Description|$)', re.IGNORECASE),
    # "Claims": re.compile(r'I claim[:\s]*(.*?)(?=REFERENCES|Description|$)', re.IGNORECASE),
}


# Function to extract text from scanned PDFs using OCR
def extract_text_from_pdf(file_path, dpi=600):
    text_data = []
    for page in convert_from_path(file_path, dpi=dpi):
        text_data.append(image_to_string(page))
    return " ".join(text_data)


# Process patent text and structure it into fields
def process_patent_text(text, file_prefix):
    normalized_text = re.sub(r"\s+", " ", text.strip())

    structured_data = {
        "Patent Number": "Not Found",
        "Title": "Not Found",
        "Applicant": "Not Found",
        "Application Date": "Not Found",
        "Patent Date": "Not Found",
        # "References": "Not Found",
        # "Claims": "Not Found",
        # "Description": text.strip()
    }

    # Apply regex patterns based on the file prefix
    if file_prefix == "D0":
        # structured_data["Patent Number"] = re.search(r"(Des\.?\s?\d+)", normalized_text).group(1) if re.search(r"(Des\.?\s?\d+)", normalized_text) else "Not Found"
        structured_data["Patent Number"] = (
            re.search(r"(Des\.?\s?\d{1,3}(?:,\d{3})*)", normalized_text).group(1)
            if re.search(r"(Des\.?\s?\d{1,3}(?:,\d{3})*)", normalized_text)
            else "Not Found"
        )
        # structured_data["Title"] = re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text).group(1) if re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text) else "Not Found"
        structured_data["Title"] = (
            re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            ).group(1)
            if re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            )
            else "Not Found"
        )

        # structured_data["Patent Date"] = re.search(r"Patented\s(.*?)\sUNITED", normalized_text).group(1) if re.search(r"Patented\s(.*?)\sUNITED", normalized_text) else "Not Found"
        structured_data["Patent Date"] = (
            re.search(
                r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text
            ).group(1)
            if re.search(r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text)
            else "Not Found"
        )

        # structured_data["Applicant"] = re.search(r"Be it known that I, (.*?) of", normalized_text).group(1) if re.search(r"Be it known that I, (.*?) of", normalized_text) else "Not Found"
        structured_data["Applicant"] = (
            re.search(r"(\b[A-Z][A-Z. ]+)", normalized_text).group(1)
            if re.search(r"(\b[A-Z][A-Z. ]+)", normalized_text)
            else "Not Found"
        )

        # structured_data["Application Date"] = re.search(r"Filed (.*?),", normalized_text).group(1) if re.search(r"Filed (.*?),", normalized_text) else "Not Found"
        structured_data["Application Date"] = (
            re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            ).group(1)
            if re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            )
            else "Not Found"
        )

    elif file_prefix == "02":
        # Similar structure as 'D0' but adjusted for "02" prefix logic
        # structured_data["Patent Number"] = re.search(r"(Patent\sNumber\s\d+)", normalized_text).group(1) if re.search(r"(Patent\sNumber\s\d+)", normalized_text) else "Not Found"
        # structured_data["Patent Number"] = re.search(r"UNITED\sSTATES\sPATENT\sOFFICE.*?(Patent\sNumber\s\d{1,3}(?:,\d{3})*)", normalized_text).group(1) if re.search(r"UNITED\sSTATES\sPATENT\sOFFICE.*?(Patent\sNumber\s\d{1,3}(?:,\d{3})*)", normalized_text) else "Not Found"
        structured_data["Patent Number"] = (
            re.search(
                r"UNITED\sSTATES\sPATENT\sOFFICE\s+(\d{1,3}(?:,\d{3})*)",
                normalized_text,
            ).group(1)
            if re.search(
                r"UNITED\sSTATES\sPATENT\sOFFICE\s+(\d{1,3}(?:,\d{3})*)",
                normalized_text,
            )
            else "Not Found"
        )

        # structured_data["Patent Date"] = re.search(r"Patented\s(.*?)\sUNITED", normalized_text).group(1) if re.search(r"Patented\s(.*?)\sUNITED", normalized_text) else "Not Found"
        # structured_data["Title"] = re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text).group(1) if re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text) else "Not Found"
        structured_data["Title"] = (
            re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            ).group(1)
            if re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            )
            else "Not Found"
        )

        structured_data["Patent Date"] = (
            re.search(
                r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text
            ).group(1)
            if re.search(r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text)
            else "Not Found"
        )
        structured_data["Application Date"] = (
            re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            ).group(1)
            if re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            )
            else "Not Found"
        )

    elif file_prefix == "PP":
        # Plant patents start with "Plant Pat."
        structured_data["Patent Number"] = (
            re.search(r"(Plant Pat\.\s\d+)", normalized_text).group(1)
            if re.search(r"(Plant Pat\.\s\d+)", normalized_text)
            else "Not Found"
        )
        # structured_data["Patent Date"] = re.search(r"Patented\s(.*?)\sUNITED", normalized_text).group(1) if re.search(r"Patented\s(.*?)\sUNITED", normalized_text) else "Not Found"
        structured_data["Patent Date"] = (
            re.search(
                r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text
            ).group(1)
            if re.search(r"Patented\s([A-Z][a-z]+\.\s\d{1,2},\s\d{4})", normalized_text)
            else "Not Found"
        )
        # structured_data["Title"] = re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text).group(1) if re.search(r'UNITED STATES PATENT OFFICE\s+\d+[\s\n]+([A-Z0-9 ,.\-]+)', normalized_text) else "Not Found"
        structured_data["Title"] = (
            re.search(
                r"UNITED STATES PATENT OFFICE\s*\n\s*\d+[,\d]*\s*\n\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            ).group(1)
            if re.search(
                r"UNITED STATES PATENT OFFICE\s*\n\s*\d+[,\d]*\s*\n\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            )
            else "Not Found"
        )

        # structured_data["Title"] = re.search(r'^\d+\s+([A-Z0-9 ,.\-]+)', normalized_text).group(1) if re.search(r'^\d+\s+([A-Z0-9 ,.\-]+)', normalized_text) else "Not Found"
        # structured_data["Applicant"] = re.search(r'([A-Za-z .]+), [A-Za-z]+, [A-Za-z]+, assignor to .+?,', normalized_text).group(1) if re.search(r'([A-Za-z .]+), [A-Za-z]+, [A-Za-z]+, assignor to .+?,', normalized_text) else "Not Found"
        # structured_data["Application Date"] = re.search(r'Application\s+(\w+\s+\d{1,2},\s+\d{4})', normalized_text).group(1) if re.search(r'Application\s+(\w+\s+\d{1,2},\s+\d{4})', normalized_text) else "Not Found"
        structured_data["Application Date"] = (
            re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            ).group(1)
            if re.search(
                r"Application\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text
            )
            else "Not Found"
        )

    elif file_prefix == "RE":
        # Reissued patents start with "Re."
        # structured_data["Patent Number"] = re.search(r"(Re\.\s\d+)", normalized_text).group(1) if re.search(r"(Re\.\s\d+)", normalized_text) else "Not Found"
        structured_data["Patent Number"] = (
            re.search(r"(Re\.?\s?\d{1,3}(?:,\d{3})*)", normalized_text).group(1)
            if re.search(r"(Re\.?\s?\d{1,3}(?:,\d{3})*)", normalized_text)
            else "Not Found"
        )
        # structured_data["Title"] = re.search(r'UNITED STATES PATENT OFFICE\s*\d+[,\d]*\s*([\w ,.\-]+)', normalized_text).group(1) if re.search(r'UNITED STATES PATENT OFFICE\s*\d+[,\d]*\s*([\w ,.\-]+)', normalized_text) else "Not Found"
        structured_data["Title"] = (
            re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            ).group(1)
            if re.search(
                r"UNITED STATES PATENT OFFICE\s*\n+\s*\d+[,\d]*\s*\n+\s*([A-Z0-9 ,.\-]+)",
                normalized_text,
            )
            else "Not Found"
        )

        # structured_data["Patent Date"] = re.search(r"Reissued\s(.*?)\sApplication", normalized_text).group(1) if re.search(r"Reissued\s(.*?)\sApplication", normalized_text) else "Not Found"
        structured_data["Patent Date"] = (
            re.search(
                r"Reissued\s([A-Z][a-z]+[.,]\s\d{1,2},\s\d{4})", normalized_text
            ).group(1)
            if re.search(
                r"Reissued\s([A-Z][a-z]+[.,]\s\d{1,2},\s\d{4})", normalized_text
            )
            else "Not Found"
        )
        structured_data["Application Date"] = (
            re.search(
                r"Application for re[-\s]?issue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                normalized_text,
                re.IGNORECASE,
            ).group(1)
            if re.search(
                r"Application for re[-\s]?issue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
                normalized_text,
                re.IGNORECASE,
            )
            else "Not Found"
        )

        # structured_data["Application Date"] = re.search(r"Application for reissue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text).group(1) if re.search(r"Application for reissue\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", normalized_text) else "Not Found"

    # Apply common patterns for references and claims
    # structured_data["References"] = re.search(REGEX_PATTERNS["References"], normalized_text).group(1) if re.search(REGEX_PATTERNS["References"], normalized_text) else "Not Found"
    # structured_data["Claims"] = re.search(REGEX_PATTERNS["Claims"], normalized_text).group(1) if re.search(REGEX_PATTERNS["Claims"], normalized_text) else "Not Found"

    return structured_data


# Process a single PDF and return structured data
def process_single_pdf(file_path, file_prefix):
    try:
        raw_text = extract_text_from_pdf(file_path)
        structured_data = process_patent_text(raw_text, file_prefix)
        return file_path, structured_data
    except Exception as e:
        return file_path, {"Error": str(e)}


# Select PDF files based on their prefixes
def select_pdfs_with_prefixes(directory, prefixes):
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".pdf") and any(
                file.startswith(prefix) for prefix in prefixes
            ):
                file_paths.append(os.path.join(root, file))
    return file_paths


# Save extracted data into CSV
def save_to_csv(output_csv, data):
    csv_headers = [
        "File Path",
        "Patent Number",
        "Title",
        "Applicant",
        "Application Date",
        "Patent Date",
        # "References", "Claims", "Description"
    ]
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
        writer.writeheader()
        for file, structured_data in data.items():
            if "Error" in structured_data:
                # row = {"File Path": file, "Patent Number": "Error", "Title": "Error", "Applicant": "Error",
                #        "Application Date": "Error", "Patent Date": "Error", "References": "Error",
                #        "Claims": "Error", "Description": structured_data["Error"]}

                row = {
                    "File Path": file,
                    "Patent Number": "Error",
                    "Title": "Error",
                    "Applicant": "Error",
                    "Application Date": "Error",
                    "Patent Date": "Error",
                }
            else:
                row = {"File Path": file, **structured_data}
            writer.writerow(row)


# Directory and file prefix setup
directory = "data"
prefixes = ["02", "D0", "PP", "RE"]

# Collect matching PDF file paths
pdf_files = select_pdfs_with_prefixes(directory, prefixes)

# Use threading for faster OCR and processing (ThreadPoolExecutor works better in Jupyter)
print(f"Processing {len(pdf_files)} files...")

# Process files concurrently using ThreadPoolExecutor
results = {}
with ThreadPoolExecutor() as executor:
    futures = []
    for file_path in pdf_files:
        file_prefix = file_path.split(os.path.sep)[-1][
            :2
        ]  # Extract prefix from filename
        futures.append(executor.submit(process_single_pdf, file_path, file_prefix))

    for future in futures:
        file_path, structured_data = future.result()
        results[file_path] = structured_data


# Save results to CSV
output_csv = "optimized_patent_data.csv"
save_to_csv(output_csv, results)
print(f"Data saved to {output_csv}!")
