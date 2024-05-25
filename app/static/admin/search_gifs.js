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
});