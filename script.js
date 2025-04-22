document.addEventListener('DOMContentLoaded', function() {
    // Form Elements
    const scanForm = document.getElementById('scanForm');
    const categorySelect = document.getElementById('categorySelect');
    const subcategoryContainer = document.getElementById('subcategoryContainer');
    const subcategoryOptions = document.getElementById('subcategoryOptions');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsTitle = document.getElementById('resultsTitle');
    const dealList = document.getElementById('dealList');
    
    // Auth Elements
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const loginModal = document.getElementById('loginModal');
    const signupModal = document.getElementById('signupModal');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    // Feedback Elements
    const feedbackBtn = document.getElementById('feedbackBtn');
    const feedbackModal = document.getElementById('feedbackModal');
    const feedbackForm = document.getElementById('feedbackForm');
    
    // About Elements
    const aboutLink = document.getElementById('aboutLink');
    const aboutModal = document.getElementById('aboutModal');
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    // Stats Elements
    const scanningCountEl = document.getElementById('scanningCount');
    const weeklyDealsCountEl = document.getElementById('weeklyDealsCount');
    const userCountEl = document.getElementById('userCount');
    
    // Close Modal Buttons
    const closeButtons = document.querySelectorAll('.close-modal');
    
    // User state
    let isLoggedIn = false;
    let userFavorites = [];
    
    // Define subcategories for each category with icons
    const subcategories = {
        'Tech': [
            { name: 'Laptops', icon: '💻' },
            { name: 'Smartphones', icon: '📱' },
            { name: 'Tablets', icon: '📱' },
            { name: 'Headphones', icon: '🎧' },
            { name: 'Gaming Consoles', icon: '🎮' },
            { name: 'Computer Parts', icon: '🔧' },
            { name: 'Cameras', icon: '📷' },
            { name: 'Smartwatches', icon: '⌚' },
            { name: 'Bluetooth Speakers', icon: '🔊' }
        ],
        'Collectibles': [
            { name: 'Action Figures', icon: '🦸' },
            { name: 'Comic Books', icon: '📚' },
            { name: 'Coins', icon: '🪙' },
            { name: 'Stamps', icon: '📬' },
            { name: 'Vinyl Records', icon: '💿' },
            { name: 'Movie Memorabilia', icon: '🎬' },
            { name: 'Vintage Toys', icon: '🧸' },
            { name: 'Autographs', icon: '✍️' }
        ],
        'Antiques': [
            { name: 'Furniture', icon: '🪑' },
            { name: 'Jewelry', icon: '💍' },
            { name: 'Clocks', icon: '🕰️' },
            { name: 'Art', icon: '🖼️' },
            { name: 'Silverware', icon: '🍴' },
            { name: 'Glassware', icon: '🥃' },
            { name: 'Pottery', icon: '🏺' },
            { name: 'Books', icon: '📚' }
        ],
        'Trading Cards': [
            { name: 'Magic: The Gathering', icon: '🃏' },
            { name: 'Pokémon', icon: '⚡' },
            { name: 'Yu-Gi-Oh!', icon: '👾' },
            { name: 'Baseball Cards', icon: '⚾' },
            { name: 'Football Cards', icon: '🏈' },
            { name: 'Basketball Cards', icon: '🏀' },
            { name: 'Soccer Cards', icon: '⚽' },
            { name: 'Hockey Cards', icon: '🏒' }
        ],
        'Vintage Clothing': [
            { name: 'Denim', icon: '👖' },
            { name: 'T-Shirts', icon: '👕' },
            { name: 'Jackets', icon: '🧥' },
            { name: 'Dresses', icon: '👗' },
            { name: 'Sweaters', icon: '🧶' },
            { name: 'Band Merch', icon: '🎸' },
            { name: 'Designer Items', icon: '👜' },
            { name: 'Activewear', icon: '🏃' }
        ],
        'Shoes': [
            { name: 'Sneakers', icon: '👟' },
            { name: 'Boots', icon: '👢' },
            { name: 'Dress Shoes', icon: '👞' },
            { name: 'Athletic Shoes', icon: '🏃' },
            { name: 'Designer Shoes', icon: '👠' },
            { name: 'Limited Edition', icon: '✨' },
            { name: 'Vintage', icon: '🕰️' },
            { name: 'Sandals', icon: '👡' }
        ]
    };

    // Initialize real-time stats with random values
    initializeStats();

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
            checkbox.value = subcategory.name;
            
            const label = document.createElement('label');
            label.htmlFor = checkboxId;
            label.innerHTML = `${subcategory.icon} ${subcategory.name}`;
            
            checkboxDiv.appendChild(checkbox);
            checkboxDiv.appendChild(label);
            subcategoryOptions.appendChild(checkboxDiv);
        });
    }

    // Handle form submission
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
        
        // Update scanning count
        updateScanningCount(selectedSubcategories.length * 20);
        
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
                
                // Update weekly deals count
                updateWeeklyDealsCount(data.length);
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

    // Display deals as cards
    function displayDeals(deals) {
        dealList.innerHTML = '';
        
        deals.forEach((deal, index) => {
            const isFavorite = userFavorites.some(fav => 
                fav.buyLink === deal.buyLink && fav.sellLink === deal.sellLink
            );
            
            const card = document.createElement('div');
            card.className = 'deal-card';
            
            // Get a placeholder image URL or use the actual image if available
            const imageUrl = deal.image_url || getPlaceholderImage(deal.subcategory);
            
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
            
            const profitPercentage = deal.profitPercentage.toFixed(0);
            
            // Get confidence color
            const confidenceColor = getConfidenceColor(deal.confidence);
            
            card.innerHTML = `
                <div class="card-favorite ${isFavorite ? 'active' : ''}" data-id="${index}">
                    <i class="fas ${isFavorite ? 'fa-heart' : 'fa-heart'}"></i>
                </div>
                <div class="card-image">
                    <img src="${imageUrl}" alt="${deal.title}">
                </div>
                <div class="card-content">
                    <div class="card-header">
                        <h3 class="card-title">${deal.title}</h3>
                        <span class="confidence-badge" style="background-color: ${confidenceColor}">
                            ${deal.confidence}% Confidence
                        </span>
                    </div>
                    <div class="card-prices">
                        <div class="price-box buy-box">
                            <div class="price-label">Buy for:</div>
                            <div class="price-value buy-price">${buyPrice}</div>
                        </div>
                        <div class="price-box sell-box">
                            <div class="price-label">Sell for:</div>
                            <div class="price-value sell-price">${sellPrice}</div>
                        </div>
                    </div>
                    <div class="card-profit">
                        <div class="profit-amount">Profit: ${profit}</div>
                        <div class="profit-percentage">${profitPercentage}% ROI</div>
                    </div>
                    <div class="card-actions">
                        <a href="${deal.buyLink}" target="_blank" class="card-btn buy-btn">
                            <i class="fas fa-shopping-cart"></i> Buy
                        </a>
                        <a href="${deal.sellLink}" target="_blank" class="card-btn sell-btn">
                            <i class="fas fa-tag"></i> Sell
                        </a>
                    </div>
                    <div class="card-info">
                        <i class="fas fa-tag"></i> ${getCategoryIcon(deal.subcategory)} ${deal.subcategory}
                    </div>
                </div>
            `;
            
            dealList.appendChild(card);
            
            // Add favorite functionality
            const favoriteBtn = card.querySelector('.card-favorite');
            favoriteBtn.addEventListener('click', function() {
                const dealId = this.getAttribute('data-id');
                toggleFavorite(deals[dealId], this);
            });
        });
    }
    
    // Toggle favorite status
    function toggleFavorite(deal, element) {
        if (!isLoggedIn) {
            // Show login modal if not logged in
            showModal(loginModal);
            return;
        }
        
        const index = userFavorites.findIndex(fav => 
            fav.buyLink === deal.buyLink && fav.sellLink === deal.sellLink
        );
        
        if (index === -1) {
            // Add to favorites
            userFavorites.push(deal);
            element.classList.add('active');
            element.querySelector('i').className = 'fas fa-heart';
        } else {
            // Remove from favorites
            userFavorites.splice(index, 1);
            element.classList.remove('active');
            element.querySelector('i').className = 'fas fa-heart';
        }
        
        // Save to localStorage (in a real app, this would be saved to the server)
        localStorage.setItem('userFavorites', JSON.stringify(userFavorites));
    }
    
    // Get confidence color based on score
    function getConfidenceColor(confidence) {
        if (confidence >= 90) return "#4CAF50"; // Green
        if (confidence >= 80) return "#8BC34A"; // Light Green
        if (confidence >= 70) return "#FFC107"; // Amber
        return "#FF5722"; // Deep Orange
    }
    
    // Get placeholder image based on category
    function getPlaceholderImage(category) {
        const categoryMap = {
            'Laptops': 'https://via.placeholder.com/300x180.png?text=Laptop',
            'Smartphones': 'https://via.placeholder.com/300x180.png?text=Smartphone',
            'Headphones': 'https://via.placeholder.com/300x180.png?text=Headphones',
            'Sneakers': 'https://via.placeholder.com/300x180.png?text=Sneakers',
            'Pokémon': 'https://via.placeholder.com/300x180.png?text=Pokemon+Cards',
            'Magic: The Gathering': 'https://via.placeholder.com/300x180.png?text=Magic+Cards'
        };
        
        return categoryMap[category] || 'https://via.placeholder.com/300x180.png?text=Product';
    }
    
    // Get category icon
    function getCategoryIcon(category) {
        // Search through all subcategories to find the matching one
        for (const [key, value] of Object.entries(subcategories)) {
            const subcat = value.find(item => item.name === category);
            if (subcat) {
                return subcat.icon;
            }
        }
        return '🔍'; // Default icon
    }
    
    // Initialize mock statistics
    function initializeStats() {
        // Random number of listings being scanned
        const scanningCount = Math.floor(Math.random() * 500) + 100;
        scanningCountEl.innerHTML = `Scanning <b>${scanningCount}</b> listings...`;
        
        // Random number of deals found this week
        const weeklyDeals = Math.floor(Math.random() * 200) + 50;
        weeklyDealsCountEl.innerHTML = `Found <b>${weeklyDeals}</b> deals this week`;
        
        // Random number of users online
        const userCount = Math.floor(Math.random() * 100) + 20;
        userCountEl.innerHTML = `<b>${userCount}</b> users online`;
        
        // Update these values periodically
        setInterval(() => {
            updateScanningCount(Math.floor(Math.random() * 100) + 50);
        }, 10000);
    }
    
    // Update scanning count
    function updateScanningCount(count) {
        scanningCountEl.innerHTML = `Scanning <b>${count}</b> listings...`;
    }
    
    // Update weekly deals count
    function updateWeeklyDealsCount(newDeals) {
        const currentCount = parseInt(weeklyDealsCountEl.querySelector('b').textContent);
        const updatedCount = currentCount + newDeals;
        weeklyDealsCountEl.innerHTML = `Found <b>${updatedCount}</b> deals this week`;
    }
    
    // Modal functions
    function showModal(modal) {
        modal.classList.add('active');
    }
    
    function hideModal(modal) {
        modal.classList.remove('active');
    }
    
    // Event listeners for modals
    loginBtn.addEventListener('click', () => showModal(loginModal));
    signupBtn.addEventListener('click', () => showModal(signupModal));
    feedbackBtn.addEventListener('click', () => showModal(feedbackModal));
    aboutLink.addEventListener('click', () => showModal(aboutModal));
    
    // Close modal when clicking the X
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            hideModal(modal);
        });
    });
    
    // Close modal when clicking outside the content
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            hideModal(e.target);
        }
    });
    
    // Tab functionality for the about modal
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Show the selected tab pane
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Handle login form submission
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        // In a real app, this would validate with a server
        // For demo purposes, just set logged in state
        isLoggedIn = true;
        loginBtn.innerHTML = `<i class="fas fa-user"></i> ${email.split('@')[0]}`;
        signupBtn.style.display = 'none';
        
        // Close modal
        hideModal(loginModal);
        
        // Load user favorites from localStorage
        loadUserFavorites();
    });
    
    // Handle signup form submission
    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('signupName').value;
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        
        // In a real app, this would create an account on the server
        // For demo purposes, just set logged in state
        isLoggedIn = true;
        loginBtn.innerHTML = `<i class="fas fa-user"></i> ${name.split(' ')[0]}`;
        signupBtn.style.display = 'none';
        
        // Close modal
        hideModal(signupModal);
    });
    
    // Handle feedback form submission
    feedbackForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const feedbackType = document.getElementById('feedbackType').value;
        const message = document.getElementById('feedbackMessage').value;
        
        // In a real app, this would send feedback to the server
        alert('Thank you for your feedback! We appreciate your input.');
        
        // Reset the form
        this.reset();
        
        // Close modal
        hideModal(feedbackModal);
    });
    
    // Load user favorites from localStorage
    function loadUserFavorites() {
        const savedFavorites = localStorage.getItem('userFavorites');
        if (savedFavorites) {
            userFavorites = JSON.parse(savedFavorites);
        }
    }
    
    // Check if user has previously logged in (in a real app, this would validate with the server)
    function checkLoginStatus() {
        // For demo purposes, we'll just check if favorites exist
        const savedFavorites = localStorage.getItem('userFavorites');
        if (savedFavorites) {
            isLoggedIn = true;
            loginBtn.innerHTML = `<i class="fas fa-user"></i> User`;
            signupBtn.style.display = 'none';
            loadUserFavorites();
        }
    }
    
    // Check login status on page load
    checkLoginStatus();
});
