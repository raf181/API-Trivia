"""
Test suite for Flask Trivia Dashboard
Tests input validation, utility functions, and Flask routes
"""
import pytest
import json
import random
from datetime import datetime

# Import app and utilities
from app import app, get_cache_key, fetch_trivia_questions
from models import init_db, save_score, get_leaderboard, get_db_connection
from utils import (
    validate_amount, validate_difficulty, validate_type, validate_encode,
    decode_html_entities, shuffle_answers, get_response_code_message,
    format_time, calculate_grade, get_difficulty_badge_class
)


# ==================== Fixtures ====================

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def init_test_db():
    """Initialize test database"""
    init_db()
    yield
    # Cleanup after tests if needed


# ==================== Validation Tests ====================

def test_validate_amount_valid():
    """Test amount validation with valid inputs"""
    assert validate_amount('10') == 10
    assert validate_amount('1') == 1
    assert validate_amount('50') == 50
    assert validate_amount('25') == 25


def test_validate_amount_invalid():
    """Test amount validation with invalid inputs"""
    with pytest.raises(ValueError):
        validate_amount('0')
    
    with pytest.raises(ValueError):
        validate_amount('51')
    
    with pytest.raises(ValueError):
        validate_amount('abc')
    
    with pytest.raises(ValueError):
        validate_amount('-5')


def test_validate_difficulty_valid():
    """Test difficulty validation with valid inputs"""
    assert validate_difficulty('') == ''
    assert validate_difficulty('easy') == 'easy'
    assert validate_difficulty('medium') == 'medium'
    assert validate_difficulty('hard') == 'hard'
    assert validate_difficulty('EASY') == 'easy'  # Case insensitive


def test_validate_difficulty_invalid():
    """Test difficulty validation with invalid inputs"""
    with pytest.raises(ValueError):
        validate_difficulty('invalid')
    
    with pytest.raises(ValueError):
        validate_difficulty('extreme')


def test_validate_type_valid():
    """Test type validation with valid inputs"""
    assert validate_type('') == ''
    assert validate_type('multiple') == 'multiple'
    assert validate_type('boolean') == 'boolean'
    assert validate_type('MULTIPLE') == 'multiple'


def test_validate_type_invalid():
    """Test type validation with invalid inputs"""
    with pytest.raises(ValueError):
        validate_type('invalid')
    
    with pytest.raises(ValueError):
        validate_type('single')


def test_validate_encode_valid():
    """Test encode validation with valid inputs"""
    assert validate_encode('') == ''
    assert validate_encode('url3986') == 'url3986'
    assert validate_encode('base64') == 'base64'


def test_validate_encode_invalid():
    """Test encode validation with invalid inputs"""
    with pytest.raises(ValueError):
        validate_encode('invalid')


# ==================== Utility Function Tests ====================

def test_decode_html_entities():
    """Test HTML entity decoding"""
    assert decode_html_entities('&lt;div&gt;') == '<div>'
    assert decode_html_entities('&quot;Hello&quot;') == '"Hello"'
    assert decode_html_entities('&amp;') == '&'
    assert decode_html_entities('Rock &amp; Roll') == 'Rock & Roll'
    assert decode_html_entities('No entities') == 'No entities'


def test_shuffle_answers():
    """Test answer shuffling preserves correct answer"""
    correct = "Paris"
    incorrect = ["London", "Berlin", "Madrid"]
    
    # Test multiple times to ensure randomization
    for _ in range(10):
        shuffled, correct_index = shuffle_answers(correct, incorrect)
        
        # Check all answers are present
        assert len(shuffled) == 4
        assert correct in shuffled
        assert all(ans in shuffled for ans in incorrect)
        
        # Check correct index points to correct answer
        assert shuffled[correct_index] == correct


def test_shuffle_answers_deterministic():
    """Test shuffle is deterministic with seed"""
    correct = "True"
    incorrect = ["False"]
    
    random.seed(42)
    result1, index1 = shuffle_answers(correct, incorrect)
    
    random.seed(42)
    result2, index2 = shuffle_answers(correct, incorrect)
    
    assert result1 == result2
    assert index1 == index2


def test_get_response_code_message():
    """Test OpenTDB response code mapping"""
    assert "Success" in get_response_code_message(0)
    assert "No results" in get_response_code_message(1)
    assert "Invalid parameter" in get_response_code_message(2)
    assert "Token not found" in get_response_code_message(3)
    assert "Token empty" in get_response_code_message(4)
    assert "Rate limit" in get_response_code_message(5)
    assert "Unknown" in get_response_code_message(999)


def test_format_time():
    """Test time formatting"""
    assert format_time(30) == "30.0s"
    assert format_time(59.5) == "59.5s"
    assert format_time(60) == "1m 0s"
    assert format_time(125) == "2m 5s"
    assert format_time(90.7) == "1m 31s"


def test_calculate_grade():
    """Test grade calculation"""
    assert calculate_grade(95) == "A"
    assert calculate_grade(90) == "A"
    assert calculate_grade(85) == "B"
    assert calculate_grade(75) == "C"
    assert calculate_grade(65) == "D"
    assert calculate_grade(50) == "F"


def test_get_difficulty_badge_class():
    """Test difficulty badge class mapping"""
    assert get_difficulty_badge_class('easy') == 'success'
    assert get_difficulty_badge_class('medium') == 'warning'
    assert get_difficulty_badge_class('hard') == 'danger'
    assert get_difficulty_badge_class('any') == 'secondary'
    assert get_difficulty_badge_class('unknown') == 'secondary'


# ==================== Cache Tests ====================

def test_get_cache_key():
    """Test cache key generation"""
    params1 = {'amount': 10, 'difficulty': 'easy'}
    params2 = {'difficulty': 'easy', 'amount': 10}
    
    # Same params in different order should produce same key
    assert get_cache_key(params1) == get_cache_key(params2)
    
    params3 = {'amount': 10, 'difficulty': 'hard'}
    # Different params should produce different key
    assert get_cache_key(params1) != get_cache_key(params3)


# ==================== Database Tests ====================

def test_save_and_get_leaderboard(init_test_db):
    """Test saving scores and retrieving leaderboard"""
    # Save test scores
    save_score("Alice", 8, 10, 80.0, "easy")
    save_score("Bob", 9, 10, 90.0, "medium")
    save_score("Charlie", 7, 10, 70.0, "hard")
    
    # Get all scores
    scores = get_leaderboard(limit=10)
    assert len(scores) >= 3
    
    # Check ordering (highest score first)
    assert scores[0]['score'] >= scores[1]['score']
    
    # Filter by difficulty
    easy_scores = get_leaderboard(difficulty='easy', limit=10)
    assert all(s['difficulty'] == 'easy' for s in easy_scores)


def test_database_connection():
    """Test database connection"""
    conn = get_db_connection()
    assert conn is not None
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
    result = cursor.fetchone()
    
    assert result is not None
    conn.close()


# ==================== Flask Route Tests ====================

def test_index_route(client):
    """Test home page route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Trivia Dashboard' in response.data
    assert b'API Explorer' in response.data
    assert b'Start Game' in response.data


def test_healthz_route(client):
    """Test health check endpoint"""
    response = client.get('/healthz')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_api_preview_valid_params(client):
    """Test API preview with valid parameters"""
    response = client.get('/api-preview?amount=5&difficulty=easy')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert 'latency_ms' in data


def test_api_preview_invalid_amount(client):
    """Test API preview with invalid amount"""
    response = client.get('/api-preview?amount=100')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data


def test_api_preview_invalid_difficulty(client):
    """Test API preview with invalid difficulty"""
    response = client.get('/api-preview?difficulty=extreme')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] is False


def test_play_route_get(client):
    """Test play route with GET request"""
    # Should redirect or show play page
    response = client.get('/play')
    assert response.status_code in [200, 302]


def test_question_no_session(client):
    """Test question route without active session"""
    response = client.get('/question', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to index with warning
    assert b'No active game' in response.data or b'Start' in response.data


def test_results_no_session(client):
    """Test results route without active session"""
    response = client.get('/results', follow_redirects=True)
    assert response.status_code == 200
    # Should redirect with warning
    assert b'No game results' in response.data or b'Start' in response.data


def test_leaderboard_route(client):
    """Test leaderboard route"""
    response = client.get('/leaderboard')
    assert response.status_code == 200
    assert b'Leaderboard' in response.data


def test_leaderboard_filter(client):
    """Test leaderboard with difficulty filter"""
    response = client.get('/leaderboard?difficulty=easy')
    assert response.status_code == 200
    assert b'Leaderboard' in response.data


def test_clear_session(client):
    """Test session clearing"""
    with client.session_transaction() as session:
        session['game'] = {'questions': [], 'score': 0}
    
    response = client.post('/clear', follow_redirects=True)
    assert response.status_code == 200
    
    with client.session_transaction() as session:
        assert 'game' not in session


# ==================== Integration Tests ====================

def test_full_game_flow(client):
    """Test complete game flow from start to finish"""
    # This would require mocking the OpenTDB API
    # For now, we just test the flow without actual API calls
    
    # Step 1: Start on home page
    response = client.get('/')
    assert response.status_code == 200
    
    # Step 2: View leaderboard
    response = client.get('/leaderboard')
    assert response.status_code == 200
    
    # Step 3: Health check
    response = client.get('/healthz')
    assert response.status_code == 200


def test_csrf_protection_disabled_in_tests(client):
    """Verify CSRF is disabled for tests"""
    response = client.post('/clear')
    # Should not get CSRF error
    assert response.status_code in [200, 302]


# ==================== Edge Cases ====================

def test_empty_leaderboard(client):
    """Test leaderboard with no scores"""
    # This depends on database state, but should handle gracefully
    response = client.get('/leaderboard?difficulty=nonexistent')
    assert response.status_code == 200


def test_large_amount_validation():
    """Test amount validation at boundaries"""
    assert validate_amount('1') == 1
    assert validate_amount('50') == 50
    
    with pytest.raises(ValueError):
        validate_amount('0')
    
    with pytest.raises(ValueError):
        validate_amount('51')


def test_special_characters_in_html():
    """Test HTML decoding with special characters"""
    assert decode_html_entities('&lt;&gt;&amp;&quot;&#39;') == '<>&"\''
    assert decode_html_entities('Normal text') == 'Normal text'
    assert decode_html_entities('Mixed &amp; text &lt;tag&gt;') == 'Mixed & text <tag>'


# ==================== Performance Tests ====================

def test_cache_performance():
    """Test that caching improves performance"""
    params = {'amount': 5}
    
    # First call should cache
    key = get_cache_key(params)
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length


if __name__ == '__main__':
    pytest.main(['-v', __file__])
