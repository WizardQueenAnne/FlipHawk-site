console.log("Script loaded");

// Test basic JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded");
    
    // Check if elements exist
    const root = document.getElementById('root');
    if (root) {
        console.log("Root element found");
        root.innerHTML = '<h1>FlipHawk is Loading...</h1>';
    } else {
        console.error("Root element not found");
    }
});
