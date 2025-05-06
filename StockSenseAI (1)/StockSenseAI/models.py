from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    portfolios = db.relationship('Portfolio', backref='user', lazy=True)
    watchlists = db.relationship('WatchList', backref='user', lazy=True)
    transactions = db.relationship('StockTransaction', backref='user', lazy=True)
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    brokerage_accounts = db.relationship('BrokerageAccount', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    holdings = db.relationship('StockHolding', backref='portfolio', lazy=True)

    def __repr__(self):
        return f'<Portfolio {self.name}>'

class StockHolding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StockHolding {self.symbol}>'

class WatchList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), default="Default Watchlist")
    stocks = db.Column(db.Text, default='[]')  # JSON string of stock symbols
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<WatchList {self.name}>'

class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    brokerage_account_id = db.Column(db.Integer, db.ForeignKey('brokerage_account.id'), nullable=True)

    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.symbol}>'

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    prediction_days = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prediction {self.symbol}>'

class BrokerageAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    brokerage_name = db.Column(db.String(50), nullable=False)  # 'groww', 'zerodha', 'upstox'
    account_id = db.Column(db.String(100), nullable=False)
    access_token = db.Column(db.String(256))
    refresh_token = db.Column(db.String(256))
    token_expiry = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    transactions = db.relationship('StockTransaction', backref='brokerage_account', lazy=True)

    def __repr__(self):
        return f'<BrokerageAccount {self.brokerage_name}>'
