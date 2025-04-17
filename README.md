# FlipHawk Arbitrage Finder

FlipHawk is a web application that helps users find arbitrage opportunities across online marketplaces. It's designed to identify items that can be purchased at a lower price and sold at a higher price for profit.

## How It Works

1. **Select a Category**: Choose from Tech, Collectibles, Antiques, Trading Cards, Vintage Clothing, or Shoes.

2. **Select Subcategories**: For each category, you can select multiple subcategories to search for arbitrage opportunities.

3. **Find Deals**: The application scans online marketplaces (currently eBay) for price discrepancies of similar items.

4. **View Opportunities**: Results display the item, buy price, sell price, potential profit, and confidence score.

## Features

- **Real Price Comparison**: Compares similar items across listings to find genuine arbitrage opportunities.
- **Multi-Category Support**: Search across various product categories and subcategories.
- **Confidence Scoring**: Each opportunity includes a confidence score based on title similarity and price difference.
- **Mobile Responsive**: Works well on both desktop and mobile devices.

## Technical Details

The application consists of:

- A Flask backend (`app.py`) that serves the web interface and handles API requests
- An arbitrage bot (`arbitrage_bot.py`) that finds price discrepancies
- A responsive frontend (HTML, CSS, JavaScript) that displays the results

### The Arbitrage Algorithm

1. **Data Collection**: Fetches listings from eBay with different sort orders (price low-to-high and high-to-low)
2. **Item Matching**: Uses string similarity to identify the same or similar items
3. **Opportunity Calculation**: Computes potential profit and ROI for matched items
4. **Confidence Scoring**: Assigns a confidence score based on title similarity and profit margin

## Deployment

The application is deployed on Render and can be accessed at your Render URL.

## Future Enhancements

- Add support for more marketplaces (Amazon, Facebook Marketplace, etc.)
- Implement user accounts to save favorite opportunities
- Add email alerts for new high-confidence opportunities
- Integrate with shipping calculators to estimate shipping costs

## Development

To run locally:

1. Clone the repository
2. Install the requirements: `pip install -r requirements.txt`
3. Run the Flask app: `python app.py`
4. Access the application at `http://localhost:5000`
