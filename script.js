document.addEventListener('DOMContentLoaded', function() {
    const scanForm = document.getElementById('scanForm');
    const categorySelect = document.getElementById('categorySelect');
    const subcategoryContainer = document.getElementById('subcategoryContainer');
    const subcategoryOptions = document.getElementById('subcategoryOptions');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsTitle = document.getElementById('resultsTitle');
    const dealList = document.getElementById('dealList');

    // Define subcategories for each category
    const subcategories = {
        'Tech': [
            'Laptops', 'Smartphones', 'Tablets', 'Headphones', 'Gaming Consoles', 
            'Computer Parts', 'Cameras', 'Smartwatches', 'Bluetooth Speakers'
        ],
        'Collectibles': [
            'Action Figures', 'Comic Books', 'Coins', 'Stamps', 'Vinyl Records', 
            'Movie Memorabilia', 'Vintage Toys', 'Autographs'
        ],
        'Antiques': [
            'Furniture', 'Jewelry', 'Clocks', 'Art', 'Silverware', 
            'Glassware', 'Pottery', 'Books'
        ],
        'Trading Cards': [
            'Magic: The Gathering', 'Pokémon', 'Yu-Gi-Oh!', 'Baseball Cards', 
            'Football Cards', 'Basketball Cards', 'Soccer Cards', 'Hockey Cards'
        ],
        'Vintage Clothing': [
            'Denim', 'T-Shirts', 'Jackets', 'Dresses', 'Sweaters', 
            'Band Merch', 'Designer Items', 'Activewear'
        ],
        'Shoes': [
            'Sneakers', 'Boots', 'Dress Shoes', 'Athletic Shoes', 'Designer Shoes',
            'Limited Edition', 'Vintage', 'Sandals'
        ]
    };

    // Update subcategories when category changes
    categorySelect.addEventListener('change', function() {
        const category = this.value;
        if (category) {
            populateSubcategories(category);
            subcategoryContainer.style.display = 'block';
        } else {
            subcategoryContainer.style.display = 'none';
        }
    });

    // Populate subcategories based on selected category
    function populateSubcategories(category) {
        subcategoryOptions.innerHTML = '';
        const options = subcategories[category] || [];
        
        options.forEach((subcategory, index) => {
            const checkboxId = `subcategory-${index}`;
            
            const checkboxDiv = document.createElement('div');
            checkboxDiv.className = 'checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = checkboxId;
            checkbox.name = 'subcategories';
            checkbox.value = subcategory;
            
            const label = document.createElement('label');
            label.htmlFor = checkboxId;
            label.textContent = subcategory;
            
            checkboxDiv.appendChild(checkbox);
            checkboxDiv.appendChild(label);
            subcategoryOptions.appendChild(checkboxDiv);
        });
    }

    scanForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the selected category
        const category = categorySelect.value;
        
        if (!category) {
            alert('Please select a category');
            return;
        }
        
        // Get selected subcategories
        const selectedSubcategories = [];
        document.querySelectorAll('input[name="subcategories"]:checked').forEach(checkbox => {
            selectedSubcategories.push(checkbox.value);
        });
        
        if (selectedSubcategories.length === 0) {
            alert('Please select at least one subcategory');
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
            body: JSON.stringify({ 
                category: category,
                subcategories: selectedSubcategories
            })
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
                dealList.innerHTML = '<p class="no-results">No arbitrage opportunities found. Please try different subcategories or check back later.</p>';
            }
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            dealList.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
            console.error('Error:', error);
        });
    });

    function displayDeals(deals) {
        dealList.innerHTML = '';
        
        deals.forEach(deal => {
            const listItem = document.createElement('li');
            listItem.className = 'deal-item';
            
            const buyPrice = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(deal.buyPrice);
            
            const sellPrice = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(deal.sellPrice);
            
            const profit = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(deal.profit);
            
            const profitPercentage = deal.profitPercentage.toFixed(0);
            
            listItem.innerHTML = `
                <div class="deal-header">
                    <h3>${deal.title}</h3>
                    <span class="confidence-badge" style="background-color: ${getConfidenceColor(deal.confidence)}">
                        ${deal.confidence}% Confidence
                    </span>
                </div>
                <div class="deal-prices">
                    <div class="price-container">
                        <div class="price-label">Buy for:</div>
                        <div class="buy-price">${buyPrice}</div>
                        <a href="${deal.buyLink}" target="_blank" class="deal-btn buy-btn">View Listing</a>
                    </div>
                    <div class="price-container">
                        <div class="price-label">Sell for:</div>
                        <div class="sell-price">${sellPrice}</div>
                        <a href="${deal.sellLink}" target="_blank" class="deal-btn sell-btn">View Listing</a>
                    </div>
                </div>
                <div class="deal-profit">
                    <div class="profit-amount">Potential Profit: ${profit}</div>
                    <div class="profit-percentage">(${profitPercentage}% ROI)</div>
                </div>
                <div class="deal-info">
                    <p class="deal-subcategory">Category: ${deal.subcategory}</p>
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
