# FlipHawk - Marketplace Arbitrage System

FlipHawk is an advanced AI-powered marketplace arbitrage system that helps users find profitable product flipping opportunities across multiple online marketplaces like eBay, Amazon, Etsy, and Facebook Marketplace.

## 🌟 Features

### Core Functionality
- **Advanced AI Matching**: Uses NLP and machine learning to identify identical products across different listings
- **Real-time Scanning**: Fast, concurrent scanning of multiple marketplaces
- **Smart Filtering**: Advanced filters for profit, confidence, and product conditions
- **Comprehensive Analytics**: Detailed profit calculations including taxes, fees, and shipping

### User Experience
- **User Authentication**: Secure login/signup with JWT tokens
- **Subscription Tiers**: Free, Pro, and Business tiers with different features
- **Advanced Filters**: Filter by profit margin, condition, location, and more
- **Risk Assessment**: Detailed risk analysis for each opportunity
- **Historical Price Trends**: View price history and trends for items
- **Category Heatmaps**: Visualize best performing categories
- **Saved Opportunities**: Save and track promising deals
- **Analytics Dashboard**: View performance metrics and statistics

### Technical Features
- **Rate Limiting**: Intelligent API rate limiting to prevent blocking
- **Caching System**: Redis-backed caching for improved performance
- **Error Handling**: Comprehensive error tracking with Sentry integration
- **Security**: CSRF protection, secure headers, and input validation
- **Performance Monitoring**: Prometheus metrics and custom performance tracking

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Node.js (for frontend development)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/fliphawk.git
cd fliphawk
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create necessary directories
```bash
mkdir -p static/css static/js templates
```

5. Set up environment variables (create a .env file)
```
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/fliphawk
REDIS_URL=redis://localhost:6379/0
```

6. Initialize the database
```bash
flask db init
flask db migrate
flask db upgrade
```

7. Run the application
```bash
python app.py
```

## 🌐 Deployment

### Deploying to Render

1. Create a render.yaml file (already included in this repository)
2. Connect your GitHub repository to Render
3. Deploy using the "Blueprint" option and select the render.yaml file

### Docker Deployment

1. Build the Docker image
```bash
docker-compose build
```

2. Run the Docker containers
```bash
docker-compose up -d
```

## 📁 Project Structure

```
fliphawk/
├── app.py                  # Main application entry point
├── amazon_scraper.py       # Amazon marketplace scraper
├── ebay_scraper.py         # eBay marketplace scraper
├── etsy_scraper.py         # Etsy marketplace scraper
├── facebook_scraper.py     # Facebook Marketplace scraper
├── api_integration.py      # API integration utilities
├── arbitrage_api.py        # Arbitrage API endpoints
├── arbitrage_coordinator.py # Coordinates arbitrage scanning
├── auth.py                 # Authentication functionality
├── comprehensive_keywords.py # Keyword management
├── filters.py              # Filtering functionality
├── analytics.py            # Analytics functionality
├── static/                 # Static files
│   ├── css/                # CSS files
│   ├── js/                 # JavaScript files
│   └── images/             # Image assets
├── templates/              # HTML templates
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── render.yaml             # Render deployment configuration
```

## 🧑‍💻 Development

### Running Tests
```bash
pytest
```

### Code Style
We use flake8 for code linting and black for code formatting:
```bash
flake8 .
black .
```

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact
For questions or support, please contact support@fliphawk.org
