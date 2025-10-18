# Flask Trivia Dashboard

A comprehensive Flask web application that integrates with the [Open Trivia Database (OpenTDB)](https://opentdb.com/) to provide an interactive trivia quiz experience with API exploration, gameplay, and leaderboard tracking.

## 🎯 Features

- **API Explorer**: Preview JSON responses from OpenTDB with customizable parameters
- **Play Mode**: Complete trivia games with shuffled answers and progress tracking
- **Leaderboard**: Save and compare scores with other players
- **Responsive Design**: Mobile-friendly interface built with Bootstrap 5
- **Real-time Stats**: Track accuracy, time taken, and performance metrics
- **Security**: CSRF protection, input validation, and secure session management
- **Caching**: Smart API response caching with 60-second TTL
- **Error Handling**: Graceful fallbacks for API timeouts and errors

## 📸 Screenshots

### Home Page
- API Explorer with parameter controls
- Game setup form with category/difficulty selection
- Real-time JSON preview with latency display

### Question Page
- Clean question display with shuffled answers
- Progress bar showing game completion
- Category and difficulty badges
- Current score tracking

### Results Page
- Final score with accuracy percentage
- Performance grade (A-F)
- Time taken statistics
- Leaderboard submission form

### Leaderboard
- Sortable table of top scores
- Filter by difficulty level
- Rank badges (🥇🥈🥉)
- Recent game history

## 🚀 Setup and Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone or download the repository**
   ```powershell
   cd "c:\Users\Isabel Arias\OneDrive\Uni 1\programacion\programacion II\API_Trivia"
   ```

2. **Create a virtual environment (recommended)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```powershell
   Copy-Item .env.example .env
   ```
   
   Edit `.env` and set a secure `SECRET_KEY`:
   ```
   SECRET_KEY=your-very-secure-random-secret-key-here
   ```

5. **Initialize the database**
   The database will be automatically created when you first run the app.

6. **Run the application**
   ```powershell
   flask --app app run
   ```
   
   Or simply:
   ```powershell
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to: `http://127.0.0.1:5000`

## 📚 Usage

### API Explorer
1. Navigate to the home page
2. Adjust parameters (amount, category, difficulty, type)
3. Click "Preview JSON" to see the raw API response
4. View latency and caching status

### Playing a Game
1. Scroll to the "Start Game" section
2. Configure your trivia preferences:
   - **Amount**: 1-50 questions
   - **Category**: Choose from 24+ categories
   - **Difficulty**: Easy, Medium, Hard, or Any
   - **Type**: Multiple Choice, True/False, or Any
3. Click "Start Game"
4. Answer each question by selecting an option
5. Submit your answer to proceed
6. View your final results and save to leaderboard

### Leaderboard
- View top scores from all players
- Filter by difficulty level
- See accuracy percentages and dates
- Compare your performance with others

## 🔧 Configuration

### OpenTDB API Parameters

The application supports all OpenTDB query parameters:

| Parameter | Description | Values |
|-----------|-------------|--------|
| `amount` | Number of questions | 1-50 |
| `category` | Trivia category | 9-32 (see categories list) |
| `difficulty` | Question difficulty | easy, medium, hard |
| `type` | Question type | multiple, boolean |
| `encode` | Response encoding | url3986, base64 |

### Session Tokens

OpenTDB supports session tokens to prevent duplicate questions. The application can be extended to implement token management via `https://opentdb.com/api_token.php`.

### Caching Strategy

- API responses are cached in memory for 60 seconds
- Cache keys are generated from sorted parameters
- Reduces API load and improves response times
- Cached responses excluded from latency measurements

## 🧪 Testing

Run the test suite:

```powershell
pytest -q
```

Run with coverage:

```powershell
pytest --cov=. --cov-report=html
```

### Test Coverage

- Input validation (amount, difficulty, type, encode)
- HTML entity decoding
- Answer shuffling with seed
- Response code message mapping
- Database operations
- Mock API integration

## 🔒 Security Features

1. **CSRF Protection**: Flask-WTF CSRF tokens on all POST forms
2. **Input Validation**: Server-side validation of all user inputs
3. **Session Security**: HttpOnly and SameSite=Lax cookie settings
4. **Output Escaping**: Jinja2 auto-escaping prevents XSS
5. **SQL Injection**: Parameterized queries via SQLite3
6. **Rate Limiting**: Ready for implementation on API routes

### Security Best Practices

- Never commit `.env` files with real secrets
- Use strong, random `SECRET_KEY` in production
- Consider adding rate limiting middleware
- Implement HTTPS in production deployments
- Regular dependency updates for security patches

## 📁 Project Structure

```
API_Trivia/
├── app.py                  # Main Flask application with routes
├── models.py               # Database models and operations
├── utils.py                # Utility functions (validation, shuffling)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── trivia.db              # SQLite database (auto-created)
├── templates/
│   ├── base.html          # Base template with navbar
│   ├── index.html         # Home page with API explorer
│   ├── question.html      # Question display page
│   ├── results.html       # Results summary page
│   └── leaderboard.html   # Leaderboard table
├── static/
│   └── styles.css         # Custom CSS styles
└── tests/
    └── test_app.py        # Test suite
```

## 🎨 Technologies Used

- **Backend**: Flask 3.0, Python 3.8+
- **Frontend**: Bootstrap 5, Jinja2, Bootstrap Icons
- **Database**: SQLite3
- **API**: OpenTDB REST API
- **Security**: Flask-WTF, itsdangerous
- **Testing**: pytest
- **Environment**: python-dotenv

## 🔄 API Response Codes

OpenTDB uses response codes to indicate request status:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Request successful |
| 1 | No Results | Not enough questions match parameters |
| 2 | Invalid Parameter | Invalid parameter in request |
| 3 | Token Not Found | Session token doesn't exist |
| 4 | Token Empty | All questions exhausted for token |
| 5 | Rate Limit | Too many requests |

The application automatically maps these codes to user-friendly messages.

## 🐛 Troubleshooting

### Database Issues
```powershell
# Delete and recreate database
Remove-Item trivia.db
python app.py
```

### Port Already in Use
```powershell
# Use different port
flask --app app run --port 5001
```

### API Timeout Errors
- Check internet connection
- OpenTDB may be experiencing issues
- Try reducing the number of questions
- Wait a moment and retry

### Missing Dependencies
```powershell
pip install -r requirements.txt --upgrade
```

## 📈 Future Enhancements

- [ ] User authentication and profiles
- [ ] Question timer with time bonus scoring
- [ ] Multiplayer/challenge mode
- [ ] Statistics dashboard with charts
- [ ] Session token integration for unique questions
- [ ] Admin panel for leaderboard management
- [ ] Export results to PDF/CSV
- [ ] Social sharing features
- [ ] Dark mode toggle
- [ ] Progressive Web App (PWA) support

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [Open Trivia Database](https://opentdb.com/) for providing the free trivia API
- [Bootstrap](https://getbootstrap.com/) for the responsive UI framework
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) for the icon set

## 📞 Support

If you encounter any issues or have questions:
- Check the troubleshooting section
- Review the OpenTDB API documentation
- Open an issue in the repository

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenTDB API Documentation](https://opentdb.com/api_config.php)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)

---

**Happy Trivia Playing! 🎉**
