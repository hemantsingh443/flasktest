import itertools
import os
import arxiv
from tempfile import TemporaryDirectory
import requests
from flask import Flask, Response, jsonify, render_template, request
from tempfile import TemporaryDirectory
from pdfminer.high_level import extract_text
import torch
from transformers import BartTokenizer, BartForConditionalGeneration
import io
from pdfminer.pdfparser import PDFParser  # Import the io module
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import os
import urllib

current_directory = os.getcwd()
print("Current working directory:", current_directory)

if torch.cuda.is_available():
    print("CUDA is available! GPU will be used.")
else:
    print("CUDA is not available. CPU will be used.")


def extract_pdf_text(pdf_content):
    with io.BytesIO(pdf_content) as file:
        parser = PDFParser(file)
        doc = PDFDocument(parser)
        # Create an in-memory buffer for the text
        text_buffer = io.StringIO()
        # Extract the text to the buffer
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, text_buffer, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
        pdf_text = text_buffer.getvalue()
        # Get the text from the buffer
        return pdf_text


# Model Setup
model_name = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


def download_pdf(pdf_url):
    with TemporaryDirectory() as temp_dir:
        response = requests.get(pdf_url)
        if not response.ok:
            raise requests.exceptions.HTTPError(f"PDF download failed: {response.status_code}")
        temp_pdf_path = os.path.join(temp_dir, 'temp.pdf')
        with open(temp_pdf_path, 'wb') as pdf_file:
            pdf_file.write(response.content)
        return response.content


# Summarization Logic
def iterative_summarization(pdf_text, chunk_size=1000, output_file="summary.txt", reset_method="reload"):
    output_path = os.path.join('C:/anotherTry', output_file)
    with open(output_path, "w", encoding='utf-8') as f:
        summary = ""  # Accumulate summaries in a string
        start_index = 0
        while start_index < len(pdf_text):
            end_index = start_index + chunk_size
            chunk = pdf_text[start_index:end_index]
            if reset_method == "reload":
                # Option 1: Full Model Reload
                model = BartForConditionalGeneration.from_pretrained(model_name)
                model.to(device)
            elif reset_method == "hidden_state":
                # Option 2: Resetting Hidden States (implementation may vary)
                model.reset_hidden_states()
                # You might need to adjust how states are reset
            else:
                raise ValueError("Invalid reset_method. Choose 'reload' or 'hidden_state'")
            chunk_summary = summarize_chunk(chunk)
            summary += chunk_summary + "\n"  # Add chunk summary to the string
            start_index = end_index
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(summary)


# Character-Aware Summarization Logic
def summarize_chunk(text, max_length=200):
    inputs = tokenizer(text, return_tensors="pt").to(device)  # Move inputs to GPU
    model.to(device)  # Ensure model is on GPU
    output = model.generate(**inputs, max_length=max_length, min_length=50)
    return tokenizer.decode(output[0], skip_special_tokens=True)


def generate_pdf_summary(pdf_url):
    try:
        pdf_content = download_pdf(pdf_url)  # Get PDF content as bytes
        pdf_text = extract_pdf_text(pdf_content)  # Pass content to extractor
        iterative_summarization(pdf_text)
        with open("summary.txt", "r") as f:
            summary = f.read()
        return jsonify(summary=summary)
    except requests.exceptions.RequestException as e:
        return jsonify(error=f"Error downloading PDF: {str(e)}"), 500
    except FileNotFoundError:
        return jsonify(error="Error: Downloaded PDF not found."), 500
    except Exception as e:
        return jsonify(error=f"Error generating summary: {str(e)}"), 500


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_query = request.form["query"]
        page = 1  # Start from the first page on new search
    else:
        search_query = request.args.get('query')
        page = request.args.get('page', 1, type=int)

    results_per_page = 10
    if search_query:
        search = arxiv.Search(query=search_query, max_results=100)
        results = list(search.results())  # Convert generator to a list
        total_results = len(results)
        total_pages = (total_results // results_per_page) + (total_results % results_per_page > 0)
        start_index = (page - 1) * results_per_page
        end_index = min(start_index + results_per_page, total_results)
        papers = [
            {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'abstract': paper.summary,
                'pdf_url': paper.pdf_url,
                'arxiv_url': paper.entry_id,
                # ... add other paper details as needed ...
            } for paper in results[start_index:end_index]
        ]
    else:
        papers = []
        total_pages = 0

    # Generate pagination links
    pagination_links = []
    for page_num in range(1, total_pages + 1):
        active_class = "active" if page_num == page else ""
        pagination_links.append(f'{page_num}')

    return render_template(
        "combined.html",
        papers=papers,
        pagination_links=pagination_links,
        query=search_query
    )


def generate_pagination_link(page_num, query):
    base_url =base_url = 'http://127.0.0.1:5000/search'   # Replace with your actual base URL
    params = {'query': query, 'page': page_num}
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def search_arxiv_by_author(author_name):
    search_query = f'au:"{author_name}"'  # Using arXiv API syntax
    search = arxiv.Search(query=search_query)
    results = search.results()
    # Format results for display - This is your existing formatting logic
    formatted_papers = []
    for paper in results:
        paper_data = {
            'title': paper.title,
            'abstract': paper.summary,
            'authors': [author.name for author in paper.authors],
            'pdf_url': paper.pdf_url,
            'arxiv_url': paper.entry_id,
            'pdf_summary': '',
            'pdf_summary_status': 'Not Started'
        }
        formatted_papers.append(paper_data)
    return formatted_papers


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    pdf_url = data.get('pdf_url')
    if not pdf_url:
        return jsonify({'error': 'Missing pdf_url in request data'}), 

@app.route("/summarize_pdf", methods=["POST"])
def summarize_pdf():
    pdf_url = request.json.get('pdf_url')  # Get from JSON data
    print("Received pdf_url:", pdf_url)
    if not pdf_url:
        return jsonify(error="Please provide a PDF URL."), 400
    try:
        summary = generate_pdf_summary(pdf_url)
        return jsonify(summary=summary)
    except Exception as e:
        return jsonify(error=f"Error generating summary: {str(e)}"), 500


@app.route('/get_summary')
def get_summary():
    try:
        with open("summary.txt", "r", encoding='utf-8') as f:
            summary_text = f.read()
        return jsonify(summary=summary_text)
    except FileNotFoundError:
        return jsonify(error="Summary file not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
