
window.addEventListener('load', () => {
    attachButtonEvents(); // Attach listeners to initially loaded buttons
  });

  
  
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('favorite-button')) {
        const paperId = event.target.dataset.paperId;
        const isFavorite = event.target.textContent.includes('Remove');
        const paperContainer = event.target.closest('.search-result'); // Get the parent container

        const url = isFavorite ? '/remove_favorite' : '/add_favorite';
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ paper_id: paperId }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);

            if (isFavorite) {
                // Remove the paper container from the DOM
                paperContainer.remove();
            } else {
                // Update button text and styling (for adding to favorites)
                event.target.textContent = 'Remove from Favorites'; 
            }

            // Store favorite state in local storage
            localStorage.setItem(paperId, !isFavorite);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
});


// On page load, set button states based on local storage
window.addEventListener('load', function() {
    const favoriteButtons = document.querySelectorAll('.favorite-button');
    favoriteButtons.forEach(button => {
        const paperId = button.dataset.paperId;
        const isFavorite = localStorage.getItem(paperId) === 'true';
        button.textContent = isFavorite ? 'Remove from Favorites' : 'Add to Favorites';
        // ... (additional styling updates if needed)
    });
}); 

