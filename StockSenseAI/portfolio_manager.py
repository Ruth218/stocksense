import logging
import json
import pandas as pd
import yfinance as yf
from app import db
from models import Portfolio, StockHolding, StockTransaction, BrokerageAccount
from datetime import datetime, timedelta

def get_portfolio_summary(user_id):
    """Get a summary of the user's portfolio performance"""
    try:
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        if not portfolios:
            return {
                'total_value': 0,
                'total_investment': 0,
                'total_return': 0,
                'return_percentage': 0,
                'holdings_count': 0,
                'portfolios_count': 0
            }
        
        total_value = 0
        total_investment = 0
        total_holdings = 0
        
        for portfolio in portfolios:
            holdings = StockHolding.query.filter_by(portfolio_id=portfolio.id).all()
            for holding in holdings:
                try:
                    investment = holding.quantity * holding.average_price
                    
                    # Get current price
                    stock = yf.Ticker(f"{holding.symbol}.NS")
                    current_price = stock.info.get('regularMarketPrice', 0)
                    
                    current_value = holding.quantity * current_price
                    
                    total_investment += investment
                    total_value += current_value
                    total_holdings += 1
                except Exception as e:
                    logging.error(f"Error calculating holding value for {holding.symbol}: {e}")
                    continue
        
        total_return = total_value - total_investment
        return_percentage = (total_return / total_investment * 100) if total_investment > 0 else 0
        
        return {
            'total_value': round(total_value, 2),
            'total_investment': round(total_investment, 2),
            'total_return': round(total_return, 2),
            'return_percentage': round(return_percentage, 2),
            'holdings_count': total_holdings,
            'portfolios_count': len(portfolios)
        }
    except Exception as e:
        logging.error(f"Error getting portfolio summary: {e}")
        return {
            'total_value': 0,
            'total_investment': 0,
            'total_return': 0,
            'return_percentage': 0,
            'holdings_count': 0,
            'portfolios_count': 0
        }

def get_portfolio_detail(user_id):
    """Get detailed information about the user's portfolios and holdings"""
    try:
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        if not portfolios:
            return []
        
        result = []
        
        for portfolio in portfolios:
            holdings = StockHolding.query.filter_by(portfolio_id=portfolio.id).all()
            
            holdings_data = []
            portfolio_value = 0
            portfolio_investment = 0
            
            for holding in holdings:
                try:
                    stock = yf.Ticker(f"{holding.symbol}.NS")
                    info = stock.info
                    
                    if not info:
                        continue
                    
                    investment = holding.quantity * holding.average_price
                    current_price = info.get('regularMarketPrice', 0)
                    current_value = holding.quantity * current_price
                    
                    profit_loss = current_value - investment
                    profit_loss_percentage = (profit_loss / investment * 100) if investment > 0 else 0
                    
                    holdings_data.append({
                        'id': holding.id,
                        'symbol': holding.symbol,
                        'name': info.get('shortName', holding.symbol),
                        'quantity': holding.quantity,
                        'average_price': holding.average_price,
                        'current_price': current_price,
                        'investment': round(investment, 2),
                        'current_value': round(current_value, 2),
                        'profit_loss': round(profit_loss, 2),
                        'profit_loss_percentage': round(profit_loss_percentage, 2)
                    })
                    
                    portfolio_value += current_value
                    portfolio_investment += investment
                except Exception as e:
                    logging.error(f"Error processing holding {holding.symbol}: {e}")
                    continue
            
            portfolio_profit_loss = portfolio_value - portfolio_investment
            portfolio_profit_loss_percentage = (portfolio_profit_loss / portfolio_investment * 100) if portfolio_investment > 0 else 0
            
            result.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'created_at': portfolio.created_at,
                'holdings': holdings_data,
                'total_value': round(portfolio_value, 2),
                'total_investment': round(portfolio_investment, 2),
                'profit_loss': round(portfolio_profit_loss, 2),
                'profit_loss_percentage': round(portfolio_profit_loss_percentage, 2),
                'holdings_count': len(holdings_data)
            })
        
        return result
    except Exception as e:
        logging.error(f"Error getting portfolio details: {e}")
        return []

def add_portfolio(user_id, name, description=""):
    """Create a new portfolio for the user"""
    try:
        new_portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description
        )
        
        db.session.add(new_portfolio)
        db.session.commit()
        
        return {'success': True, 'portfolio_id': new_portfolio.id}
    except Exception as e:
        logging.error(f"Error creating portfolio: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def add_holding(portfolio_id, symbol, quantity, average_price):
    """Add a stock holding to a portfolio"""
    try:
        # Check if the holding already exists
        existing_holding = StockHolding.query.filter_by(
            portfolio_id=portfolio_id,
            symbol=symbol
        ).first()
        
        if existing_holding:
            # Update existing holding
            total_quantity = existing_holding.quantity + quantity
            total_value = (existing_holding.quantity * existing_holding.average_price) + (quantity * average_price)
            new_average_price = total_value / total_quantity if total_quantity > 0 else average_price
            
            existing_holding.quantity = total_quantity
            existing_holding.average_price = new_average_price
            existing_holding.updated_at = datetime.utcnow()
        else:
            # Create new holding
            new_holding = StockHolding(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                average_price=average_price
            )
            db.session.add(new_holding)
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        logging.error(f"Error adding holding: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def record_transaction(user_id, symbol, transaction_type, quantity, price, brokerage_account_id=None):
    """Record a stock transaction"""
    try:
        new_transaction = StockTransaction(
            user_id=user_id,
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            brokerage_account_id=brokerage_account_id
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return {'success': True, 'transaction_id': new_transaction.id}
    except Exception as e:
        logging.error(f"Error recording transaction: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def get_transaction_history(user_id, limit=20):
    """Get the user's transaction history"""
    try:
        transactions = StockTransaction.query.filter_by(user_id=user_id).order_by(StockTransaction.transaction_date.desc()).limit(limit).all()
        
        result = []
        for tx in transactions:
            # Get brokerage account info if available
            brokerage_name = None
            if tx.brokerage_account_id:
                account = BrokerageAccount.query.get(tx.brokerage_account_id)
                if account:
                    brokerage_name = account.brokerage_name
            
            result.append({
                'id': tx.id,
                'symbol': tx.symbol,
                'transaction_type': tx.transaction_type,
                'quantity': tx.quantity,
                'price': tx.price,
                'total_value': tx.quantity * tx.price,
                'transaction_date': tx.transaction_date,
                'brokerage': brokerage_name
            })
        
        return result
    except Exception as e:
        logging.error(f"Error getting transaction history: {e}")
        return []

def delete_portfolio(portfolio_id, user_id):
    """Delete a portfolio and its holdings"""
    try:
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        
        if not portfolio:
            return {'success': False, 'error': 'Portfolio not found or access denied'}
        
        # Delete holdings first
        StockHolding.query.filter_by(portfolio_id=portfolio_id).delete()
        
        # Delete portfolio
        db.session.delete(portfolio)
        db.session.commit()
        
        return {'success': True}
    except Exception as e:
        logging.error(f"Error deleting portfolio: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def update_holding(holding_id, portfolio_id, user_id, quantity=None, average_price=None):
    """Update a stock holding"""
    try:
        # First verify the portfolio belongs to the user
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        
        if not portfolio:
            return {'success': False, 'error': 'Portfolio not found or access denied'}
        
        # Find the holding
        holding = StockHolding.query.filter_by(id=holding_id, portfolio_id=portfolio_id).first()
        
        if not holding:
            return {'success': False, 'error': 'Holding not found'}
        
        # Update the holding
        if quantity is not None:
            holding.quantity = quantity
        
        if average_price is not None:
            holding.average_price = average_price
        
        holding.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {'success': True}
    except Exception as e:
        logging.error(f"Error updating holding: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}
