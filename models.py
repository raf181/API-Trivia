"""
Database models and operations for Flask Trivia Dashboard
Uses SQLite3 for leaderboard scores
"""
import sqlite3
from datetime import datetime
import os


DB_PATH = os.path.join(os.path.dirname(__file__), 'trivia.db')


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with scores table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            difficulty TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON scores(created_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_score 
        ON scores(score DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_difficulty 
        ON scores(difficulty)
    ''')
    
    conn.commit()
    conn.close()


def save_score(name, score, total, accuracy, difficulty='any'):
    """Save a score to the leaderboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO scores (name, score, total, accuracy, difficulty, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, score, total, accuracy, difficulty, created_at))
    
    conn.commit()
    conn.close()


def get_leaderboard(difficulty='', limit=50):
    """
    Get leaderboard entries
    
    Args:
        difficulty: Filter by difficulty ('easy', 'medium', 'hard', '' for all)
        limit: Maximum number of entries to return
    
    Returns:
        List of score dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if difficulty:
        cursor.execute('''
            SELECT id, name, score, total, accuracy, difficulty, created_at
            FROM scores
            WHERE difficulty = ?
            ORDER BY score DESC, accuracy DESC, created_at DESC
            LIMIT ?
        ''', (difficulty, limit))
    else:
        cursor.execute('''
            SELECT id, name, score, total, accuracy, difficulty, created_at
            FROM scores
            ORDER BY score DESC, accuracy DESC, created_at DESC
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    scores = []
    for row in rows:
        scores.append({
            'id': row['id'],
            'name': row['name'],
            'score': row['score'],
            'total': row['total'],
            'accuracy': row['accuracy'],
            'difficulty': row['difficulty'],
            'created_at': row['created_at']
        })
    
    return scores


def get_top_scores(limit=10):
    """Get top scores across all difficulties"""
    return get_leaderboard(difficulty='', limit=limit)


def get_recent_scores(limit=20):
    """Get most recent scores"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, score, total, accuracy, difficulty, created_at
        FROM scores
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    scores = []
    for row in rows:
        scores.append({
            'id': row['id'],
            'name': row['name'],
            'score': row['score'],
            'total': row['total'],
            'accuracy': row['accuracy'],
            'difficulty': row['difficulty'],
            'created_at': row['created_at']
        })
    
    return scores


def delete_score(score_id):
    """Delete a score by ID (admin functionality)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
    
    conn.commit()
    conn.close()


def get_stats():
    """Get overall statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total_games FROM scores')
    total_games = cursor.fetchone()['total_games']
    
    cursor.execute('SELECT AVG(accuracy) as avg_accuracy FROM scores')
    avg_accuracy = cursor.fetchone()['avg_accuracy'] or 0
    
    cursor.execute('SELECT MAX(score) as high_score FROM scores')
    high_score = cursor.fetchone()['high_score'] or 0
    
    conn.close()
    
    return {
        'total_games': total_games,
        'avg_accuracy': round(avg_accuracy, 2),
        'high_score': high_score
    }
