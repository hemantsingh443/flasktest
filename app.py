
import os
import arxiv
from tempfile import TemporaryDirectory
from flask_login import current_user, login_required, login_user, logout_user
import requests
from flask import Flask, Response, jsonify, redirect, render_template, request, url_for
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
import db 
from flask_caching import Cache  
from flask_login import LoginManager  
from db import get_user_by_username, get_user_by_id, add_user, get_papers_by_ids, User, create_tables  
from functools import wraps

# Create a cache instance
cache = Cache(config={'CACHE_TYPE': 'simple'}) 

app = Flask(__name__) 
cache.init_app(app)
app.secret_key = '12345678'  # Replace with a strong secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

create_tables()  # Create database tables

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)  # Replace with a strong, random key



current_directory = os.getcwd()
print("Current working directory:", current_directory)

if torch.cuda.is_available():
    print("CUDA is available! GPU will be used.")
else:
    print("CUDA is not available. CPU will be used.") 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


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
            print(f"Chunk Summary: {chunk_summary}\n")  
            yield chunk_summary + "\n"
            summary += chunk_summary + "\n"  # Add chunk summary to the string
            start_index = end_index
    


# Character-Aware Summarization Logic
def summarize_chunk(text, max_length=200):
    inputs = tokenizer(text, return_tensors="pt").to(device)  # Move inputs to GPU
    model.to(device)  # Ensure model is on GPU
    output = model.generate(**inputs, max_length=max_length, min_length=50)
    return tokenizer.decode(output[0], skip_special_tokens=True)


def generate_pdf_summary(pdf_url):
        pdf_content = download_pdf(pdf_url)
        pdf_text = extract_pdf_text(pdf_content)
        def generate_chunks():
            for chunk_summary in iterative_summarization(pdf_text):
                yield chunk_summary + "\n"
        return Response(generate_chunks(), mimetype='text/plain')
  


@app.route("/", methods=["GET", "POST"]) 
@login_required 
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
                "is_favorite": paper.entry_id in current_user.get_favorite_paper_ids(),
            } for paper in results[start_index:end_index]
        ]
    else:
        papers = []
        total_pages = 0

    # Generate pagination links
    pagination_links = []
    for page_num in range(1, total_pages + 1):
        url = url_for('search', query=search_query, page=page_num) 
        pagination_links.append({'page_num': page_num, 'url': url})

    return render_template(
        "combined.html",
        papers=papers,
        pagination_links=pagination_links,  
        query=search_query,
        current_user=current_user # Make sure you're passing the query
    ) 




def generate_pagination_link(page_num, query):
    base_url = url_for('search')  # Use url_for to get the correct endpoint
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
        return jsonify({'error': 'Missing pdf_url in request data'}), 400
    try:
        with TemporaryDirectory() as temp_dir:
            response = requests.get(pdf_url)
            temp_pdf_path = os.path.join(temp_dir, 'temp.pdf')
            with open(temp_pdf_path, 'wb') as pdf_file:  
                pdf_file.write(response.content)
            filename = 'downloaded_paper.pdf'
            response = Response(open(temp_pdf_path, 'rb').read(), mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename={filename}' 
            return response
    except Exception as e:

        return jsonify({'error': str(e)}), 500 

@app.route("/summarize_pdf", methods=["POST"])
def summarize_pdf():
    pdf_url = request.json.get('pdf_url')  # Get from JSON data
    print("Received pdf_url:", pdf_url)
    if not pdf_url:
        return jsonify(error="Please provide a PDF URL."), 400
    try:
        return generate_pdf_summary(pdf_url)  # Return Response directly
    except Exception as e:
        return jsonify(error=f"Error generating summary: {str(e)}"), 500



@app.route("/author/<author_name>")
def author_search(author_name):
    papers = search_arxiv_by_author(author_name)
    return render_template("combined.html", papers=papers, query=f'au:"{author_name}"')   


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.get_user_by_username(username)
        if user and user.password == password:  # In a real app, you would hash and compare passwords
            login_user(user)
            return redirect(url_for('search'))  # Redirect to the main page after login
        else:
            # Handle invalid login
            pass
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # ... (add validation for username and password)
        db.add_user(username, password)
        return redirect(url_for('login'))  # Redirect to login after signup
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 

@app.route('/favorites')
@login_required
def favorites():
    favorite_paper_ids = current_user.get_favorite_paper_ids()
    favorite_papers = get_papers_by_ids(favorite_paper_ids)  # Get full paper details
    return render_template('favorites.html', papers=favorite_papers)

@app.route('/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    paper_id = request.json.get('paper_id') 
    if not paper_id:
        return jsonify(message='Missing paper_id'), 400  
    current_user.add_favorite(paper_id) 
    return jsonify(message='Paper added to favorites')

@app.route('/remove_favorite', methods=['POST'])
@login_required
def remove_favorite():
    paper_id = request.json.get('paper_id') 
    if not paper_id:
        return jsonify(message='Missing paper_id'), 400

    try:
        current_user.remove_favorite(paper_id)
        
        # Invalidate cache for favorites list (if using caching)
        cache.delete_memoized(current_user.get_favorite_paper_ids)  
        
        return jsonify(message='Paper removed from favorites')
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error removing favorite: {e}")
        return jsonify(message='An error occurred while removing the favorite.'), 500



if __name__ == "__main__":
    app.run(debug=True)  
