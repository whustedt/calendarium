let debounceTimeout;

// Checks if Giphy is enabled and sets up the search interface accordingly
function checkGiphyEnabledAndDisplay() {
    fetch('/check-giphy-enabled')
        .then(response => response.json())
        .then(data => {
            const searchSection = document.getElementById('giphySearchSection');
            if (data.enabled) {
                searchSection.style.display = 'block'; // Show the search input
                setupGiphySearch(); // Set up the search input event listener
            } else {
                searchSection.style.display = 'none'; // Hide the search input if not enabled
            }
        })
        .catch(error => console.error('Error checking Giphy status:', error));
}

// Sets up event listener for the Giphy search input
function setupGiphySearch() {
    const searchInput = document.getElementById('giphySearchInput');
    const resultsContainer = document.getElementById('giphySearchResults');

    searchInput.addEventListener('input', function(e) {
        clearTimeout(debounceTimeout);

        debounceTimeout = setTimeout(() => {
            let query = searchInput.value;
            if (query.length === 0) {
                resultsContainer.innerHTML = '';
                // TODO Reset Submitbutton
            } else if (query.length > 2) {
                fetchGiphyData(query, resultsContainer);
            }
        }, 1000);
    });
}

// Fetches GIFs from Giphy and updates the results container
function fetchGiphyData(query, resultsContainer) {
    fetch(`${getGiphyUrlUrl}?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => fetch(data.url))
        .then(response => response.json())
        .then(giphyData => updateResultsContainer(giphyData, resultsContainer));
}

// Updates the results container with GIFs
function updateResultsContainer(giphyData, resultsContainer) {
    resultsContainer.innerHTML = '';
    giphyData.data.forEach(gif => {
        let img = document.createElement('img');
        img.src = gif.images.fixed_height.url;
        var tooltip = `${gif.username ? `Created by ${gif.username}` : ''}${gif.username && gif.alt_text ? ': ' : ''}${gif.alt_text || ''}` || 'No additional information available';
        img.alt = tooltip;
        img.title = tooltip;
        img.classList.add('gif-image');
        img.onclick = () => selectGif(img, gif.images.fixed_height.url, resultsContainer);
        resultsContainer.appendChild(img);
    });
    // Add Giphy attributioon
    var imgAttr = document.createElement('img');
    imgAttr.src = `${attributionImg}`;
    resultsContainer.appendChild(imgAttr);
}

// Handles GIF selection and applies style changes
function selectGif(imgElement, gifUrl, resultsContainer) {
    // Update styles for all images to indicate non-selection
    resultsContainer.querySelectorAll('.gif-image').forEach(img => {
        img.classList.remove('selected');
        img.classList.add('not-selected');
    });

    // Mark the current image as selected
    imgElement.classList.add('selected');
    imgElement.classList.remove('not-selected');

    fetch(gifUrl)
        .then(response => response.blob())
        .then(blob => {
            const file = new File([blob], 'selectedGif.gif', { type: 'image/gif' });
            const form = document.getElementById('entry-form');
            const formData = new FormData(form);
            formData.set('entryImage', file);

            // Set up form submission
            setUpFormSubmission(form, formData);
        });
}


// Sets up form submission
function setUpFormSubmission(form, formData) {
    const submitButton = document.getElementById('submit-button');
    submitButton.addEventListener('click', function(event) {
        event.preventDefault(); // Always prevent the default form submission

        // Check the form validity and report any errors
        if (true || form.checkValidity()) { // TODO turn on again after debugging
            submitForm(form.action, formData); // Only submit if the form is valid
        } else {
            form.reportValidity(); // This will show the validation messages
        }
    });
}

// Submits the form
function submitForm(actionUrl, formData) {
    fetch(actionUrl, {
        method: 'POST',
        body: formData,
        redirect: 'follow' // This should handle the redirection on successful form submission
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url; // Redirect if needed
        } else {
            console.log('Upload successful');
            // Additional handling if needed
        }
    })
    .catch(error => console.error('Error uploading the GIF:', error));
}

checkGiphyEnabledAndDisplay();