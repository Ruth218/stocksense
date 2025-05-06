from flask import Flask, request, jsonify, send_from_directory
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping
import os
import json
from difflib import get_close_matches

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load Indian stocks data
with open('stocks.json', 'r') as f:
    INDIAN_STOCKS = json.load(f)

# Store stocks data with proper Yahoo Finance symbols
STOCKS_DATA = {}
for name, ticker in INDIAN_STOCKS.items():
    STOCKS_DATA[ticker] = name
    STOCKS_DATA[f"{ticker}.NS"] = name

def get_close_stocks(query):
    query = query.lower().strip()
    exact_matches = [(ticker, name) for ticker, name in STOCKS_DATA.items() 
                    if query in ticker.lower() or query in name.lower()]
    
    if exact_matches:
        return exact_matches[:10]
    
    all_names = list(STOCKS_DATA.values())
    all_tickers = list(STOCKS_DATA.keys())
    name_matches = get_close_matches(query, all_names, n=5, cutoff=0.3)
    ticker_matches = get_close_matches(query, all_tickers, n=5, cutoff=0.3)
    
    results = []
    for name in name_matches:
        ticker = [k for k, v in STOCKS_DATA.items() if v == name][0]
        results.append((ticker, name))
    
    for ticker in ticker_matches:
        if ticker not in [r[0] for r in results]:
            results.append((ticker, STOCKS_DATA[ticker]))
    
    return results[:10]

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window):
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_pivot_points(data):
    pp = (data['High'] + data['Low'] + data['Close']) / 3
    return pd.DataFrame({
        'PP': pp,
        'S1': 2 * pp - data['High'],
        'S2': pp - (data['High'] - data['Low']),
        'R1': 2 * pp - data['Low'],
        'R2': pp + (data['High'] - data['Low'])
    })

def get_stock_data(symbol, period='3y'):
    try:
        if not symbol.endswith('.NS'):
            symbol += '.NS'
            
        stock = yf.Ticker(symbol)
        try:
            hist = stock.history(period=period, interval='1d')
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None
        
        if hist.empty:
            return None
            
        # Calculate technical indicators
        hist['RSI'] = calculate_rsi(hist)
        hist['SMA_50'] = calculate_sma(hist, 50)
        hist['SMA_200'] = calculate_sma(hist, 200)
        hist['MACD'], hist['MACD_Signal'] = calculate_macd(hist)
        
        # Calculate Bollinger Bands
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['UpperBB'] = hist['MA20'] + (2 * hist['Close'].rolling(window=20).std())
        hist['LowerBB'] = hist['MA20'] - (2 * hist['Close'].rolling(window=20).std())
        
        # Calculate Volume SMA
        hist['Volume_SMA'] = hist['Volume'].rolling(window=20).mean()
        
        pivot_points = calculate_pivot_points(hist)
        hist = pd.concat([hist, pivot_points], axis=1)
        
        return hist.dropna()
    except Exception as e:
        print(f"Error processing data for {symbol}: {e}")
        return None

def create_dataset(dataset, look_back=60):
    X, Y = [], []
    for i in range(look_back, len(dataset)):
        X.append(dataset[i-look_back:i, :])
        Y.append(dataset[i, 0])
    return np.array(X), np.array(Y)

def predict_future(model, last_sequence, days, scaler, feature_size):
    predictions = []
    current_sequence = last_sequence.copy()
    
    for _ in range(days):
        # Reshape the input correctly for LSTM (batch_size, timesteps, features)
        input_seq = current_sequence.reshape(1, current_sequence.shape[0], current_sequence.shape[1])
        next_pred = model.predict(input_seq, verbose=0)
        
        new_row = np.zeros((1, feature_size))
        new_row[0, 0] = next_pred[0, 0]
        
        if feature_size > 1:
            # Carry forward other features (with some noise to simulate real market)
            new_row[0, 1:] = current_sequence[-1, 1:] * np.random.normal(1, 0.01, feature_size-1)
        
        # Update the sequence: remove first element and add new prediction
        new_sequence = np.vstack([current_sequence[1:], new_row])
        current_sequence = new_sequence
        
        # Inverse transform the prediction
        unscaled_pred = scaler.inverse_transform(new_row)[0, 0]
        predictions.append(unscaled_pred)
    
    return predictions

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    symbol = data['symbol']
    days = int(data['days'])
    
    try:
        # Get historical data
        hist_data = get_stock_data(symbol)
        if hist_data is None or len(hist_data) < 100:
            return jsonify({'error': 'Insufficient historical data available for this stock. Please try another.'}), 400
        
        # Select features for prediction
        features = hist_data[['Close', 'RSI', 'SMA_50', 'SMA_200', 'MACD', 'Volume', 'UpperBB', 'LowerBB', 'PP']].values
        
        # Scale data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(features)
        
        # Create sequences
        look_back = 60
        X, y = create_dataset(scaled_data, look_back)
        
        if len(X) < 100:
            return jsonify({'error': 'Not enough data points for training. Please try another stock.'}), 400
            
        # Split data
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Build and train model
        model = build_lstm_model((X_train.shape[1], X_train.shape[2]))
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        model.fit(
            X_train, y_train, 
            epochs=50, 
            batch_size=32, 
            verbose=0,
            validation_split=0.2,
            callbacks=[early_stop]
        )
        
        # Evaluate model
        test_loss = model.evaluate(X_test, y_test, verbose=0)
        last_sequence = X[-1]
        
        # Ensure last_sequence has the correct shape
        if len(last_sequence.shape) == 2:
            last_sequence = last_sequence.reshape(1, *last_sequence.shape)
        
        future_predictions = predict_future(model, last_sequence[0], days, scaler, features.shape[1])
        
        # Rest of your prediction code...
        # Generate dates for predictions
        last_date = hist_data.index[-1].to_pydatetime()
        prediction_dates = [last_date + timedelta(days=i) for i in range(1, days+1)]
        
        # Prepare historical data for response
        history = [{
            'date': date.strftime('%Y-%m-%d'),
            'close': close,
            'rsi': rsi,
            'sma_50': sma_50,
            'sma_200': sma_200,
            'volume': volume,
            'upper_bb': upper_bb,
            'lower_bb': lower_bb,
            'pp': pp
        } for date, close, rsi, sma_50, sma_200, volume, upper_bb, lower_bb, pp in zip(
            hist_data.index, 
            hist_data['Close'], 
            hist_data['RSI'], 
            hist_data['SMA_50'], 
            hist_data['SMA_200'],
            hist_data['Volume'],
            hist_data['UpperBB'],
            hist_data['LowerBB'],
            hist_data['PP']
        )]
        
        # Prepare predictions for response
        predictions = [{
            'date': date.strftime('%Y-%m-%d'),
            'price': float(price)
        } for date, price in zip(prediction_dates, future_predictions)]
        
        # Calculate accuracy metrics
        test_predictions = model.predict(X_test, verbose=0)
        test_predictions_expanded = np.zeros((len(test_predictions), features.shape[1]))
        test_predictions_expanded[:, 0] = test_predictions.flatten()
        if features.shape[1] > 1:
            test_predictions_expanded[:, 1:] = X_test[:, -1, 1:]
        
        test_predictions_actual = scaler.inverse_transform(test_predictions_expanded)[:, 0]
        y_test_expanded = np.zeros((len(y_test), features.shape[1]))
        y_test_expanded[:, 0] = y_test.flatten()
        if features.shape[1] > 1:
            y_test_expanded[:, 1:] = X_test[:, -1, 1:]
        
        y_test_actual = scaler.inverse_transform(y_test_expanded)[:, 0]
        
        # Calculate directional accuracy
        direction_correct = np.sum(
            (np.sign(test_predictions_actual[1:] - test_predictions_actual[:-1]) == 
            np.sign(y_test_actual[1:] - y_test_actual[:-1]))
        ) / len(test_predictions_actual[1:])
        
        # Calculate percentage accuracy
        accuracy = 100 * (1 - np.mean(np.abs((test_predictions_actual - y_test_actual) / (y_test_actual + 1e-7))))
        
        # Get current market status
        current_rsi = hist_data['RSI'].iloc[-1]
        market_status = "Neutral"
        if current_rsi > 70:
            market_status = "Overbought"
        elif current_rsi < 30:
            market_status = "Oversold"
        
        # Get current price position relative to Bollinger Bands
        current_price = hist_data['Close'].iloc[-1]
        upper_band = hist_data['UpperBB'].iloc[-1]
        lower_band = hist_data['LowerBB'].iloc[-1]
        
        bb_position = ""
        if current_price > upper_band:
            bb_position = "Above Upper Band (Potential Overbought)"
        elif current_price < lower_band:
            bb_position = "Below Lower Band (Potential Oversold)"
        else:
            bb_position = "Within Bands"
        
        return jsonify({
            'history': history[-100:],  # Last 100 days of history
            'predictions': predictions,
            'accuracy': float(accuracy),
            'directional_accuracy': float(direction_correct * 100),
            'model_loss': float(test_loss),
            'last_close': float(hist_data['Close'].iloc[-1]),
            'market_status': market_status,
            'bollinger_status': bb_position,
            'pivot_points': {
                'pp': float(hist_data['PP'].iloc[-1]),
                's1': float(hist_data['S1'].iloc[-1]),
                's2': float(hist_data['S2'].iloc[-1]),
                'r1': float(hist_data['R1'].iloc[-1]),
                'r2': float(hist_data['R2'].iloc[-1])
            },
            'technical_indicators': {
                'rsi': float(hist_data['RSI'].iloc[-1]),
                'macd': float(hist_data['MACD'].iloc[-1]),
                'macd_signal': float(hist_data['MACD_Signal'].iloc[-1]),
                'sma_50': float(hist_data['SMA_50'].iloc[-1]),
                'sma_200': float(hist_data['SMA_200'].iloc[-1]),
                'bollinger_upper': float(upper_band),
                'bollinger_lower': float(lower_band)
            }
        })
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({'error': f"Prediction failed: {str(e)}"}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)