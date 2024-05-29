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
                                        // Manipulate form data
                                        handleGifSelection(img.src);
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
}

// Function to handle GIF selection
function handleGifSelection(gifUrl) {
    fetch(gifUrl)
        .then(response => response.blob())
        .then(blob => {
            const file = new File([blob], 'selectedGif.gif', { type: 'image/gif' });
            const formData = new FormData(document.getElementById('entry-form'));
            formData.set('entryImage', file);
 
            // Use this formData object for the form submission instead of the standard submission method
            const submitButton = document.getElementById('submit-button');
            submitButton.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent the standard form submission
                fetch(document.getElementById('entry-form').action, {
                    method: 'POST',
                    body: formData,
                    redirect: 'follow'  // Ensure redirects are followed
                })
                .then(response => {
                    console.log('Upload successful');
                    if (response.redirected) {
                        window.location.href = response.url;  // Redirect to the new URL if a redirect occurred
                    }
                })
                .catch(error => {
                    console.error('Error uploading the GIF:', error);
                });
            });
        });
 }

checkGiphyEnabledAndDisplay();