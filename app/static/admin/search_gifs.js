document.getElementById('giphySearchInput').addEventListener('input', function(e) {
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
                    img.alt = gif.alt_text;
                    img.title = gif.alt_text;
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
            });
    }
});