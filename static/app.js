// ------- Dark/Light Mode --------
const toggleButton = document.getElementById('dark-mode-toggle');    
toggleButton.addEventListener('click', () => {
    document.body.classList.toggle('dark');    
});

// ------- Text Highlighting --------
const highlightElements = document.querySelectorAll('.highlight-text'); 
highlightElements.forEach(element => {
  element.addEventListener('click', () => {
    element.classList.toggle('highlighted'); 
  });
});

// ------- Download Button Logic --------
const downloadButtons = document.querySelectorAll('.download-button');  

downloadButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent default form submission
        const pdfUrl = button.dataset.pdfUrl; // Get PDF URL from button

        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ pdf_url: pdfUrl })  
        })
        .then(response => {
            if (!response.ok) {
                // Handle download errors 
                throw new Error('Download failed!'); 
            }
            return response.blob(); // Get PDF data as a Blob
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'downloaded_paper.pdf'; // Adjust filename as needed
            link.click();
            window.URL.revokeObjectURL(url); // Cleanup
        })
        .catch(error => {
            console.error('Download Error:', error);
            // Display an error message to the user (ex: alert)
        });
    }); 
});  
// ... your existing JavaScript ...

// Logic for arXiv buttons
const arxivButtons = document.querySelectorAll('.arxiv-button'); 

arxivButtons.forEach(button => {
    button.addEventListener('click', () => { 
        const pdfUrl = button.dataset.pdfUrl;
        const arxivUrl = pdfUrl.replace('.pdf', '').replace('/pdf/', '/abs/'); // Modified replacement pattern
        window.open(arxivUrl, '_blank'); 
    });
}); 
function searchByAuthor(authorName) {
    const formattedAuthorName = encodeURIComponent(authorName); 
    const query = `au:"${formattedAuthorName}"`;

    fetch(`/search_by_author?query=${encodeURIComponent(query)}`) 
        .then(response => response.json()) // Parse response as JSON
        .then(data => {
            const formattedPapers = processApiResults(data); // You'll need to create this function
            renderResults(formattedPapers); // You might need to create or adjust this
        })
        .catch(error => console.error('Error fetching author results:', error));
}


// Click handler for author links
const authorLinks = document.querySelectorAll('.author-link');
authorLinks.forEach(link => {
    link.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent default link behavior
        const authorName = link.dataset.authorName;
        searchByAuthor(authorName);
    });
});


