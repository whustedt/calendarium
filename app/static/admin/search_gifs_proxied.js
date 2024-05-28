let debounceTimeout;

// Set up an event listener for input on the search box.
document.getElementById('giphySearchInput').addEventListener('input', function(e) {
    // Clear any existing timeout to ensure that it only fires after the user has stopped typing for 1 second.
    clearTimeout(debounceTimeout);
    
    // Set a new timeout to debounce the input event.
    debounceTimeout = setTimeout(() => {
        var query = e.target.value;  // Get the current value of the input field.
        var resultsContainer = document.getElementById('giphySearchResults');  // Get the container for displaying GIFs.
        
        // Clear results if the input is empty or not enough characters are typed.
        if (query.length === 0) {
            resultsContainer.innerHTML = '';
            document.getElementById('hiddenGiphyUrl').value = '';
        } else if (query.length > 2) {
            // Make a request to the backend to get the secured Giphy URL.
            fetch(`${getGiphyUrlUrl}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // Use the URL provided by the backend to fetch data directly from Giphy.
                    fetch(data.url)
                        .then(response => response.json())
                        .then(giphyData => {
                            resultsContainer.innerHTML = '';
                            // Iterate through the GIF data to create and display image elements.
                            giphyData.data.forEach(gif => {
                                var img = document.createElement('img');
                                img.src = gif.images.fixed_height.url;
                                var tooltip = `${gif.username ? `Created by ${gif.username}` : ''}${gif.username && gif.alt_text ? ': ' : ''}${gif.alt_text || ''}` || 'No additional information available';
                                img.alt = tooltip;
                                img.title = tooltip;
                                img.classList.add('gif-image');
                                img.onclick = function() {
                                    // Manage the selection and deselection of GIFs.
                                    document.querySelectorAll('.gif-image').forEach(g => {
                                        g.classList.remove('selected');
                                        g.classList.add('not-selected');
                                    });
                                    img.classList.add('selected');
                                    img.classList.remove('not-selected');
                                    // Store the selected GIF URL in a hidden input for later use.
                                    document.getElementById('hiddenGiphyUrl').value = img.src;
                                };
                                resultsContainer.appendChild(img);
                            });
                            var imgAttr = document.createElement('img');
                            imgAttr.src = `${attributionImg}`;
                            resultsContainer.appendChild(imgAttr);
                        });
                });
        }
    }, 1000);  // Wait for one second after the user stops typing to minimize unnecessary API calls.
});
