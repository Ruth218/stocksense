import logging
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
import pandas as pd
from app import db
from models import Prediction, StockHolding, Portfolio

def get_recent_predictions(user_id, limit=5):
    """Get recent predictions made by the user"""
    try:
        recent_predictions = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).limit(limit).all()
        
        result = []
        for pred in recent_predictions:
            try:
                # Get current price to compare with prediction
                stock = yf.Ticker(f"{pred.symbol}.NS")
                current_price = stock.info.get('regularMarketPrice', 0)
                
                # Calculate days elapsed and remaining
                days_elapsed = (datetime.utcnow() - pred.created_at).days
                days_remaining = pred.prediction_days - days_elapsed
                
                if days_remaining < 0:
                    status = "Expired"
                    days_remaining = 0
                else:
                    status = "Active"
                
                # Calculate current performance of the prediction
                if current_price > 0:
                    actual_change = ((current_price - pred.current_price) / pred.current_price) * 100
                    predicted_change = ((pred.predicted_price - pred.current_price) / pred.current_price) * 100
                    direction_correct = (actual_change > 0 and predicted_change > 0) or (actual_change < 0 and predicted_change < 0)
                else:
                    actual_change = 0
                    predicted_change = 0
                    direction_correct = False
                
                result.append({
                    'id': pred.id,
                    'symbol': pred.symbol,
                    'created_at': pred.created_at,
                    'prediction_days': pred.prediction_days,
                    'current_price': pred.current_price,
                    'predicted_price': pred.predicted_price,
                    'accuracy': pred.accuracy,
                    'latest_price': current_price,
                    'actual_change': actual_change,
                    'predicted_change': predicted_change,
                    'direction_correct': direction_correct,
                    'days_elapsed': days_elapsed,
                    'days_remaining': days_remaining,
                    'status': status
                })
            except Exception as e:
                logging.error(f"Error processing prediction {pred.id}: {e}")
                continue
        
        return result
    except Exception as e:
        logging.error(f"Error getting recent predictions: {e}")
        return []

def get_personalized_recommendations(user_id):
    """Generate personalized investment recommendations based on user portfolio and market conditions"""
    try:
        # Get user's current holdings
        holdings = []
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        for portfolio in portfolios:
            portfolio_holdings = StockHolding.query.filter_by(portfolio_id=portfolio.id).all()
            for holding in portfolio_holdings:
                holdings.append(holding)
        
        recommendations = []
        
        # 1. Analyze current holdings
        if holdings:
            for holding in holdings:
                try:
                    stock = yf.Ticker(f"{holding.symbol}.NS")
                    info = stock.info
                    history = stock.history(period="1mo")
                    
                    if history.empty or 'regularMarketPrice' not in info:
                        continue
                    
                    current_price = info['regularMarketPrice']
                    avg_price = holding.average_price
                    change = ((current_price - avg_price) / avg_price) * 100
                    
                    # Check if stock has fallen significantly
                    if change < -10:
                        recommendations.append({
                            'type': 'holding_alert',
                            'symbol': holding.symbol,
                            'message': f"{holding.symbol} has fallen {abs(change):.2f}% from your purchase price. Consider averaging down.",
                            'action': 'Consider buying more to average down'
                        })
                    
                    # Check if stock has risen significantly
                    elif change > 20:
                        recommendations.append({
                            'type': 'holding_alert',
                            'symbol': holding.symbol,
                            'message': f"{holding.symbol} has risen {change:.2f}% from your purchase price. Consider taking profits.",
                            'action': 'Consider taking profits'
                        })
                    
                    # Check RSI for overbought/oversold conditions
                    if len(history) > 14:
                        delta = history['Close'].diff()
                        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs))
                        
                        latest_rsi = rsi.iloc[-1]
                        
                        if latest_rsi > 70:
                            recommendations.append({
                                'type': 'technical_alert',
                                'symbol': holding.symbol,
                                'message': f"{holding.symbol} is showing overbought conditions with RSI at {latest_rsi:.2f}.",
                                'action': 'Consider reducing position'
                            })
                        elif latest_rsi < 30:
                            recommendations.append({
                                'type': 'technical_alert',
                                'symbol': holding.symbol,
                                'message': f"{holding.symbol} is showing oversold conditions with RSI at {latest_rsi:.2f}.",
                                'action': 'Consider increasing position'
                            })
                except Exception as e:
                    logging.error(f"Error analyzing holding {holding.symbol}: {e}")
                    continue
        
        # 2. Market sector recommendations
        try:
            # Check Nifty 50 performance
            nifty = yf.Ticker("^NSEI")
            nifty_info = nifty.info
            nifty_history = nifty.history(period="1mo")
            
            if not nifty_history.empty:
                nifty_change = ((nifty_history['Close'].iloc[-1] - nifty_history['Close'].iloc[0]) / nifty_history['Close'].iloc[0]) * 100
                
                if nifty_change > 5:
                    recommendations.append({
                        'type': 'market_alert',
                        'symbol': 'NIFTY 50',
                        'message': f"Indian markets have risen {nifty_change:.2f}% in the last month. Consider diversifying across sectors.",
                        'action': 'Consider sector rotation'
                    })
                elif nifty_change < -5:
                    recommendations.append({
                        'type': 'market_alert',
                        'symbol': 'NIFTY 50',
                        'message': f"Indian markets have fallen {abs(nifty_change):.2f}% in the last month. Consider defensive stocks.",
                        'action': 'Consider defensive positions'
                    })
        except Exception as e:
            logging.error(f"Error analyzing market indices: {e}")
        
        # 3. Add some general diversification recommendations
        if len(holdings) < 5:
            recommendations.append({
                'type': 'portfolio_alert',
                'symbol': 'PORTFOLIO',
                'message': "Your portfolio has fewer than 5 stocks. Consider diversifying to reduce risk.",
                'action': 'Add more stocks for diversification'
            })
        
        if len(holdings) > 0:
            sectors = {}
            for holding in holdings:
                try:
                    stock = yf.Ticker(f"{holding.symbol}.NS")
                    sector = stock.info.get('sector', 'Unknown')
                    if sector in sectors:
                        sectors[sector] += 1
                    else:
                        sectors[sector] = 1
                except:
                    continue
            
            # Check for sector concentration
            for sector, count in sectors.items():
                if count > len(holdings) * 0.3 and len(holdings) > 3:
                    recommendations.append({
                        'type': 'diversification_alert',
                        'symbol': 'SECTOR',
                        'message': f"Your portfolio has a high concentration in the {sector} sector. Consider diversifying.",
                        'action': 'Diversify across sectors'
                    })
                    break
        
        # 4. Add some trending stock recommendations
        try:
            # Top gainers in Nifty 50
            gainers = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']  # Default list in case we can't fetch
            
            recommendations.append({
                'type': 'trending_alert',
                'symbol': 'TRENDING',
                'message': f"Consider researching these trending stocks: {', '.join(gainers)}.",
                'action': 'Research trending stocks'
            })
        except Exception as e:
            logging.error(f"Error fetching trending stocks: {e}")
        
        return recommendations
    except Exception as e:
        logging.error(f"Error generating recommendations: {e}")
        return []

def save_prediction(user_id, symbol, prediction_days, current_price, predicted_price, accuracy):
    """Save a prediction to the database"""
    try:
        new_prediction = Prediction(
            user_id=user_id,
            symbol=symbol,
            prediction_days=prediction_days,
            current_price=current_price,
            predicted_price=predicted_price,
            accuracy=accuracy
        )
        
        db.session.add(new_prediction)
        db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Error saving prediction: {e}")
        db.session.rollback()
        return False
