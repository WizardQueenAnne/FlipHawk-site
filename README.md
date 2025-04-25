# FlipHawk - Advanced Arbitrage Scanner 🚀

FlipHawk is a next-generation web application that helps users discover profitable resale opportunities across online marketplaces using advanced AI-powered scanning and matching algorithms.

![FlipHawk Logo](static/logo.png)

## 🌟 Features

### Core Functionality
- **Advanced AI Matching**: Uses NLP and machine learning to identify identical products across different listings
- **Real-time Scanning**: Fast, concurrent scanning of multiple marketplaces
- **Smart Filtering**: Advanced filters for profit, confidence, and product conditions
- **Comprehensive Analytics**: Detailed profit calculations including taxes, fees, and shipping

### User Experience
- **Modern Dashboard**: Interactive charts and real-time statistics
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Notifications**: Instant updates on scan progress and opportunities
- **Saved Opportunities**: Save and track promising deals for later

### Technical Features
- **Rate Limiting**: Intelligent API rate limiting to prevent blocking
- **Caching System**: Redis-backed caching for improved performance
- **Error Handling**: Comprehensive error tracking with Sentry integration
- **Security**: CSRF protection, secure headers, and input validation
- **Performance Monitoring**: Prometheus metrics and custom performance tracking

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Redis (for caching)
- PostgreSQL (recommended for production)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourorg/fliphawk.git
cd fliphawk
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
# Development
flask run

# Production
gunicorn app:app
```

## 🛠️ Configuration

### Environment Variables
- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Flask secret key
- `SENTRY_DSN`: Sentry error tracking DSN
- `RATE_LIMIT`: API rate limit configuration

### Database Setup
The application supports both SQLite (development) and PostgreSQL (production):

```python
# SQLite (development)
DATABASE_URL=sqlite:///fliphawk.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/fliphawk
```

## 📚 API Documentation

### Endpoints

#### Scanning
- `POST /api/v1/scan`: Run an arbitrage scan
- `GET /api/v1/stats`: Get application statistics
- `GET /api/v1/health`: Health check endpoint

#### User Data
- `POST /api/v1/save_opportunity`: Save an opportunity
- `GET /api/v1/my_opportunities`: Get saved opportunities

For detailed API documentation, visit `/api/docs` when running the application.

## 🧪 Testing

Run the test suite:
```bash
pytest

# With coverage
pytest --cov=app tests/
```

## 🚀 Deployment

### Docker Deployment
```bash
docker build -t fliphawk .
docker run -p 5000:5000 fliphawk
```

### Render Deployment
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy!

## 🔧 Development

### Code Style
We use Black for code formatting and Flake8 for linting:
```bash
black .
flake8 .
```

### Type Checking
Run mypy for type checking:
```bash
mypy app
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📈 Performance Optimization

- **Caching**: Results are cached for 5 minutes to reduce API calls
- **Concurrent Requests**: Async scanning for faster results
- **Database Indexing**: Optimized queries for fast data retrieval
- **Compression**: Gzip compression for reduced bandwidth usage

## 🔒 Security

- CSRF protection with Flask-WTF
- Rate limiting to prevent abuse
- Input validation and sanitization
- Secure session management
- Regular security audits

## 🤝 Support

- Documentation: [docs.fliphawk.com](https://docs.fliphawk.com)
- Issues: [GitHub Issues](https://github.com/yourorg/fliphawk/issues)
- Email: support@fliphawk.com

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask for the web framework
- BeautifulSoup for web scraping
- Recharts for data visualization
- All our contributors and users

---

Made with ❤️ by the FlipHawk Team
