document.addEventListener('DOMContentLoaded', function() {
    // Form Elements
    const scanForm = document.getElementById('scanForm');
    const categorySelect = document.getElementById('categorySelect');
    const subcategoryContainer = document.getElementById('subcategoryContainer');
    const subcategoryOptions = document.getElementById('subcategoryOptions');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingMessage = document.getElementById('loadingMessage');
    const resultsTitle = document.getElementById('resultsTitle');
    const dealList = document.getElementById('dealList');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const filterOptions = document.getElementById('filterOptions');
    const sortOptions = document.getElementById('sortOptions');
    const confidenceFilter = document.getElementById('confidenceFilter');
    const progressFill = document.querySelector('.progress-fill');
    
    // Define all categories and subcategories
    const categories = {
        'Tech': [
            'Headphones', 'Keyboards', 'Graphics Cards', 'CPUs', 'Laptops',
            'Monitors', 'SSDs', 'Routers', 'Vintage Tech'
        ],
        'Collectibles': [
            'Pokémon', 'Magic: The Gathering', 'Yu-Gi-Oh', 'Funko Pops', 'Sports Cards',
            'Comic Books', 'Action Figures', 'LEGO Sets'
        ],
        'Vintage Clothing': [
            'Jordans', 'Nike Dunks', 'Vintage Tees', 'Band Tees', 'Denim Jackets',
            'Designer Brands', 'Carhartt', 'Patagonia'
        ],
        'Antiques': [
            'Coins', 'Watches', 'Cameras', 'Typewriters', 'Vinyl Records',
            'Vintage Tools', 'Old Maps', 'Antique Toys'
        ],
        'Gaming': [
            'Consoles', 'Game Controllers', 'Rare Games', 'Arcade Machines', 
            'Handhelds', 'Gaming Headsets', 'VR Gear'
        ],
        'Music Gear': [
            'Electric Guitars', 'Guitar Pedals', 'Synthesizers', 'Vintage Amps',
            'Microphones', 'DJ Equipment'
        ],
        'Tools & DIY': [
            'Power Tools', 'Hand Tools', 'Welding Equipment', 'Toolboxes',
            'Measuring Devices', 'Woodworking Tools'
        ],
        'Outdoors & Sports': [
            'Bikes', 'Skateboards', 'Scooters', 'Camping Gear', 'Hiking Gear',
            'Fishing Gear', 'Snowboards'
        ]
    };
    
    // Category icons
    const categoryIcons = {
        'Tech': '💻',
        'Collectibles': '🏆',
        'Vintage Clothing': '👟',
        'Antiques': '🕰️',
        'Gaming': '🎮',
        'Music Gear': '🎸',
        'Tools & DIY': '🛠️',
        'Outdoors & Sports': '🚲'
    };
    
    // Subcategory icons
    const subcategoryIcons = {
        // Tech
        'Headphones': '🎧',
        'Keyboards': '⌨️',
        'Graphics Cards': '🖥️',
        'CPUs': '🔄',
        'Laptops': '💻',
        'Monitors': '🖥️',
        'SSDs': '💾',
        'Routers': '📡',
        'Vintage Tech': '📟',
        
        // Collectibles
        'Pokémon': '⚡',
        'Magic: The Gathering': '🃏',
        'Yu-Gi-Oh': '👹',
        'Funko Pops': '🧸',
        'Sports Cards': '🏆',
        'Comic Books': '📚',
        'Action Figures': '🦸',
        'LEGO Sets': '🧱',
        
        // Vintage Clothing
        'Jordans': '👟',
        'Nike Dunks': '👟',
        'Vintage Tees': '👕',
        'Band Tees': '🎸',
        'Denim Jackets': '🧥',
        'Designer Brands': '👜',
        'Carhartt': '👷',
        'Patagonia': '🏔️',
        
        // Default icon for others
        'default': '📦'
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
        const options = categories[category] || [];
        
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
            
            // Add icon if available
            const icon = subcategoryIcons[subcategory] || subcategoryIcons['default'];
            label.innerHTML = `${icon} ${subcategory}`;
            
            checkboxDiv.appendChild(checkbox);
            checkboxDiv.appendChild(label);
            subcategoryOptions.appendChild(checkboxDiv);
        });
        
        // Add click handler to checkbox items for better UX
        document.querySelectorAll('.checkbox-item').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't trigger if they clicked directly on the checkbox
                if (e.target !== this.querySelector('input[type="checkbox"]')) {
                    const checkbox = this.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                }
            });
        });
    }
    
    // Handle form submission
    scanForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the selected category
        const category = categorySelect.value;
        
        if (!category) {
            showAlert('Please select a category');
            return;
        }
        
        // Get selected subcategories
        const selectedSubcategories = [];
        document.querySelectorAll('input[name="subcategories"]:checked').forEach(checkbox => {
            selectedSubcategories.push(checkbox.value);
        });
        
        if (selectedSubcategories.length === 0) {
            showAlert('Please select at least one subcategory');
            return;
        }
        
        if (selectedSubcategories.length > 5) {
            showAlert('Please select up to 5 subcategories for optimal results');
            return;
        }
        
        // Show loading indicator and hide results
        startLoading(selectedSubcategories);
        resetResults();
        
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
            stopLoading();
            
            // Display results
            displayResults(data, selectedSubcategories);
        })
        .catch(error => {
            stopLoading();
            showError('Error connecting to server. Please try again.');
            console.error('Error:', error);
        });
    });
    
    // Display resale opportunities
    function displayResults(deals, selectedSubcategories) {
        // Hide loading indicator completely
        loadingIndicator.style.display = 'none';
        
        // Display results
        if (deals && deals.length > 0) {
            resultsTitle.style.display = 'block';
            resultsTitle.textContent = 'Top Resale Opportunities';
            filterOptions.style.display = 'flex';
            displayDeals(deals);
        } else {
            noResultsMessage.style.display = 'block';
            
            // Make the message more specific with the selected subcategories
            const subCatList = selectedSubcategories.join(', ');
            document.querySelector('.no-results-content p:first-of-type').textContent = 
                `We couldn't find any resale opportunities for ${subCatList} at the moment.`;
        }
    }
    
    // Display deals as cards
    function displayDeals(deals) {
        dealList.innerHTML = '';
        
        deals.forEach(deal => {
            const card = document.createElement('div');
            card.className = 'opportunity-card';
            
            // Format prices
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
            
            const profitPercentage = Math.round(deal.profitPercentage);
            
            // Get confidence color
            const confidenceColor = getConfidenceColor(deal.confidence);
            
            // Calculate estimated taxes (simplified, around 8%)
            const estimatedTax = deal.buyPrice * 0.08;
            const estimatedShipping = 5.99; // Example fixed shipping cost
            
            const totalCost = deal.buyPrice + estimatedTax + estimatedShipping;
            const netProfit = deal.sellPrice - totalCost;
            const netProfitPercentage = (netProfit / totalCost) * 100;
            
            const formattedNetProfit = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(netProfit);
            
            // Get icon for subcategory
            const subcategoryIcon = getSubcategoryIcon(deal.subcategory);
            
            card.innerHTML = `
                <div class="opportunity-header">
                    <div class="opportunity-title">
                        <h3>${deal.title}</h3>
                        <span class="confidence-badge" style="background-color: ${confidenceColor}">
                            ${deal.confidence}% Match
                        </span>
                    </div>
                </div>

                <div class="product-comparison">
                    <div class="product-card buy-card">
                        <div class="product-image">
                            <img src="${deal.image_url || 'https://via.placeholder.com/300x180?text=No+Image'}" alt="${deal.title}">
                        </div>
                        <div class="product-details">
                            <div class="product-price">${buyPrice}</div>
                            <div class="product-condition">${deal.buyCondition || 'New'}</div>
                            <a href="${deal.buyLink}" target="_blank" class="product-btn buy-btn">
                                <i class="fas fa-shopping-cart"></i> Buy Product
                            </a>
                        </div>
                    </div>
                    
                    <div class="profit-details">
                        <div class="profit-card">
                            <div class="profit-header">Profit Details</div>
                            <div class="profit-row">
                                <span>Cost Price:</span>
                                <span>${buyPrice}</span>
                            </div>
                            <div class="profit-row">
                                <span>Est. Tax (8%):</span>
                                <span>+$${estimatedTax.toFixed(2)}</span>
                            </div>
                            <div class="profit-row">
                                <span>Est. Shipping:</span>
                                <span>+$${estimatedShipping.toFixed(2)}</span>
                            </div>
                            <div class="profit-row">
                                <span>Selling Price:</span>
                                <span>${sellPrice}</span>
                            </div>
                            <div class="profit-total">
                                <span>Net Profit:</span>
                                <span>${formattedNetProfit}</span>
                            </div>
                            <div class="profit-roi">
                                <span>ROI:</span>
                                <span>${Math.round(netProfitPercentage)}%</span>
                            </div>
                        </div>
                    </div>

                    <div class="product-card sell-card">
                        <div class="product-image">
                            <img src="${deal.image_url || 'https://via.placeholder.com/300x180?text=No+Image'}" alt="${deal.title}">
                        </div>
                        <div class="product-details">
                            <div class="product-price">${sellPrice}</div>
                            <div class="product-condition">${deal.sellCondition || 'New'}</div>
                            <a href="${deal.sellLink}" target="_blank" class="product-btn sell-btn">
                                <i class="fas fa-external-link-alt"></i> View Listing
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="opportunity-footer">
                    <div class="opportunity-category">
                        <i class="fas fa-tag"></i> ${subcategoryIcon} ${deal.subcategory}
                    </div>
                    <div class="opportunity-actions">
                        <button class="save-btn"><i class="far fa-bookmark"></i> Save</button>
                        <button class="share-btn"><i class="fas fa-share-alt"></i> Share</button>
                    </div>
                </div>
            `;
            
            dealList.appendChild(card);
            
            // Add save functionality
            const saveBtn = card.querySelector('.save-btn');
            saveBtn.addEventListener('click', function() {
                const bookmarkIcon = this.querySelector('i');
                if (bookmarkIcon.classList.contains('far')) {
                    bookmarkIcon.classList.replace('far', 'fas');
                    showAlert('Opportunity saved!');
                } else {
                    bookmarkIcon.classList.replace('fas', 'far');
                    showAlert('Opportunity removed from saved items');
                }
            });
            
            // Add share functionality
            const shareBtn = card.querySelector('.share-btn');
            shareBtn.addEventListener('click', function() {
                if (navigator.share) {
                    navigator.share({
                        title: 'FlipHawk Resale Opportunity',
                        text: `Check out this profit opportunity: ${deal.title} - Buy: ${buyPrice}, Sell: ${sellPrice}, Profit: ${profit}`,
                        url: window.location.href
                    })
                    .catch(() => showAlert('Copied to clipboard!'));
                } else {
                    // Fallback to copy to clipboard
                    const shareText = `Resale opportunity
