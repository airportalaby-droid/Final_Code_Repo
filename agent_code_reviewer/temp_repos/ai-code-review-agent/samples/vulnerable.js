// Example JS vulnerable snippet
const userContent = location.search.substring(1);
// XSS: direct insertion
document.getElementById('out').innerHTML = userContent;

// safer approach
document.getElementById('out-safe').textContent = userContent;
