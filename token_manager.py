from datetime import datetime, timedelta
from flask import current_app # To access logger if needed

# Import db from extensions and UserToken model from models
from extensions import db
from models import UserToken, User # Import User to handle relationship if needed

_app = None

def init_app(app):
    """
    Initialize token manager with the Flask app instance.
    Registers the UserToken model with the db instance.
    Args:
        app: Flask application instance
    """
    global _app
    _app = app
    # No need to define UserTokenModel here, it's imported from models.py
    # Ensure tables are created within the app context if needed elsewhere
    # Typically handled by Flask-Migrate or initial db.create_all()
    pass

def check_balance(user_id, cost=0):
    """
    Check if user balance is sufficient for a cost.
    Creates a UserToken record if one doesn't exist.
    Also checks for weekly reset.
    Args:
        user_id: The user's ID.
        cost: The cost of the operation (default: 0).
    Returns:
        tuple: (bool: True if balance is sufficient, float: current balance)
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id) # Default balance is set in the model
        db.session.add(token)
        # Commit immediately or rely on commit after operation?
        # Committing here ensures token exists before reset check
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating UserToken for {user_id}: {str(e)}")
            # Decide how to handle this error, maybe return insufficient balance
            return False, 0.0 
    
    # Check if balance needs resetting
    check_weekly_reset(token)
    
    # Check if balance is sufficient
    return token.balance >= cost, token.balance

def deduct_balance(user_id, cost):
    """
    Deduct cost from user's balance.
    Creates a UserToken record if one doesn't exist.
    Also checks for weekly reset before deduction.
    Args:
        user_id: The user's ID.
        cost: The cost to deduct.
    Returns:
        float: The new balance after deduction.
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id)
        db.session.add(token)
        # Commit needed before reset check and deduction
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating UserToken for {user_id} during deduction: {str(e)}")
            return 0.0 # Return 0 balance on error
            
    # Check for reset before deduction
    check_weekly_reset(token)
    
    # Ensure cost is non-negative
    cost = max(0, cost)
    
    # Deduct cost
    token.balance -= cost
    
    # Prevent negative balance
    token.balance = max(0, token.balance)
    
    try:
        db.session.commit()
        print(f"User {user_id} deducted {cost:.6f}, current balance: {token.balance:.6f}") # Use logger in production
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing balance deduction for {user_id}: {str(e)}")
        # Return the balance before the failed commit? Or 0?
        # Returning the potentially incorrect balance might be misleading
        return 0.0 # Return 0 on commit error
        
    return token.balance

def check_weekly_reset(token):
    """
    Check if the user's balance needs to be reset (every Sunday UTC).
    Args:
        token: The UserToken object.
    """
    now = datetime.utcnow()
    # Check if it's a different week OR a different year, and if today is Sunday (6)
    needs_reset = False
    if token.last_reset.year < now.year:
        needs_reset = True
    elif token.last_reset.isocalendar()[1] < now.isocalendar()[1]:
         needs_reset = True

    if needs_reset and now.weekday() == 6: # Sunday is 6
        old_balance = token.balance
        token.balance = 5.0  # Reset to 5
        token.last_reset = now
        try:
            db.session.commit() # Commit the reset
            print(f"User {token.user_id} balance reset to 5.0 from {old_balance:.6f}") # Use logger
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing weekly reset for user {token.user_id}: {str(e)}")
            # Revert changes if commit fails?
            token.balance = old_balance
            token.last_reset = token.last_reset # Keep old reset time

def get_balance(user_id):
    """
    Get the current balance for a user.
    Creates a UserToken record if one doesn't exist.
    Also checks for weekly reset.
    Args:
        user_id: The user's ID.
    Returns:
        float: The current balance.
    """
    token = UserToken.query.filter_by(user_id=user_id).first()
    
    if not token:
        token = UserToken(user_id=user_id)
        db.session.add(token)
        try:
            db.session.commit()
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Error creating UserToken for {user_id} in get_balance: {str(e)}")
             return 0.0
             
    # Check for reset
    check_weekly_reset(token)
    
    return token.balance

def get_next_reset_time():
    """
    Calculate the next weekly reset time (Sunday 00:00 UTC).
    Returns:
        datetime: The datetime of the next reset.
    """
    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday() + 7) % 7 # Days until next Sunday
    
    # If today is Sunday, the next reset is next Sunday unless it's exactly 00:00:00
    if days_until_sunday == 0 and (now.hour > 0 or now.minute > 0 or now.second > 0 or now.microsecond > 0):
        days_until_sunday = 7
        
    # Calculate the date of the next Sunday
    next_sunday_date = (now + timedelta(days=days_until_sunday)).date()
    
    # Combine with 00:00:00 time
    next_reset_time = datetime.combine(next_sunday_date, datetime.min.time())
    
    return next_reset_time