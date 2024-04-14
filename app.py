import itertools
import os
#import torch 
#from transformers import BartTokenizer, BartForConditionalGeneration  
#import PyPDF2
#import io 
import arxiv 
import requests
#import io
#import multiprocessing  
from flask import Flask, Response, jsonify, render_template, request 
from tempfile import TemporaryDirectory 



#if torch.cuda.is_available():
#    print("GPU is available") 
#else:
#    print("GPU is not available")  

#import os
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"  
#os.environ["TOKENIZERS_PARALLELISM"] = "false"  

#def process_query(search_query):
#    search = arxiv.Search(query=search_query, max_results=10)  
#    results = search.results()                              
#    papers = []
#    for paper in results:
#        paper_data = {
#            'title': paper.title,
#            'abstract': paper.summary,
#            'authors': [author.name for author in paper.authors],
#            'pdf_url': paper.pdf_url,
#            'arxiv_url': paper.entry_id,
#            'summary': generate_summary(paper.summary)  # Using our summarization function
#        }
#        papers.append(paper_data)

#    return papers   

# PyTorch GPU Setup 
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  

# Load the BART CNN model (PyTorch)
#model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn").to(device) 
#tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn") 

#def fetch_and_parse_pdf(pdf_url):
 #   response = requests.get(pdf_url)
 #   with io.BytesIO(response.content) as f:  # Create BytesIO wrapper
 #       pdf_reader = PyPDF2.PdfReader(f)
 #       pdf_text = ""
 #       for page_num in range(len(pdf_reader.pages)):
 #           page = pdf_reader.pages[page_num]
 #           pdf_text += page.extract_text()
 #       return pdf_text 

#def generate_summary(pdf_text, max_length=150):  
#    inputs = tokenizer(pdf_text, return_tensors="pt").to(device) 
#   outputs = model.generate(**inputs)  
#    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)  
#    return summary

#def process_pdf_in_portions(pdf_text, portion_size=10, batch_size=1): 
#    portions = [pdf_text[i:i + portion_size] for i in range(0, len(pdf_text), portion_size)]
#
#    with multiprocessing.Pool() as pool:  
#        result = []
#       for i in range(0, len(portions), batch_size):
#            batch = portions[i:i + batch_size]
#            summaries = pool.map(generate_summary, batch)
#            result.extend(summaries) # Combine results into a single list
#       return result  
    

app = Flask(__name__) 

@app.route("/", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        if request.args.get('author_search'):  # Check for author search
            author_name = request.args.get('query')
            papers = search_arxiv_by_author(author_name) 
        else:  # Regular search 
            search_query = request.form["query"]
            page = request.args.get('page', 1, type=int) 
            results_per_page = 10 

            search = arxiv.Search(query=search_query)  
            results = search.results()  

            # Pagination 
            total_results = 0  
            start_index = (page - 1) * results_per_page  
            end_index = start_index + results_per_page   

            for paper in results:  
                total_results += 1 

                if total_results > end_index: 
                    break

            total_pages = (total_results // results_per_page) + (total_results % results_per_page > 0)

            # Reset to iterate results again 
            results = search.results()
            papers_for_current_page = list(itertools.islice(results, start_index, end_index))

            # Format results for display
            formatted_papers = []
            for paper in papers_for_current_page:
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

        return render_template("results.html", 
                               papers=formatted_papers, 
                               current_page=page, 
                               total_pages=total_pages) 
    else:
        return render_template("index.html") 

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


if __name__ == "__main__":
    app.run(debug=True) 