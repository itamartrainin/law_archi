import pandas as pd
import pdfplumber
from tqdm import tqdm

def read_pdf(work_dir):
    with pdfplumber.open(work_dir) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                corrected_lines = [''.join(reversed(line)) for line in text.split('\n')]
                corrected_text = '\n'.join(corrected_lines)
                yield corrected_text

def pdf_to_txt(pdf_path):
    content = ''
    for page in read_pdf(pdf_path):
        content += '\n' + page
    return content

def pdf_to_pages(pdf_path):
    return pd.DataFrame([[i, page] for i, page in tqdm(enumerate(read_pdf(pdf_path)), desc='Converting pdf to pages')], columns=['page_num', 'content'])
