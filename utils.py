"""
Utility functions for Flask Trivia Dashboard
Input validation, HTML decoding, answer shuffling, etc.
"""
import html
import random
from typing import List, Tuple


def validate_amount(amount_str: str) -> int:
    """
    Validate amount parameter (1-50)
    
    Args:
        amount_str: String representation of amount
    
    Returns:
        Validated integer amount
    
    Raises:
        ValueError: If amount is invalid
    """
    try:
        amount = int(amount_str)
        if amount < 1 or amount > 50:
            raise ValueError("Amount must be between 1 and 50")
        return amount
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("Amount must be a valid integer")
        raise


def validate_difficulty(difficulty: str) -> str:
    """
    Validate difficulty parameter
    
    Args:
        difficulty: Difficulty string
    
    Returns:
        Validated difficulty or empty string
    
    Raises:
        ValueError: If difficulty is invalid
    """
    valid_difficulties = ['', 'easy', 'medium', 'hard']
    difficulty = difficulty.lower().strip()
    
    if difficulty not in valid_difficulties:
        raise ValueError(f"Difficulty must be one of: {', '.join(valid_difficulties[1:])}")
    
    return difficulty


def validate_type(q_type: str) -> str:
    """
    Validate question type parameter
    
    Args:
        q_type: Question type string
    
    Returns:
        Validated type or empty string
    
    Raises:
        ValueError: If type is invalid
    """
    valid_types = ['', 'multiple', 'boolean']
    q_type = q_type.lower().strip()
    
    if q_type not in valid_types:
        raise ValueError(f"Type must be one of: {', '.join(valid_types[1:])}")
    
    return q_type


def validate_encode(encode: str) -> str:
    """
    Validate encode parameter
    
    Args:
        encode: Encoding string
    
    Returns:
        Validated encoding or empty string
    
    Raises:
        ValueError: If encoding is invalid
    """
    valid_encodings = ['', 'url3986', 'base64']
    encode = encode.lower().strip()
    
    if encode not in valid_encodings:
        raise ValueError(f"Encode must be one of: {', '.join(valid_encodings)}")
    
    return encode


def decode_html_entities(text: str) -> str:
    """
    Decode HTML entities in text
    
    Args:
        text: Text with HTML entities
    
    Returns:
        Decoded text
    """
    return html.unescape(text)


def shuffle_answers(correct_answer: str, incorrect_answers: List[str]) -> Tuple[List[str], int]:
    """
    Shuffle answers while tracking correct answer index
    
    Args:
        correct_answer: The correct answer
        incorrect_answers: List of incorrect answers
    
    Returns:
        Tuple of (shuffled_answers, correct_index)
    """
    all_answers = [correct_answer] + incorrect_answers
    correct_index = 0
    
    # Shuffle with seed for reproducibility in tests if needed
    random.shuffle(all_answers)
    
    # Find new index of correct answer
    correct_index = all_answers.index(correct_answer)
    
    return all_answers, correct_index


def get_response_code_message(code: int) -> str:
    """
    Map OpenTDB response codes to user-friendly messages
    
    Args:
        code: OpenTDB response code
    
    Returns:
        User-friendly message
    """
    messages = {
        0: "Success",
        1: "No results - Not enough questions for your query",
        2: "Invalid parameter - Check your request parameters",
        3: "Token not found - Session token is invalid",
        4: "Token empty - All questions have been used, reset token",
        5: "Rate limit - Too many requests"
    }
    
    return messages.get(code, f"Unknown error code: {code}")


def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    return f"{minutes}m {remaining_seconds:.0f}s"


def calculate_grade(accuracy: float) -> str:
    """
    Calculate letter grade from accuracy percentage
    
    Args:
        accuracy: Accuracy percentage (0-100)
    
    Returns:
        Letter grade
    """
    if accuracy >= 90:
        return "A"
    elif accuracy >= 80:
        return "B"
    elif accuracy >= 70:
        return "C"
    elif accuracy >= 60:
        return "D"
    else:
        return "F"


def get_difficulty_badge_class(difficulty: str) -> str:
    """
    Get Bootstrap badge class for difficulty
    
    Args:
        difficulty: Difficulty level
    
    Returns:
        Bootstrap badge class
    """
    classes = {
        'easy': 'success',
        'medium': 'warning',
        'hard': 'danger',
        'any': 'secondary'
    }
    
    return classes.get(difficulty.lower(), 'secondary')


def validate_mixed_difficulty(easy: str, medium: str, hard: str) -> dict:
    """
    Validate mixed difficulty parameters
    
    Args:
        easy: Number of easy questions
        medium: Number of medium questions
        hard: Number of hard questions
    
    Returns:
        Dictionary with validated counts
    
    Raises:
        ValueError: If parameters are invalid
    """
    try:
        easy_count = int(easy) if easy else 0
        medium_count = int(medium) if medium else 0
        hard_count = int(hard) if hard else 0
        
        if easy_count < 0 or medium_count < 0 or hard_count < 0:
            raise ValueError("Question counts must be non-negative")
        
        total = easy_count + medium_count + hard_count
        
        if total < 1:
            raise ValueError("At least one question must be requested")
        
        if total > 50:
            raise ValueError("Total questions cannot exceed 50")
        
        return {
            'easy': easy_count,
            'medium': medium_count,
            'hard': hard_count,
            'total': total
        }
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError("Question counts must be valid integers")
        raise


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."
