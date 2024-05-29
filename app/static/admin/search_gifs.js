let debounceTimeout;

// Function to check if Giphy is enabled and display the search input accordingly
function checkGiphyEnabledAndDisplay() {
    fetch('/check-giphy-enabled')
        .then(response => response.json())
        .then(data => {
            if (data.enabled) {
                document.getElementById('giphySearchSection').style.display = 'block';  // Show the search input
                setupGiphySearch();  // Setup the event listener for Giphy search
            } else {
                document.getElementById('giphySearchSection').style.display = 'none';  // Hide the search input if not enabled
            }
        })
        .catch(error => console.error('Error checking Giphy status:', error));
}

// Function to set up event listener and handle the search input for GIFs
function setupGiphySearch() {
    document.getElementById('giphySearchInput').addEventListener('input', function(e) {
        clearTimeout(debounceTimeout);
        
        debounceTimeout = setTimeout(() => {
            var query = e.target.value;
            var resultsContainer = document.getElementById('giphySearchResults');
            
            if (query.length === 0) {
                resultsContainer.innerHTML = '';
                document.getElementById('hiddenGiphyUrl').value = '';
            } else if (query.length > 2) {
                fetch(`${searchGifsUrl}?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        resultsContainer.innerHTML = '';
                        data.forEach(gif => {
                            var img = document.createElement('img');
                            img.src = gif.images.fixed_height.url;
                            var tooltip = `${gif.username ? `Created by ${gif.username}` : ''}${gif.username && gif.alt_text ? ': ' : ''}${gif.alt_text || ''}` || 'No additional information available';
                            img.alt = tooltip;
                            img.title = tooltip;
                            img.classList.add('gif-image');
                            img.onclick = function() {
                                document.querySelectorAll('.gif-image').forEach(g => {
                                    g.classList.remove('selected');
                                    g.classList.add('not-selected');
                                });
                                img.classList.add('selected');
                                img.classList.remove('not-selected');
                                document.getElementById('hiddenGiphyUrl').value = img.src;
                            };
                            resultsContainer.appendChild(img);
                        });
                        var imgAttr = document.createElement('img');
                        imgAttr.src = `${attributionImg}`;
                        resultsContainer.appendChild(imgAttr);
                    });
            }
        }, 1000);  // Wait for one second after the user stops typing
    });
}

checkGiphyEnabledAndDisplay();