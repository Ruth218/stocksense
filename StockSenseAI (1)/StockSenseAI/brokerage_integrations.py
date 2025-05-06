import logging
import json
import requests
from datetime import datetime, timedelta
from app import db
from models import BrokerageAccount, StockTransaction, Portfolio, StockHolding

def get_connected_accounts(user_id):
    """Get all brokerage accounts connected by the user"""
    try:
        accounts = BrokerageAccount.query.filter_by(user_id=user_id, is_active=True).all()
        
        result = []
        for account in accounts:
            # Check if token is expired
            is_expired = False
            if account.token_expiry and account.token_expiry < datetime.utcnow():
                is_expired = True
            
            result.append({
                'id': account.id,
                'brokerage_name': account.brokerage_name,
                'account_id': account.account_id,
                'is_active': account.is_active,
                'is_expired': is_expired,
                'last_synced': account.last_synced,
                'created_at': account.created_at
            })
        
        return result
    except Exception as e:
        logging.error(f"Error getting connected accounts: {e}")
        return []

def connect_brokerage(user_id, brokerage_name, credentials):
    """Connect a brokerage account"""
    try:
        # Check if this brokerage is already connected
        existing_account = BrokerageAccount.query.filter_by(
            user_id=user_id,
            brokerage_name=brokerage_name,
            is_active=True
        ).first()
        
        if existing_account:
            return {'success': False, 'error': f'You already have an active {brokerage_name} account connected'}
        
        # Validate credentials with mock validation
        # In a real system, we would make API calls to the respective brokerages
        if brokerage_name == 'groww':
            account_id = credentials.get('client_id', '')
            api_key = credentials.get('api_key', '')
            api_secret = credentials.get('api_secret', '')
            
            if not account_id or not api_key or not api_secret:
                return {'success': False, 'error': 'Invalid Groww credentials'}
            
        elif brokerage_name == 'zerodha':
            account_id = credentials.get('client_id', '')
            api_key = credentials.get('api_key', '')
            api_secret = credentials.get('api_secret', '')
            
            if not account_id or not api_key or not api_secret:
                return {'success': False, 'error': 'Invalid Zerodha credentials'}
            
        elif brokerage_name == 'upstox':
            account_id = credentials.get('client_id', '')
            api_key = credentials.get('api_key', '')
            api_secret = credentials.get('api_secret', '')
            
            if not account_id or not api_key or not api_secret:
                return {'success': False, 'error': 'Invalid Upstox credentials'}
            
        else:
            return {'success': False, 'error': 'Unsupported brokerage'}
        
        # Create a new brokerage account
        new_account = BrokerageAccount(
            user_id=user_id,
            brokerage_name=brokerage_name,
            account_id=account_id,
            access_token='mock_token',  # In a real system, this would be a real token
            refresh_token='mock_refresh_token',
            token_expiry=datetime.utcnow() + timedelta(days=7),
            is_active=True
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        # Automatically sync the portfolio
        sync_result = sync_portfolio(user_id, new_account.id)
        
        if not sync_result.get('success', False):
            logging.warning(f"Initial portfolio sync failed: {sync_result.get('error')}")
        
        return {'success': True, 'account_id': new_account.id}
    except Exception as e:
        logging.error(f"Error connecting brokerage: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def sync_portfolio(user_id, brokerage_id):
    """Sync portfolio data from the brokerage"""
    try:
        # Get the brokerage account
        account = BrokerageAccount.query.filter_by(id=brokerage_id, user_id=user_id).first()
        
        if not account:
            return {'success': False, 'error': 'Brokerage account not found or access denied'}
        
        if not account.is_active:
            return {'success': False, 'error': 'Brokerage account is not active'}
        
        # Check if token is expired
        if account.token_expiry and account.token_expiry < datetime.utcnow():
            return {'success': False, 'error': 'Brokerage token is expired. Please reconnect.'}
        
        # In a real application, we would make API calls to get actual portfolio data
        # For this example, we'll simulate portfolio data based on the brokerage
        
        if account.brokerage_name == 'groww':
            holdings = [
                {'symbol': 'RELIANCE', 'quantity': 10, 'average_price': 2500.00},
                {'symbol': 'HDFCBANK', 'quantity': 15, 'average_price': 1600.50},
                {'symbol': 'INFY', 'quantity': 20, 'average_price': 1450.75}
            ]
        elif account.brokerage_name == 'zerodha':
            holdings = [
                {'symbol': 'TCS', 'quantity': 5, 'average_price': 3400.25},
                {'symbol': 'WIPRO', 'quantity': 25, 'average_price': 420.10},
                {'symbol': 'SBIN', 'quantity': 30, 'average_price': 550.60}
            ]
        elif account.brokerage_name == 'upstox':
            holdings = [
                {'symbol': 'LT', 'quantity': 8, 'average_price': 2100.35},
                {'symbol': 'ICICIBANK', 'quantity': 18, 'average_price': 950.45},
                {'symbol': 'BHEL', 'quantity': 100, 'average_price': 90.25}
            ]
        else:
            return {'success': False, 'error': 'Unsupported brokerage'}
        
        # Find or create a portfolio for this brokerage
        portfolio_name = f"{account.brokerage_name.capitalize()} Portfolio"
        
        portfolio = Portfolio.query.filter_by(
            user_id=user_id,
            name=portfolio_name
        ).first()
        
        if not portfolio:
            portfolio = Portfolio(
                user_id=user_id,
                name=portfolio_name,
                description=f"Holdings from your {account.brokerage_name.capitalize()} account"
            )
            db.session.add(portfolio)
            db.session.commit()
        
        # Sync holdings
        for holding_data in holdings:
            existing_holding = StockHolding.query.filter_by(
                portfolio_id=portfolio.id,
                symbol=holding_data['symbol']
            ).first()
            
            if existing_holding:
                # Update existing holding
                existing_holding.quantity = holding_data['quantity']
                existing_holding.average_price = holding_data['average_price']
                existing_holding.updated_at = datetime.utcnow()
            else:
                # Create new holding
                new_holding = StockHolding(
                    portfolio_id=portfolio.id,
                    symbol=holding_data['symbol'],
                    quantity=holding_data['quantity'],
                    average_price=holding_data['average_price']
                )
                db.session.add(new_holding)
        
        # Update last synced timestamp
        account.last_synced = datetime.utcnow()
        db.session.commit()
        
        return {'success': True}
    except Exception as e:
        logging.error(f"Error syncing portfolio: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def disconnect_brokerage(user_id, brokerage_id):
    """Disconnect a brokerage account"""
    try:
        account = BrokerageAccount.query.filter_by(id=brokerage_id, user_id=user_id).first()
        
        if not account:
            return {'success': False, 'error': 'Brokerage account not found or access denied'}
        
        account.is_active = False
        account.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'success': True}
    except Exception as e:
        logging.error(f"Error disconnecting brokerage: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def refresh_brokerage_token(user_id, brokerage_id):
    """Refresh the brokerage access token"""
    try:
        account = BrokerageAccount.query.filter_by(id=brokerage_id, user_id=user_id).first()
        
        if not account:
            return {'success': False, 'error': 'Brokerage account not found or access denied'}
        
        if not account.is_active:
            return {'success': False, 'error': 'Brokerage account is not active'}
        
        # In a real application, we would make API calls to refresh the token
        # For this example, we'll just update the expiry
        
        account.token_expiry = datetime.utcnow() + timedelta(days=7)
        account.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'success': True}
    except Exception as e:
        logging.error(f"Error refreshing brokerage token: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}
