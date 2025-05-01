// Categories and subcategories data
const categories = {
    "Tech": ["Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops", "Monitors", "SSDs", "Routers", "Vintage Tech"],
    "Collectibles": ["Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards", "Comic Books", "Action Figures", "LEGO Sets"],
    "Vintage Clothing": ["Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets", "Designer Brands", "Carhartt", "Patagonia"],
    "Antiques": ["Coins", "Watches", "Cameras", "Typewriters", "Vinyl Records", "Vintage Tools", "Old Maps", "Antique Toys"],
    "Gaming": ["Consoles", "Game Controllers", "Rare Games", "Arcade Machines", "Handhelds", "Gaming Headsets", "VR Gear"],
    "Music Gear": ["Electric Guitars", "Guitar Pedals", "Synthesizers", "Vintage Amps", "Microphones", "DJ Equipment"],
    "Tools & DIY": ["Power Tools", "Hand Tools", "Welding Equipment", "Toolboxes", "Measuring Devices", "Woodworking Tools"],
    "Outdoors & Sports": ["Bikes", "Skateboards", "Scooters", "Camping Gear", "Hiking Gear", "Fishing Gear", "Snowboards"]
};

// Global variables
let selectedCategory = '';
let selectedSubcategories = [];
let currentUser = null;
let currentPlan = 'free';
let scansRemaining = 2; // Default for free plan
let scanInProgress = false;
let scanAborted = false;
let scanProgressInterval = null;

// DOM Elements
const authButtons = document.getElementById('auth-buttons');
const userMenu = document.getElementById('user-menu');
const userAvatar = document.getElementById('user-avatar');
const userDropdown = document.getElementById('user-dropdown');
const loginButton = document.getElementById('login-button');
const signupButton = document.getElementById('signup-button');
const logoutButton = document.getElementById('logout-button');
const loginModal = document.getElementById('login-modal');
const signupModal = document.getElementById('signup-modal');
const subscriptionModal = document.getElementById('subscription-modal');
const closeLogin = document.getElementById('close-login');
const closeSignup = document.getElementById('close-signup');
const closeSubscription = document.getElementById('close-subscription');
const switchToSignup = document.getElementById('switch-to-signup');
const switchToLogin = document.getElementById('switch-to-login');
const continueAsGuest = document.getElementById('continue-as-guest');
const continueAsGuestSignup = document.getElementById('continue-as-guest-signup');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const loginError = document.getElementById('login-error');
const signupError = document.getElementById('signup-error');
const loginSuccess = document.getElementById('login-success');
const signupSuccess = document.getElementById('signup-success');
const subcategoryPanel = document.getElementById('subcategory-panel');
const subcategoryGrid = document.getElementById('subcategory-grid');
const selectedCount = document.getElementById('selected-count');
const searchButton = document.getElementById('search-button');
const loadingSpinner = document.getElementById('loading-spinner');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const scanStatus = document.getElementById('scan-status');
const resultsContainer = document.getElementById('results-container');
const promoCodeInput = document.getElementById('promo-code');
const redeemButton = document.getElementById('redeem-button');
const redeemMessage = document.getElementById('redeem-message');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkAuth();
});

// Set up event listeners
function setupEventListeners() {
    // Category selection
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedCategory = this.dataset.category;
            showSubcategories(selectedCategory);
        });
    });

    // Search button
    searchButton.addEventListener('click', function() {
        if (!scanInProgress) {
            startScan();
        } else {
            // Allow aborting an in-progress scan
            abortScan();
        }
    });

    // Auth buttons
    loginButton.addEventListener('click', function() {
        loginModal.classList.add('active');
    });

    signupButton.addEventListener('click', function() {
        signupModal.classList.add('active');
    });

    // Modal close buttons
    closeLogin.addEventListener('click', function() {
        loginModal.classList.remove('active');
    });

    closeSignup.addEventListener('click', function() {
        signupModal.classList.remove('active');
    });
    
    closeSubscription.addEventListener('click', function() {
        subscriptionModal.classList.remove('active');
    });

    // Continue as guest
    continueAsGuest.addEventListener('click', function() {
        loginModal.classList.remove('active');
        setupGuestUser();
    });

    continueAsGuestSignup.addEventListener('click', function() {
        signupModal.classList.remove('active');
        setupGuestUser();
    });

    // Switch between login and signup
    switchToSignup.addEventListener('click', function() {
        loginModal.classList.remove('active');
        signupModal.classList.add('active');
    });
    
    // Add this for the subscription modal close button
    document.getElementById('close-subscription').addEventListener('click', function() {
        subscriptionModal.classList.remove('active');
    });
    
    switchToLogin.addEventListener('click', function() {
        signupModal.classList.remove('active');
        loginModal.classList.add('active');
    });

    // Form submissions
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleLogin();
    });

    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleSignup();
    });

    // User menu toggle
    userAvatar.addEventListener('click', function() {
        userDropdown.classList.toggle('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!userAvatar.contains(e.target) && !userDropdown.contains(e.target)) {
            userDropdown.classList.remove('active');
        }
    });

    // Logout
    logoutButton.addEventListener('click', function(e) {
        e.preventDefault();
        handleLogout();
    });
    
    // Subscription link
    document.querySelector('.subscription-link').addEventListener('click', function(e) {
        e.preventDefault();
        userDropdown.classList.remove('active');
        subscriptionModal.classList.add('active');
    });
    
    // Plan buttons
    document.querySelectorAll('.plan-button').forEach(button => {
        button.addEventListener('click', function() {
            const plan = this.dataset.plan;
            if (plan === currentPlan) return;
            
            updateSubscriptionPlan(plan);
        });
    });
    
    // Redeem promo code
    redeemButton.addEventListener('click', function() {
        const code = promoCodeInput.value.trim();
        if (code) {
            redeemPromoCode(code);
        }
    });

    // Listen for Escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            loginModal.classList.remove('active');
            signupModal.classList.remove('active');
            subscriptionModal.classList.remove('active');
        }
    });
}

// Handle login form submission
function handleLogin() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    // Simple validation
    if (!email || !password) {
        showLoginError('Please enter both email and password');
        return;
    }
    
    // For demo purposes, automatically log in
    setupUserFromForm(email);
    loginModal.classList.remove('active');
    showToast('Login successful!', 'success');
}

// Handle signup form submission
function handleSignup() {
    const username = document.getElementById('signup-username').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    
    // Simple validation
    if (!username || !email || !password) {
        showSignupError('Please fill out all fields');
        return;
    }
    
    if (password.length < 6) {
        showSignupError('Password must be at least 6 characters');
        return;
    }
    
    // For demo purposes, automatically create account
    setupUserFromForm(email, username);
    signupModal.classList.remove('active');
    showToast('Account created successfully!', 'success');
}

// Setup user from form data
function setupUserFromForm(email, username = null) {
    currentUser = {
        username: username || email.split('@')[0],
        email: email,
        isGuest: false
    };
    
    localStorage.setItem('user', JSON.stringify(currentUser));
    updateUIForLoggedInUser();
    currentPlan = 'free';
    scansRemaining = 5;
}

// Setup guest user
function setupGuestUser() {
    currentUser = {
        username: 'Guest',
        email: 'guest@example.com',
        isGuest: true
    };
    
    localStorage.setItem('user', JSON.stringify(currentUser));
    updateUIForLoggedInUser();
    currentPlan = 'free';
    scansRemaining = 5;
    showToast('Logged in as guest', 'success');
}

// Show login error
function showLoginError(message) {
    loginError.textContent = message;
    loginError.style.display = 'block';
    
    setTimeout(() => {
        loginError.style.display = 'none';
    }, 3000);
}

// Show signup error
function showSignupError(message) {
    signupError.textContent = message;
    signupError.style.display = 'block';
    
    setTimeout(() => {
        signupError.style.display = 'none';
    }, 3000);
}

// Check if user is logged in
function checkAuth() {
    const userData = localStorage.getItem('user');
    const userPlan = localStorage.getItem('plan');
    
    if (userData) {
        try {
            currentUser = JSON.parse(userData);
            if (userPlan) {
                currentPlan = userPlan;
                if (currentPlan === 'free') {
                    scansRemaining = 5;
                } else if (currentPlan === 'premium') {
                    scansRemaining = 10;
                } else if (currentPlan === 'pro') {
                    scansRemaining = 999; // Unlimited
                }
            }
            updateUIForLoggedInUser();
        } catch (e) {
            console.error('Error parsing user data:', e);
            localStorage.removeItem('user');
            localStorage.removeItem('plan');
        }
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    if (currentUser) {
        // Show user menu, hide auth buttons
        authButtons.style.display = 'none';
        userMenu.style.display = 'block';
        
        // Set avatar text to first letter of username
        if (currentUser.username) {
            userAvatar.textContent = currentUser.username.charAt(0).toUpperCase();
        }
    } else {
        // Show auth buttons, hide user menu
        authButtons.style.display = 'flex';
        userMenu.style.display = 'none';
    }
}

// Update subscription plan
function updateSubscriptionPlan(plan) {
    currentPlan = plan;
    localStorage.setItem('plan', plan);
    
    // Update scans remaining based on plan
    if (plan === 'free') {
        scansRemaining = 5;
    } else if (plan === 'premium') {
        scansRemaining = 10;
    } else if (plan === 'pro') {
        scansRemaining = 999; // Unlimited
    }
    
    // Update UI
    updatePlanButtons();
    showToast(`Successfully upgraded to ${plan.charAt(0).toUpperCase() + plan.slice(1)} plan!`, 'success');
    subscriptionModal.classList.remove('active');
}

// Update plan buttons based on current plan
function updatePlanButtons() {
    document.querySelectorAll('.plan-button').forEach(button => {
        const plan = button.dataset.plan;
        
        if (plan === currentPlan) {
            button.textContent = 'Current Plan';
            button.disabled = true;
            button.style.opacity = '0.7';
            button.style.cursor = 'not-allowed';
        } else {
            button.textContent = 'Upgrade';
            button.disabled = false;
            button.style.opacity = '1';
            button.style.cursor = 'pointer';
        }
    });
}

// Redeem promo code - handle special code "SEAPREP"
function redeemPromoCode(code) {
    if (code.toLowerCase() === 'seaprep') {
        // Grant Pro access
        currentPlan = 'pro';
        localStorage.setItem('plan', 'pro');
        scansRemaining = 999; // Unlimited
        
        // Show success message
        redeemMessage.textContent = 'Success! You now have unlimited scans with the Pro plan.';
        redeemMessage.className = 'redeem-message success';
        redeemMessage.style.display = 'block';
        
        // Clear input
        promoCodeInput.value = '';
        
        // Update UI
        updatePlanButtons();
        showToast('Promo code successfully redeemed! Welcome to the Pro plan.', 'success');
    } else {
        // Show error message
        redeemMessage.textContent = 'Invalid promo code. Please try again.';
        redeemMessage.className = 'redeem-message error';
        redeemMessage.style.display = 'block';
        
        setTimeout(() => {
            redeemMessage.style.display = 'none';
        }, 3000);
    }
}

// Handle logout
function handleLogout() {
    // Clear stored data
    localStorage.removeItem('user');
    localStorage.removeItem('plan');
    
    // Reset current user
    currentUser = null;
    currentPlan = 'free';
    
    // Update UI
    updateUIForLoggedInUser();
    
    // Close dropdown
    userDropdown.classList.remove('active');
    
    // Show success toast
    showToast('You have been logged out successfully', 'success');
}

// Show subcategories for selected category
function showSubcategories(category) {
    const subcats = categories[category];
    if (!subcats) return;
    
    subcategoryGrid.innerHTML = '';
    subcats.forEach(subcategory => {
        const chip = document.createElement('div');
        chip.className = 'subcategory-chip';
        chip.textContent = subcategory;
        chip.addEventListener('click', () => toggleSubcategory(chip, subcategory));
        subcategoryGrid.appendChild(chip);
    });
    
    subcategoryPanel.style.display = 'block';
    selectedSubcategories = [];
    updateSelectedCount();
    updateSearchButton();

    // Scroll to subcategories
    subcategoryPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Toggle subcategory selection
function toggleSubcategory(chip, subcategory) {
    if (chip.classList.contains('selected')) {
        chip.classList.remove('selected');
        selectedSubcategories = selectedSubcategories.filter(s => s !== subcategory);
    } else {
        chip.classList.add('selected');
        selectedSubcategories.push(subcategory);
    }
    updateSelectedCount();
    updateSearchButton();
}

// Update selected count
function updateSelectedCount() {
    selectedCount.textContent = `${selectedSubcategories.length} subcategories selected`;
}

// Update search button state
function updateSearchButton() {
    if (selectedSubcategories.length > 0) {
        searchButton.classList.add('active');
        searchButton.disabled = false;
    } else {
        searchButton.classList.remove('active');
        searchButton.disabled = true;
    }
}

// Start scan function with real-time progress updates
function startScan() {
    // Check if category and subcategories are selected
    if (!selectedCategory || selectedSubcategories.length === 0) {
        showToast('Please select a category and at least one subcategory', 'error');
        return;
    }
    
    // Set scan in progress flag
    scanInProgress = true;
    scanAborted = false;
    
    // Clear previous results and show loading indicators
    resultsContainer.innerHTML = '';
    loadingSpinner.style.display = 'block';
    progressContainer.style.display = 'block';
    scanStatus.style.display = 'block';
    scanStatus.textContent = 'Initializing scan...';
    progressBar.style.width = '0%';
    
    // Update search button to be an abort button
    searchButton.textContent = 'Cancel Scan';
    searchButton.classList.add('loading');
    
    // Create the API request data
    const requestData = {
        category: selectedCategory,
        subcategories: selectedSubcategories
    };
    
    // Set up the API request with fetch
    scanWithProgressUpdates(requestData);
}

// Abort current scan
function abortScan() {
    scanAborted = true;
    scanInProgress = false;
    
    // Clear any progress interval
    if (scanProgressInterval) {
        clearInterval(scanProgressInterval);
        scanProgressInterval = null;
    }
    
    // Reset search button
    searchButton.textContent = 'Begin Resale Search';
    searchButton.classList.remove('loading');
    
    // Update status
    scanStatus.textContent = 'Scan cancelled by user';
    scanStatus.style.color = 'var(--primary-color)';
    
    // Hide loader after a short delay
    setTimeout(() => {
        loadingSpinner.style.display = 'none';
        progressContainer.style.display = 'none';
        scanStatus.style.display = 'none';
        scanStatus.style.color = 'var(--text-color)';
    }, 1500);
    
    showToast('Scan cancelled', 'error');
}

// Scan with progress updates (improved to show results)
function scanWithProgressUpdates(requestData) {
    // Simulate a multi-step scanning process
    const totalSteps = 100;
    let currentStep = 0;
    
    // Messages for different scanning stages
    const stageMessages = [
        { step: 0, message: 'Initializing marketplaces scanners...' },
        { step: 5, message: 'Connecting to Amazon...' },
        { step: 10, message: 'Connecting to eBay...' },
        { step: 15, message: 'Connecting to Facebook Marketplace...' },
        { step: 20, message: 'Connecting to other marketplaces...' },
        { step: 25, message: `Scanning for ${selectedSubcategories.join(', ')}...` },
        { step: 60, message: 'Finding matching products across platforms...' },
        { step: 80, message: 'Calculating potential profits...' },
        { step: 90, message: 'Preparing results...' },
        { step: 95, message: 'Finalizing scan...' }
    ];
    
    // Set up a progress interval to provide UI feedback
    scanProgressInterval = setInterval(() => {
        if (scanAborted) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
            return;
        }
        
        // Increment progress
        currentStep += Math.floor(Math.random() * 3) + 1;
        const progress = Math.min(currentStep, 95); // Cap at 95% until we get results
        
        // Update progress bar
        progressBar.style.width = `${progress}%`;
        
        // Update message based on current step
        for (let i = stageMessages.length - 1; i >= 0; i--) {
            if (progress >= stageMessages[i].step) {
                scanStatus.textContent = stageMessages[i].message;
                break;
            }
        }
        
        // Stop at 95% and wait for API response
        if (progress >= 95) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
        }
    }, 300);
    
    // Make the actual API call
    fetch('/api/v1/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || 'guest-token')
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // Clear progress interval if it's still running
        if (scanProgressInterval) {
            clearInterval(scanProgressInterval);
            scanProgressInterval = null;
        }
        
        // Complete the progress bar
        progressBar.style.width = '100%';
        
        if (!response.ok) {
            throw new Error('Failed to connect to scanning service');
        }
        
        return response.json();
    })
    .then(data => {
        // Process and display results
        setTimeout(() => {
            displayResults(data);
            
            // Reset scan state
            scanInProgress = false;
            searchButton.textContent = 'Begin Resale Search';
            searchButton.classList.remove('loading');
            
            // Hide loading indicators
            loadingSpinner.style.display = 'none';
            progressContainer.style.display = 'none';
            scanStatus.style.display = 'none';
        }, 500);
    })
    .catch(error => {
        console.error('Scan error:', error);
        
        // Reset scan state
        scanInProgress = false;
        searchButton.textContent = 'Begin Resale Search';
        searchButton.classList.remove('loading');
        
        // Hide loading indicators
        loadingSpinner.style.display = 'none';
        progressContainer.style.display = 'none';
        
        // Show error message
        scanStatus.textContent = 'Error connecting to scanning service. Please try again later.';
        scanStatus.style.color = 'var(--primary-color)';
        scanStatus.style.display = 'block';
        
        setTimeout(() => {
            scanStatus.style.display = 'none';
            scanStatus.style.color = 'var(--text-color)';
        }, 5000);
    });
}

// Display results from the scan
function displayResults(results) {
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    if (!results || results.length === 0) {
        const noResults = document.createElement('div');
        noResults.style.textAlign = 'center';
        noResults.style.padding = '40px 20px';
        noResults.style.background = 'var(--card-bg)';
        noResults.style.borderRadius = '15px';
        noResults.style.marginTop = '30px';
        
        noResults.innerHTML = `
            <div style="font-size: 3em; margin-bottom: 20px;">😢</div>
            <h3>No Opportunities Found</h3>
            <p>Try selecting different subcategories or come back later for new listings.</p>
        `;
        
        resultsContainer.appendChild(noResults);
        return;
    }
    
    // Create results header
    const resultsHeader = document.createElement('div');
    resultsHeader.style.background = 'var(--card-bg)';
    resultsHeader.style.padding = '20px';
    resultsHeader.style.borderRadius = '15px';
    resultsHeader.style.marginBottom = '20px';
    resultsHeader.innerHTML = `
        <h2>Found ${results.length} Opportunities</h2>
        <p>Category: ${selectedCategory} • Subcategories: ${selectedSubcategories.join(', ')}</p>
    `;
    
    resultsContainer.appendChild(resultsHeader);
    
    // Create result cards for each opportunity
    results.forEach(result => {
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        // Create image element if available
        let imageHtml = '';
        if (result.image_url) {
            imageHtml = `<img src="${result.image_url}" alt="${result.title || result.buyTitle}" class="result-image">`;
        } else if (result.buyImage_url) {
            imageHtml = `<img src="${result.buyImage_url}" alt="${result.title || result.buyTitle}" class="result-image">`;
        }
        
        // Prepare the display values
        const title = result.title || result.buyTitle || '';
        const buyPrice = result.buyPrice || result.price || 0;
        const sellPrice = result.sellPrice || result.sell_price || 0;
        const profit = result.netProfit || result.profit || (sellPrice - buyPrice);
        const profitPercentage = result.netProfitPercentage || result.profitPercentage || (profit * 100 / buyPrice);
        const buyLink = result.buyLink || result.buy_link || '#';
        const sellLink = result.sellLink || result.sell_link || '#';
        const buyMarketplace = result.buyMarketplace || result.buy_marketplace || 'Unknown';
        const sellMarketplace = result.sellMarketplace || result.sell_marketplace || 'Unknown';
        const subcategory = result.subcategory || selectedSubcategories[0];
        const confidence = result.confidence || result.similarity_score || 85;
        
        // Calculate tax (8% of buy price)
        const tax = buyPrice * 0.08;
        
        // Calculate platform fee (default 10%)
        const platformFee = result.platformFee || sellPrice * 0.1;
        
        // Calculate shipping
        const shipping = result.buyShipping || 0;
        
        // Calculate net profit
        const netProfit = result.netProfit || (profit - tax - platformFee);
        
        // Calculate ROI
        const roi = (netProfit / (buyPrice + tax + shipping)) * 100;
        
        resultCard.innerHTML = `
            ${imageHtml}
            <div class="result-details">
                <div class="profit-badge">$${profit.toFixed(2)} profit</div>
                <h3>${title}</h3>
                <p>Buy for: $${buyPrice.toFixed(2)} from ${buyMarketplace} | Sell for: $${sellPrice.toFixed(2)} on ${sellMarketplace}</p>
                <p>ROI: ${profitPercentage.toFixed(1)}% | Net Profit: $${netProfit.toFixed(2)} | Similarity Confidence: ${confidence}%</p>
                <p>Category: ${selectedCategory} > ${subcategory}</p>
                <p>Tax: $${tax.toFixed(2)} | Platform Fee: $${platformFee.toFixed(2)} | Shipping: $${shipping.toFixed(2)}</p>
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <a href="${buyLink}" target="_blank" style="
                        background: var(--primary-color);
                        color: white;
                        padding: 8px 15px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                    ">Buy Now</a>
                    <a href="${sellLink}" target="_blank" style="
                        background: var(--secondary-color);
                        color: white;
                        padding: 8px 15px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                    ">View Listing</a>
                </div>
            </div>
        `;
        
        resultsContainer.appendChild(resultCard);
    });
    
    // Scroll to results
    resultsHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Show toast notification
function showToast(message, type = 'error') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(toast => {
        document.body.removeChild(toast);
    });
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    // Add to document
    document.body.appendChild(toast);
    
    // Remove after delay
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 500);
    }, 3000);
}
