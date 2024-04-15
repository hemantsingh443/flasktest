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
// ... other JavaScript code ...

// Click handler for author links
const authorLinks = document.querySelectorAll('.author-link'); 

authorLinks.forEach(link => {
    link.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent default link behavior
        const authorName = link.dataset.authorName;
        searchByAuthor(authorName); 
    });
});

// Function to search by author (assuming you have this function)
function searchByAuthor(authorName) {
    const formattedAuthorName = encodeURIComponent(authorName); // Encode for URL
    const query = `au:"${formattedAuthorName}"`; // arXiv API syntax

    fetch(`/search?query=${query}`) // Assuming you have a /search endpoint
        .then(response => response.json())
        .then(data => {
            const formattedPapers = data.results.map(paper => ({
                title: paper.title,
                authors: paper.authors.map(author => author.name).join(', '),
                // ... (add other properties as needed) ...
            }));
    
            // Update HTML elements with results
            const resultsList = document.getElementById('results-list'); // Assuming you have a <ul> with this ID
            resultsList.innerHTML = ''; // Clear previous results
            formattedPapers.forEach(paper => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <h3>${paper.title}</h3>
                    <p>By: ${paper.authors}</p>
                    <p>${paper.summary}</p>
                    <!-- ... add other details as needed ... -->
                `;
                resultsList.appendChild(listItem);
            });
        })

        .catch(error => console.error('Error fetching author results:', error));
}



function summarizePdf(pdfUrl) {
    fetch('/summarize_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ pdf_url: pdfUrl }) // Send as JSON data
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Summarization failed!'); 
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            // Display error message from the server
            alert('Error: ' + data.error); // Example error display
        } else {
            const summaryText = data.summary;
            updateSummary(pdfUrl, summaryText); 
        }
    })
    .catch(error => console.error('Error:', error)); 
}
 
let intervalCounter = 0; // Counter for unique IDs
const intervalIds = {}; // Store interval IDs

function summarizePdf(pdfUrl) {
    return fetch('/summarize_pdf', { // Return the promise for chaining
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pdf_url: pdfUrl })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Summarization failed!');
        }
        return response.json();
    });
}

const summaryButtons = document.querySelectorAll('.summary-button');

summaryButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        const pdfUrl = button.dataset.pdfUrl;
        const progressBarFill = button.querySelector('.progress-bar-fill'); 
        let progress = 0;
        const intervalId = intervalCounter++; // Generate unique ID

        // Disable the button to prevent concurrent requests
        button.disabled = true;

        // Clear any existing interval for this button
        if (intervalIds[intervalId]) {
            clearInterval(intervalIds[intervalId]);
            delete intervalIds[intervalId];
        }

        // Function to update the progress bar
        const updateProgressBar = () => {
            progress += 5; // Adjust increment as needed
            if (progressBarFill) { // Check if progressBarFill exists
                progressBarFill.style.width = progress + "%"; 
            }

            if (progress >= 100) {
                clearInterval(intervalIds[intervalId]);
                delete intervalIds[intervalId];
                button.disabled = false; // Re-enable the button
                // Optionally, display a completion message or reset the progress bar
            }
        };

        // Start the progress bar animation
        intervalIds[intervalId] = setInterval(updateProgressBar, 200); 

        // Trigger the summarization process
        summarizePdf(pdfUrl)
            .then(data => {
                if (data.error) {
                    // Handle error (e.g., display an error message)
                    console.error("Error:", data.error);
                } else {
                    const summaryText = data.summary;
                    updateSummary(pdfUrl, summaryText); 
                }
            })
            .catch(error => {
                console.error("Error fetching summary:", error);
                // Handle error
            })
            .finally(() => { // Always execute, even if there's an error
                clearInterval(intervalIds[intervalId]); // Clear interval
                delete intervalIds[intervalId];
                progress = 0; // Reset progress
                if (progressBarFill) {
                    progressBarFill.style.width = "0%";
                }
                button.disabled = false; 
            });
    });
});
   
// Function to dynamically update summary elements
function updateSummary(pdfUrl, summary) {
    const summaryElement = document.getElementById(`summary-${pdfUrl}`);
    if (summaryElement) {
        summaryElement.textContent = summary;
    } 
}
function displaySummary() {
    fetch('/get_summary')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                // Handle error (e.g., display an error message)
                console.error("Error:", data.error);
            } else {
                const summaryText = data.summary;
                const summaryElement = document.getElementById("summary-container");  // Assuming you have an element with this ID
                summaryElement.textContent = summaryText;
            }
        })
        .catch(error => console.error("Error fetching summary:", error));
} 
// ... (existing JavaScript code) ...

// Logic for pagination links
$(document).on('click', '.page-link', function(event) {
    event.preventDefault();
    const page = $(this).data('page');
    const query = new URLSearchParams(window.location.search).get('query');

    fetch(`/search?query=${query}&page=${page}`)
        .then(response => response.text())
        .then(html => {
            $('#results-container').html(html); // Update only the results container
            updatePaginationLinks(page);
        });
}); 
// Function to update pagination links
function updatePaginationLinks(page) {
    const paginationLinks = document.querySelectorAll('.page-link');
  
    // Update the 'href' attribute of each link
    paginationLinks.forEach(link => {
      const newPage = link.dataset.page;
      link.href = generatePaginationLink(newPage, query);
    });
  
    // Add 'active' class to the current page link
    const activeLink = document.querySelector(`.page-link[data-page="${page}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
  }
