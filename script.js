document.addEventListener('DOMContentLoaded', function() {
    const scanForm = document.getElementById('scanForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsTitle = document.getElementById('resultsTitle');
    const dealList = document.getElementById('dealList');

    scanForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the selected category
        const categorySelect = document.getElementById('categorySelect');
        const category = categorySelect.value;
        
        if (!category) {
            alert('Please select a category');
            return;
        }
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        resultsTitle.style.display = 'none';
        dealList.innerHTML = '';
        
        // Make API request to Flask backend
        fetch('/run_scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ category: category })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Display results
            if (data.length > 0) {
                resultsTitle.style.display = 'block';
                displayDeals(data);
            } else {
                dealList.innerHTML = '<p>No arbitrage opportunities found. Try a different category.</p>';
            }
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            dealList.innerHTML = `<p>Error: ${error.message}</p>`;
            console.error('Error:', error);
        });
    });

    function displayDeals(deals) {
        dealList.innerHTML = '';
        
        deals.forEach(deal => {
            const listItem = document.createElement('li');
            listItem.className = 'deal-item';
            
            const priceFormatted = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(deal.price);
            
            listItem.innerHTML = `
                <div class="deal-header">
                    <h3>${deal.title}</h3>
                    <span class="confidence-badge" style="background-color: ${getConfidenceColor(deal.confidence)}">
                        ${deal.confidence}% Confidence
                    </span>
                </div>
                <div class="deal-body">
                    <p class="deal-price">${priceFormatted}</p>
                    <p class="deal-keyword">Keyword: ${deal.keyword}</p>
                    <a href="${deal.link}" target="_blank" class="view-deal-btn">View on eBay</a>
                </div>
            `;
            
            dealList.appendChild(listItem);
        });
    }
    
    function getConfidenceColor(confidence) {
        if (confidence >= 90) return "#4CAF50"; // Green
        if (confidence >= 80) return "#8BC34A"; // Light Green
        if (confidence >= 70) return "#FFC107"; // Amber
        return "#FF5722"; // Deep Orange
    }
});
