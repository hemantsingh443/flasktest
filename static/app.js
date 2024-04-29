// Logic for dark/light mode
const toggleButton = document.getElementById('dark-mode-toggle');
toggleButton.addEventListener('click', () => {
  document.body.classList.toggle('dark');
});

// Logic for text highlighting
const highlightElements = document.querySelectorAll('.highlight-text');
highlightElements.forEach(element => {
  element.addEventListener('click', () => {
    element.classList.toggle('highlighted');
  });
});  
window.addEventListener('load', () => {
  attachButtonEvents();
});

// Logic for download button
function attachButtonEvents() {
    const downloadButtons = document.querySelectorAll('.download-button');
    downloadButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        const pdfUrl = button.dataset.pdfUrl;
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

// Logic for arXiv buttons
const arxivButtons = document.querySelectorAll('.arxiv-button');
arxivButtons.forEach(button => {
  button.addEventListener('click', () => {
    const pdfUrl = button.dataset.pdfUrl;
    const arxivUrl = pdfUrl.replace('.pdf', '').replace('/pdf/', '/abs/');
    window.open(arxivUrl, '_blank');
  });
});
}
function updateSearchResults(htmlContent) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    const newSearchResults = doc.getElementById('search-results');
    const existingSearchResults = document.getElementById('search-results'); 
    if (newSearchResults && existingSearchResults) {
      existingSearchResults.innerHTML = newSearchResults.innerHTML;
      attachButtonEvents(); // Reattach event listeners
    } else {
      console.error("Error: Could not find search result elements.");
    }
  }
  
  // Click handler for author links (Update to reattach events)
  $(document).on('click', '.author-link', function(event) { 
    event.preventDefault();
    const authorName = $(this).data('authorName');
    const url = `/author/${encodeURIComponent(authorName)}`;
  
    $.get(url, function(response) {
      $('#author-results').html(response);
  
      // Show author results, adjust layout, and reattach events
      $('#author-results').show();
      $('#search-results').css('flex', '3'); // Adjust ratio as needed
      attachButtonEvents();
    });
  });

  $(document).on('click', '.page-link', function(event) {
    event.preventDefault();
    const url = $(this).attr('href');
    
    fetch(url)
      .then(response => response.text())
      .then(html => {
        updateSearchResults(html);
        updatePaginationLinks(); 
  
        // Apply split-screen layout if on author search page
        if (window.location.pathname.includes('/author/')) {
          $('#author-results').show();
          $('#search-results').css('flex', '3'); // Adjust ratio as needed
          attachButtonEvents(); // Reattach event listeners for new buttons
        }
      })
      .catch(error => {
        console.error("Error fetching page:", error);
        // Handle error (e.g., display an error message)
      });
  });
  
// Function to summarize PDF
function summarizePdf(pdfUrl) {
  const summaryElement = document.getElementById(`summary-${pdfUrl}`);
  console.log('Summary element:', summaryElement);
  
  if (summaryElement) {
      summaryElement.textContent = 'Summarizing...';
  } else {
      console.error('Element not found:', `summary-${pdfUrl}`);
      return; // Exit if the element is not found
  }

  fetch('/summarize_pdf', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pdf_url: pdfUrl }),
  })
      .then(response => response.body.getReader()) // Get a reader for the stream
      .then(reader => {
          let decoder = new TextDecoder();
          let summaryText = "";

          function readChunk({ done, value }) {
              if (done) {
                  summaryElement.textContent = summaryText; // Set final text
                  return;
              }

              summaryText += decoder.decode(value, { stream: true });
              
              // Create a chunk element and append
              let chunkElement = document.createElement('div');
              chunkElement.className = 'summary-chunk';
              chunkElement.textContent = decoder.decode(value, { stream: true });
              summaryElement.appendChild(chunkElement);

              // Read the next chunk
              reader.read().then(readChunk);
          }

          reader.read().then(readChunk); // Start reading chunks
      })
      .catch(error => {
          console.error('Error:', error);
          summaryElement.textContent = 'An error occurred during summarization.';
      });
}
// Attach event listeners to summary buttons (using event delegation)
document.addEventListener('click', function(event) {
  if (event.target.classList.contains('summary-button')) {
    const pdfUrl = event.target.dataset.pdfUrl;
    summarizePdf(pdfUrl);
  }
});
// Function to update pagination links (styling only)
function updatePaginationLinks() {
  const paginationLinks = document.querySelectorAll('.page-link');
  // Remove 'active' class from all links
  paginationLinks.forEach(link => {
    link.classList.remove('active');
  });
  // Add 'active' class to the current page link
  const currentUrl = window.location.href;
  const activeLink = document.querySelector(`.page-link[href="${currentUrl}"]`);
  if (activeLink) {
    activeLink.classList.add('active');
  } else {
    // Handle the case where the current page is not represented in the pagination links
    const currentPage = parseInt(currentUrl.match(/page=(\d+)/)[1]);
    const currentPageLink = document.querySelector(`.page-link[data-page="${currentPage}"]`);
    if (currentPageLink) {
      currentPageLink.classList.add('active');
    }
  }
}  


  
