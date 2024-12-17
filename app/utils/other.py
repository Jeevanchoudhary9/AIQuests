import datetime
import random
from datetime import timedelta
from ..models import User, Questions, Answers

def generate_demo_data():
    # Generate sample time-series data for the past 30 days
    dates = [(datetime.datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30)]
    
    return {
        'user_metrics': {
            'total_users': 1250,
            'active_users': 890,
            'new_users_today': 25
        },
        'content_metrics': {
            'total_questions': 3450,
            'total_answers': 12340,
            'ai_answers': 5670
        },
        'trending_tags': [
            {'name': 'Python', 'count': 450},
            {'name': 'JavaScript', 'count': 380},
            {'name': 'React', 'count': 320},
            {'name': 'Flutter', 'count': 290},
            {'name': 'Docker', 'count': 250}
        ],
        'time_series_data': {
            'dates': dates,
            'questions': [random.randint(10, 50) for _ in range(30)],
            'answers': [random.randint(30, 100) for _ in range(30)]
        },
        'top_questions': [
            {'title': 'How to implement LinkedList in Rust?', 'views': 1200, 'answers': 5},
            {'title': 'Best practices for React hooks', 'views': 980, 'answers': 8},
            {'title': 'Python async vs threading', 'views': 850, 'answers': 6},
            {'title': 'Docker container networking', 'views': 720, 'answers': 4},
            {'title': 'Flutter state management', 'views': 690, 'answers': 7}
        ],
        'moderation_stats': {
            'flagged_content': 23,
            'pending_reviews': 12,
            'resolved_today': 45
        }
    }