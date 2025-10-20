"""
Flask Trivia Dashboard - Main Application
Integrates with OpenTDB API for trivia questions
"""
import os
import time
import random
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
import requests
from dotenv import load_dotenv

from models import init_db, save_score, get_leaderboard, get_db_connection
from utils import (
    validate_amount, validate_difficulty, validate_type, validate_encode,
    decode_html_entities, shuffle_answers, get_response_code_message,
    validate_mixed_difficulty
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CSRF Protection
csrf = CSRFProtect(app)

# Initialize database
init_db()

# OpenTDB API Configuration
OPENTDB_BASE_URL = 'https://opentdb.com/api.php'
OPENTDB_TOKEN_URL = 'https://opentdb.com/api_token.php'
API_TIMEOUT = 3  # seconds - fail fast for better UX
API_RETRIES = 1  # retry attempts - one retry only
API_BACKOFF = 0.3  # seconds - minimal backoff

# Simple in-memory cache for API responses
api_cache = {}
cache_timestamps = {}
CACHE_TTL = 300  # seconds (5 minutes) - increased for better performance


def get_cache_key(params):
    """Generate cache key from sorted parameters"""
    sorted_params = sorted(params.items())
    key_string = json.dumps(sorted_params, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cached_response(cache_key):
    """Get cached response if still valid"""
    if cache_key in api_cache:
        timestamp = cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp < CACHE_TTL:
            return api_cache[cache_key]
    return None


def set_cached_response(cache_key, response):
    """Store response in cache"""
    api_cache[cache_key] = response
    cache_timestamps[cache_key] = time.time()


def fetch_trivia_questions(params, use_cache=True):
    """
    Fetch questions from OpenTDB API with retry logic
    Returns: (success: bool, data: dict, latency_ms: float)
    """
    # Check cache first
    cache_key = get_cache_key(params)
    if use_cache:
        cached = get_cached_response(cache_key)
        if cached:
            return True, cached, 0
    
    start_time = time.time()
    last_error = None
    
    for attempt in range(API_RETRIES + 1):
        try:
            response = requests.get(
                OPENTDB_BASE_URL,
                params=params,
                timeout=API_TIMEOUT
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache successful responses
                if data.get('response_code') == 0:
                    set_cached_response(cache_key, data)
                
                return True, data, latency_ms
            elif response.status_code == 429:
                # Rate limited - don't retry immediately
                last_error = 'Rate limited by API'
                break  # Stop trying
            else:
                last_error = f'HTTP {response.status_code}'
                break  # Don't retry HTTP errors
            
        except requests.Timeout:
            last_error = 'Request timeout'
            # Apply backoff before retry
            if attempt < API_RETRIES:
                time.sleep(API_BACKOFF)
            continue
        
        except requests.ConnectionError:
            last_error = 'Connection error'
            # Apply backoff before retry
            if attempt < API_RETRIES:
                time.sleep(API_BACKOFF)
            continue
            
        except requests.RequestException as e:
            last_error = str(e)
            break  # Don't retry other exceptions
    
    return False, {'error': last_error or 'Max retries exceeded'}, (time.time() - start_time) * 1000


def fetch_mixed_difficulty_questions(difficulty_counts, category='', q_type='', encode=''):
    """
    Fetch questions from multiple difficulty levels in parallel and combine them
    
    Args:
        difficulty_counts: Dict with 'easy', 'medium', 'hard' counts
        category: Category ID (optional)
        q_type: Question type (optional)
        encode: Encoding type (optional)
    
    Returns:
        Tuple of (success: bool, combined_questions: list, error_message: str)
    """
    all_questions = []
    errors = []
    
    # Prepare all API requests
    fetch_tasks = []
    for difficulty in ['easy', 'medium', 'hard']:
        count = difficulty_counts.get(difficulty, 0)
        if count == 0:
            continue
        
        # Build params for this difficulty
        params = {
            'amount': count,
            'difficulty': difficulty
        }
        
        if q_type:
            params['type'] = q_type
        if encode:
            params['encode'] = encode
        if category:
            try:
                params['category'] = int(category)
            except ValueError:
                pass
        
        fetch_tasks.append((difficulty, count, params))
    
    # Fetch all difficulties in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all fetch tasks - enable cache for speed
        future_to_difficulty = {
            executor.submit(fetch_trivia_questions, params, True): (difficulty, count)
            for difficulty, count, params in fetch_tasks
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_difficulty):
            difficulty, count = future_to_difficulty[future]
            try:
                success, data, latency_ms = future.result()
                
                if not success:
                    error_msg = f"Failed to fetch {difficulty} questions: {data.get('error', 'Unknown error')}"
                    errors.append(error_msg)
                    continue
                
                if data.get('response_code') != 0:
                    message = get_response_code_message(data.get('response_code'))
                    error_msg = f"API Error for {difficulty} questions: {message}"
                    errors.append(error_msg)
                    continue
                
                questions = data.get('results', [])
                if len(questions) < count:
                    error_msg = f"Not enough {difficulty} questions available (requested {count}, got {len(questions)})"
                    errors.append(error_msg)
                    # Use what we got instead of failing completely
                    if questions:
                        all_questions.extend(questions)
                    continue
                
                all_questions.extend(questions)
                
            except Exception as e:
                error_msg = f"Exception fetching {difficulty} questions: {str(e)}"
                errors.append(error_msg)
    
    # If we got at least some questions, consider it a partial success
    if all_questions:
        # Shuffle the combined questions to mix difficulties
        random.shuffle(all_questions)
        
        if errors:
            # Warn about partial success
            warning = f"Got {len(all_questions)} questions, but some requests failed: {'; '.join(errors)}"
            return True, all_questions, warning
        
        return True, all_questions, ''
    
    # Complete failure
    if errors:
        return False, [], ' | '.join(errors)
    
    return False, [], 'No questions could be fetched'


@app.route('/')
def index():
    """Landing page with API explorer and play setup"""
    return render_template('index.html')


@app.route('/api-preview')
def api_preview():
    """Preview API response with validation and caching"""
    # Validate and collect parameters
    try:
        amount = validate_amount(request.args.get('amount', '10'))
        difficulty = validate_difficulty(request.args.get('difficulty', ''))
        q_type = validate_type(request.args.get('type', ''))
        encode = validate_encode(request.args.get('encode', ''))
        category = request.args.get('category', '')
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    # Build API parameters
    params = {'amount': amount}
    if difficulty:
        params['difficulty'] = difficulty
    if q_type:
        params['type'] = q_type
    if encode:
        params['encode'] = encode
    if category:
        try:
            params['category'] = int(category)
        except ValueError:
            pass
    
    # Fetch from API
    success, data, latency_ms = fetch_trivia_questions(params)
    
    return jsonify({
        'success': success,
        'data': data,
        'latency_ms': round(latency_ms, 2),
        'cached': get_cache_key(params) in api_cache
    })


@app.route('/play', methods=['GET', 'POST'])
def play():
    """Initialize game session"""
    if request.method == 'POST':
        # Check if mixed difficulty mode
        difficulty_mode = request.form.get('difficulty_mode', 'single')
        
        if difficulty_mode == 'mixed':
            # Handle mixed difficulty
            try:
                easy_count = request.form.get('easy_count', '0')
                medium_count = request.form.get('medium_count', '0')
                hard_count = request.form.get('hard_count', '0')
                
                difficulty_counts = validate_mixed_difficulty(easy_count, medium_count, hard_count)
                
                q_type = validate_type(request.form.get('type', ''))
                encode = validate_encode(request.form.get('encode', ''))
                category = request.form.get('category', '')
                
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('index'))
            
            # Fetch mixed difficulty questions
            success, questions, error_msg = fetch_mixed_difficulty_questions(
                difficulty_counts, category, q_type, encode
            )
            
            if not success:
                flash(error_msg, 'danger')
                return redirect(url_for('index'))
            
            # Show warning if partial success
            if error_msg:
                flash(f'Warning: {error_msg}', 'warning')
            
            # Store params for session
            params = {
                'difficulty': 'mixed',
                'easy': difficulty_counts['easy'],
                'medium': difficulty_counts['medium'],
                'hard': difficulty_counts['hard']
            }
            if q_type:
                params['type'] = q_type
            if category:
                params['category'] = category
        else:
            # Handle single difficulty (original behavior)
            try:
                amount = validate_amount(request.form.get('amount', '10'))
                difficulty = validate_difficulty(request.form.get('difficulty', ''))
                q_type = validate_type(request.form.get('type', ''))
                encode = validate_encode(request.form.get('encode', ''))
                category = request.form.get('category', '')
                
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('index'))
            
            # Build API parameters
            params = {'amount': amount}
            if difficulty:
                params['difficulty'] = difficulty
            if q_type:
                params['type'] = q_type
            if encode:
                params['encode'] = encode
            if category:
                try:
                    params['category'] = int(category)
                except ValueError:
                    pass
            
            # Fetch questions
            success, data, latency_ms = fetch_trivia_questions(params, use_cache=False)
            
            if not success:
                flash(f"Failed to fetch questions: {data.get('error', 'Unknown error')}", 'danger')
                return redirect(url_for('index'))
            
            if data.get('response_code') != 0:
                message = get_response_code_message(data.get('response_code'))
                flash(f"API Error: {message}", 'danger')
                return redirect(url_for('index'))
            
            questions = data.get('results', [])
            if not questions:
                flash("No questions returned from API", 'warning')
                return redirect(url_for('index'))
        
        # Process questions: decode and shuffle
        processed_questions = []
        for q in questions:
            question_text = decode_html_entities(q['question'])
            correct_answer = decode_html_entities(q['correct_answer'])
            incorrect_answers = [decode_html_entities(a) for a in q['incorrect_answers']]
            
            shuffled, correct_index = shuffle_answers(correct_answer, incorrect_answers)
            
            processed_questions.append({
                'category': decode_html_entities(q['category']),
                'difficulty': q['difficulty'],
                'type': q['type'],
                'question': question_text,
                'answers': shuffled,
                'correct_index': correct_index
            })
        
        # Store in session
        session['game'] = {
            'questions': processed_questions,
            'index': 0,
            'score': 0,
            'started_at': datetime.now().isoformat(),
            'params': params,
            'question_times': []
        }
        
        return redirect(url_for('question'))
    
    # GET request redirects to index
    return redirect(url_for('index'))


@app.route('/question')
def question():
    """Display current question"""
    game = session.get('game')
    
    if not game or not game.get('questions'):
        flash('No active game. Please start a new game.', 'warning')
        return redirect(url_for('index'))
    
    index = game['index']
    questions = game['questions']
    
    if index >= len(questions):
        return redirect(url_for('results'))
    
    current_question = questions[index]
    total = len(questions)
    
    # Store question start time
    if 'question_start_time' not in session:
        session['question_start_time'] = time.time()
    
    return render_template(
        'question.html',
        question=current_question,
        index=index,
        total=total
    )


@app.route('/answer', methods=['POST'])
def answer():
    """Process answer and advance game"""
    game = session.get('game')
    
    if not game or not game.get('questions'):
        flash('No active game', 'warning')
        return redirect(url_for('index'))
    
    index = game['index']
    questions = game['questions']
    
    if index >= len(questions):
        return redirect(url_for('results'))
    
    current_question = questions[index]
    user_answer = request.form.get('answer')
    
    # Calculate time taken
    question_start_time = session.pop('question_start_time', time.time())
    time_taken = time.time() - question_start_time
    
    if 'question_times' not in game:
        game['question_times'] = []
    game['question_times'].append(time_taken)
    
    # Check answer
    try:
        user_answer_index = int(user_answer)
        correct_index = current_question['correct_index']
        
        if user_answer_index == correct_index:
            game['score'] += 1
            # Optional time bonus
            if time_taken < 5:
                game['score'] += 0.2
            flash('Correct! 🎉', 'success')
        else:
            correct_answer = current_question['answers'][correct_index]
            flash(f'Wrong! The correct answer was: {correct_answer}', 'danger')
    
    except (ValueError, TypeError):
        flash('Invalid answer', 'danger')
    
    # Advance to next question
    game['index'] += 1
    session['game'] = game
    
    if game['index'] >= len(questions):
        return redirect(url_for('results'))
    
    return redirect(url_for('question'))


@app.route('/results', methods=['GET', 'POST'])
def results():
    """Display game results and save to leaderboard"""
    game = session.get('game')
    
    if not game or not game.get('questions'):
        flash('No game results to display', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Please enter your name', 'warning')
        else:
            score = int(game['score'])
            total = len(game['questions'])
            accuracy = (score / total * 100) if total > 0 else 0
            
            # Format difficulty for display and storage
            params = game['params']
            if params.get('difficulty') == 'mixed':
                difficulty = f"mixed (E:{params.get('easy',0)}/M:{params.get('medium',0)}/H:{params.get('hard',0)})"
            else:
                difficulty = params.get('difficulty', 'any')
            
            save_score(name, score, total, accuracy, difficulty)
            flash(f'Score saved to leaderboard! 🏆', 'success')
            
            # Clear game session after saving
            session.pop('game', None)
            return redirect(url_for('leaderboard'))
    
    score = int(game['score'])
    total = len(game['questions'])
    accuracy = (score / total * 100) if total > 0 else 0
    
    # Calculate time taken
    started_at = datetime.fromisoformat(game['started_at'])
    time_taken = (datetime.now() - started_at).total_seconds()
    
    return render_template(
        'results.html',
        score=score,
        total=total,
        accuracy=accuracy,
        time_taken=time_taken,
        difficulty=game['params'].get('difficulty', 'any')
    )


@app.route('/leaderboard')
def leaderboard():
    """Display leaderboard with filters"""
    difficulty_filter = request.args.get('difficulty', '')
    limit = request.args.get('limit', '50')
    
    try:
        limit = int(limit)
        if limit < 1 or limit > 100:
            limit = 50
    except ValueError:
        limit = 50
    
    scores = get_leaderboard(difficulty=difficulty_filter, limit=limit)
    
    return render_template(
        'leaderboard.html',
        scores=scores,
        difficulty_filter=difficulty_filter
    )


@app.route('/clear', methods=['POST'])
def clear_session():
    """Clear game session"""
    session.pop('game', None)
    session.pop('question_start_time', None)
    flash('Game session cleared', 'info')
    return redirect(url_for('index'))


@app.route('/healthz')
def healthz():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


@app.context_processor
def inject_categories():
    """Inject OpenTDB categories into all templates"""
    categories = [
        {'id': 9, 'name': 'General Knowledge'},
        {'id': 10, 'name': 'Entertainment: Books'},
        {'id': 11, 'name': 'Entertainment: Film'},
        {'id': 12, 'name': 'Entertainment: Music'},
        {'id': 13, 'name': 'Entertainment: Musicals & Theatres'},
        {'id': 14, 'name': 'Entertainment: Television'},
        {'id': 15, 'name': 'Entertainment: Video Games'},
        {'id': 16, 'name': 'Entertainment: Board Games'},
        {'id': 17, 'name': 'Science & Nature'},
        {'id': 18, 'name': 'Science: Computers'},
        {'id': 19, 'name': 'Science: Mathematics'},
        {'id': 20, 'name': 'Mythology'},
        {'id': 21, 'name': 'Sports'},
        {'id': 22, 'name': 'Geography'},
        {'id': 23, 'name': 'History'},
        {'id': 24, 'name': 'Politics'},
        {'id': 25, 'name': 'Art'},
        {'id': 26, 'name': 'Celebrities'},
        {'id': 27, 'name': 'Animals'},
        {'id': 28, 'name': 'Vehicles'},
        {'id': 29, 'name': 'Entertainment: Comics'},
        {'id': 30, 'name': 'Science: Gadgets'},
        {'id': 31, 'name': 'Entertainment: Japanese Anime & Manga'},
        {'id': 32, 'name': 'Entertainment: Cartoon & Animations'}
    ]
    return {'opentdb_categories': categories}


if __name__ == '__main__':
    app.run(debug=True)
