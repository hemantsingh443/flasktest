import sqlite3
from flask_login import UserMixin 
import arxiv

DATABASE_FILE = 'arxiv_app.db'  # Name of your database file

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables():
    """Creates the necessary database tables."""
    conn = get_db_connection()
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Create papers table
    c.execute('''CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY,
        title TEXT,
        authors TEXT,
        abstract TEXT,
        pdf_url TEXT,
        arxiv_url TEXT UNIQUE
    )''')

    # Create favorites table
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER,
        paper_id TEXT,
        PRIMARY KEY (user_id, paper_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (paper_id) REFERENCES papers(arxiv_url)
    )''')

    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    else:
        return None

def get_user_by_id(user_id):
    """Retrieves a user by ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE id = ?", (user_id,))  # Select specific columns
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(*user_data)
    else:
        return None 
    
def add_user(username, password):
    """Adds a new user to the database."""
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close() 


def get_papers_by_ids(paper_ids):
  """Retrieves paper details from arXiv API by a list of paper IDs, handling both old and new formats."""
  papers = []
  for paper_id in paper_ids:
    try:
      # Check if the identifier is in the old format
      if paper_id.count('.') == 0 and paper_id[-2] == 'v':
        # Add "hep-th/" prefix for old format
        search_id = f"hep-th/{paper_id[:-2]}"  # Remove the "vX" part
      else:
        # Use new format directly without modification
        search_id = paper_id 
      
      search = arxiv.Search(id_list=[search_id])
      paper = next(search.results())
      paper_data = {
        'title': paper.title,
        'authors': [author.name for author in paper.authors],
        'abstract': paper.summary,
        'pdf_url': paper.pdf_url,
        'arxiv_url': paper.entry_id,
      }
      print(paper_data)
      papers.append(paper_data)
    except Exception as e:
      print(f"Error retrieving paper {paper_id}: {e}")
  return papers

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.id)  # Flask-Login requires a string ID

    def add_favorite(self, paper_url):
      paper_id = paper_url.split('/')[-1]  # Extract paper_id
      conn = get_db_connection()
      try:
        conn.execute('INSERT INTO favorites (user_id, paper_id) VALUES (?, ?)', (self.id, paper_id))
        conn.commit()
      except sqlite3.IntegrityError:
        # Handle duplicate entry
        print(f"Paper {paper_id} is already a favorite for user {self.id}")
      finally:
       conn.close()

    def remove_favorite(self, paper_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM favorites WHERE user_id = ? AND paper_id = ?', (self.id, paper_id)) 
        print(paper_id)
        conn.commit()
        conn.close()

    def get_favorite_paper_ids(self):
      conn = get_db_connection()
      c = conn.cursor()
      c.execute("SELECT paper_id FROM favorites WHERE user_id = ?", (self.id,))
      paper_ids_with_urls = [row[0] for row in c.fetchall()]
      conn.close()
      favorite_paper_ids = []
      for paper_id_with_url in paper_ids_with_urls:
         try:
            # Extract paper ID from URL
            paper_id = paper_id_with_url.split('/')[-1]  
            favorite_paper_ids.append(paper_id)
         except IndexError:
            # Handle cases where the URL format is unexpected
            print(f"Error extracting paper ID from: {paper_id_with_url}") 

      return favorite_paper_ids 