# FlipHawk Arbitrage Finder

FlipHawk is a web application that helps users find arbitrage opportunities across online marketplaces. It's designed to identify items that can be purchased at a lower price and sold at a higher price for profit.

![FlipHawk Logo](static/logo.png)

## Features

- **Dynamic Deal Cards**: Results display as stylish cards with item images, prices, profit margin, confidence percentages, and direct links to listings.
- **Real-time Stats**: Track scanning activity, weekly deals found, and active users on the platform.
- **User Accounts**: Create an account to save favorite arbitrage opportunities and track them over time.
- **Category Icons**: Visual cues make it easier to identify product categories and subcategories.
- **Confidence Scoring**: Color-coded confidence scores (green = high, yellow = medium, red = low) help users evaluate opportunities at a glance.
- **Mobile Responsive**: Works beautifully on both desktop and mobile devices with optimized UI for all screen sizes.
- **Feedback System**: Built-in chat/feedback button allows users to report issues or suggest improvements.
- **Transparency**: Detailed explanation of how the arbitrage algorithm works and how confidence scores are calculated.

## How It Works

1. **Select a Category**: Choose from Tech, Collectibles, Antiques, Trading Cards, Vintage Clothing, or Shoes.

2. **Select Subcategories**: For each category, you can select multiple subcategories to search for arbitrage opportunities.

3. **Find Deals**: The application scans online marketplaces (currently eBay) for price discrepancies of similar items.

4. **View Opportunities**: Results display the item details, buy price, sell price, potential profit, and confidence score.

5. **Take Action**: Click on the Buy or Sell buttons to go directly to the marketplace listings.

## The Arbitrage Algorithm

FlipHawk uses a sophisticated algorithm to identify genuine arbitrage opportunities:

1. **Data Collection**: Fetches listings from eBay with different sort orders (price low-to-high and high-to-low)
2. **Item Matching**: Uses string similarity and model number matching to identify the same or similar items
3. **Opportunity Calculation**: Computes potential profit and ROI for matched items
4. **Confidence Scoring**: Assigns a confidence score based on:
   - Title similarity (80%)
   - Profit percentage (10%)
   - Condition matching (10%)
   - Model number matching (bonus points)

## Understanding Confidence Scores

- **90-100%**: High confidence - Very likely the same item with a significant price difference
- **80-89%**: Good confidence - Likely the same item with minor differences
- **70-79%**: Moderate confidence - Similar items with potential differences
- **Below 70%**: Low confidence - May be different items or conditions

## Technical Details

The application consists of:

- A Flask backend (`app.py`) that serves the web interface and handles API requests
- An arbitrage bot (`arbitrage_bot.py`) that finds price discrepancies
- A responsive frontend (HTML, CSS, JavaScript) that displays the results
- User authentication and favorites system
- Real-time statistics tracking

## Deployment

The application is deployed on Render and can be accessed at your Render URL.

## Development

To run locally:

1. Clone the repository
2. Install the requirements: `pip install -r requirements.txt`
3. Run the Flask app: `python app.py`
4. Access the application at `http://localhost:5000`

## Future Enhancements

- Add support for more marketplaces (Amazon, Facebook Marketplace, etc.)
- Implement email alerts for new high-confidence opportunities
- Integrate with shipping calculators to estimate shipping costs
- Add advanced search filters by price range, condition, and location
- Implement machine learning for better item matching
- Add price history tracking for popular items

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*FlipHawk - Find Profits Fast*
