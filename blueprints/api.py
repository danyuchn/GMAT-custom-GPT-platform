from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import Message, Chat # Import models
import token_manager # Import token manager functions

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get current user's API usage statistics."""
    try:
        # Get balance and reset time from token_manager
        balance = token_manager.get_balance(current_user.id)
        next_reset = token_manager.get_next_reset_time()
        days_until_reset = (next_reset - datetime.utcnow()).days
        
        # Calculate total tokens and cost from Message model
        # This approach queries the DB each time. Consider UserQuota for optimization if needed.
        messages = Message.query.join(Chat).filter(Chat.user_id == current_user.id).all()
        total_prompt_tokens = sum(msg.prompt_tokens for msg in messages)
        total_completion_tokens = sum(msg.completion_tokens for msg in messages)
        total_tokens = total_prompt_tokens + total_completion_tokens
        total_cost = sum(msg.cost for msg in messages)
        
        return jsonify({
            'status': 'success',
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 6), # Round cost for display
            'balance': round(balance, 6), # Round balance for display
            'days_until_reset': days_until_reset
        })
    except Exception as e:
        # Log the error properly in a real application
        # current_app.logger.error(f"Error getting user stats for {current_user.id}: {str(e)}")
        print(f"Error getting user stats for {current_user.id}: {str(e)}") # Temporary print
        return jsonify({
            'status': 'error',
            'message': '獲取用戶統計數據時發生內部錯誤。'
        }), 500 