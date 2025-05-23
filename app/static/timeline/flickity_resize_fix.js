// Add this script at the end of your timeline.html, after the Flickity script
<script type="text/javascript">
document.addEventListener('DOMContentLoaded', function() {
    var timelineElement = document.querySelector('.timeline');
    var flkty;
    
    // Initialize Flickity with a slight delay
    setTimeout(function() {
        flkty = new Flickity(timelineElement, {
            initialIndex: '.initial-focus',
            cellAlign: 'left',
            pageDots: false,
            contain: true,
            resize: true // Enable automatic resize
        });
        
        // Force an initial resize
        flkty.resize();
    }, 100);
    
    // Listen for window resize events (important for iframe resizing)
    window.addEventListener('resize', function() {
        if (flkty) {
            setTimeout(function() {
                flkty.resize();
            }, 100);
        }
    });
    
    // Additional iframe-specific resize detection
    var resizeObserver = new ResizeObserver(function(entries) {
        if (flkty) {
            setTimeout(function() {
                flkty.resize();
            }, 100);
        }
    });
    
    // Observe the timeline container for size changes
    resizeObserver.observe(timelineElement);
    
    // Also observe the body in case the iframe itself is resizing
    resizeObserver.observe(document.body);
});
</script>