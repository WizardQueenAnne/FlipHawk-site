document.addEventListener('DOMContentLoaded', () => {
  const categorySelect = document.getElementById('category');
  const subcategoriesDiv = document.getElementById('subcategories');
  const runScanButton = document.getElementById('runScan');
  const resultsContainer = document.getElementById('results');
  const dealCountDisplay = document.getElementById('deal-count');
  const feedbackModal = document.getElementById('feedbackModal');
  const feedbackBtn = document.getElementById('feedbackBtn');
  const closeFeedback = document.getElementById('closeFeedback');
  const submitFeedback = document.getElementById('submitFeedback');

  // Category → Subcategories mapping
  const subcategoriesMap = {
    'Tech': ['Laptops', 'Smartphones', 'Headphones', 'Gaming Consoles', 'Computer Parts'],
    'Collectibles': ['Action Figures', 'Comic Books', 'Coins', 'Vintage Toys', 'Autographs'],
    'Vintage Clothing': ['Denim', 'T-Shirts', 'Jackets', 'Dresses', 'Band Merch'],
    'Sneakers': ['Jordans', 'Nike', 'Adidas', 'Yeezys', 'Converse']
  };

  // Generate subcategory checkboxes
  categorySelect.addEventListener('change', () => {
    const category = categorySelect.value;
    subcategoriesDiv.innerHTML = '';

    if (subcategoriesMap[category]) {
      subcategoriesMap[category].forEach((sub, idx) => {
        const label = document.createElement('label');
        label.className = 'checkbox';

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.value = sub;
        input.id = `sub-${idx}`;

        const span = document.createElement('span');
        span.textContent = sub;

        label.appendChild(input);
        label.appendChild(span);
        subcategoriesDiv.appendChild(label);
      });
    }
  });

  // Run scan
  runScanButton.addEventListener('click', () => {
    const selectedCategory = categorySelect.value;
    const selectedSubs = [...subcategoriesDiv.querySelectorAll('input[type="checkbox"]:checked')].map(cb => cb.value);

    if (!selectedCategory || selectedSubs.length === 0) {
      alert('Please select a category and at least one subcategory.');
      return;
    }

    dealCountDisplay.textContent = 'Scanning for deals...';
    resultsContainer.innerHTML = '';

    fetch('/run_scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category: selectedCategory,
        subcategories: selectedSubs
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        dealCountDisplay.textContent = 'Error during scan.';
        resultsContainer.innerHTML = `<p class="error-message">${data.error}</p>`;
        return;
      }

      if (data.length === 0) {
        dealCountDisplay.textContent = 'No deals found.';
        resultsContainer.innerHTML = '<p class="no-results">No arbitrage opportunities found. Try different subcategories.</p>';
        return;
      }

      dealCountDisplay.textContent = `${data.length} deal${data.length > 1 ? 's' : ''} found`;

      data.forEach(deal => {
        const card = document.createElement('div');
        card.className = 'deal-card';

        const profitColor = getConfidenceColor(deal.confidence);

        card.innerHTML = `
          <div class="deal-title">
            <h3>${deal.title}</h3>
            <span class="confidence" style="background-color: ${profitColor};">${deal.confidence}% Confidence</span>
          </div>
          <div class="deal-body">
            <div class="deal-image">
              <img src="${deal.image || 'https://via.placeholder.com/120'}" alt="Item Image">
            </div>
            <div class="deal-info">
              <p><strong>Buy for:</strong> $${deal.buyPrice}</p>
              <p><strong>Sell for:</strong> $${deal.sellPrice}</p>
              <p><strong>Profit:</strong> $${deal.profit} (${deal.profitPercentage.toFixed(1)}%)</p>
              <p><strong>Category:</strong> ${deal.subcategory}</p>
            </div>
            <div class="deal-links">
              <a href="${deal.buyLink}" target="_blank" class="deal-btn buy-btn">Buy Listing</a>
              <a href="${deal.sellLink}" target="_blank" class="deal-btn sell-btn">Sell Listing</a>
            </div>
          </div>
        `;
        resultsContainer.appendChild(card);
      });
    })
    .catch(err => {
      dealCountDisplay.textContent = 'Scan failed.';
      resultsContainer.innerHTML = `<p class="error-message">Error: ${err.message}</p>`;
    });
  });

  function getConfidenceColor(conf) {
    if (conf >= 90) return '#4CAF50';       // Green
    if (conf >= 80) return '#8BC34A';       // Lime Green
    if (conf >= 70) return '#FFC107';       // Amber
    return '#FF5722';                       // Red/Orange
  }

  // Feedback Modal
  feedbackBtn.addEventListener('click', () => feedbackModal.classList.remove('hidden'));
  closeFeedback.addEventListener('click', () => feedbackModal.classList.add('hidden'));
  submitFeedback.addEventListener('click', () => {
    const feedbackText = document.getElementById('feedbackText').value;
    if (!feedbackText) {
      alert('Please enter some feedback.');
      return;
    }
    feedbackModal.classList.add('hidden');
    alert('Thank you for your feedback!');
    document.getElementById('feedbackText').value = '';
    // In real implementation, send feedback to backend or Discord webhook
  });
});
