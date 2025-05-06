from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class PortfolioForm(FlaskForm):
    name = StringField('Portfolio Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Portfolio')

class StockHoldingForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    average_price = FloatField('Average Price', validators=[DataRequired()])
    submit = SubmitField('Add Stock')

class WatchListForm(FlaskForm):
    name = StringField('Watchlist Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Create Watchlist')

class BrokerageConnectionForm(FlaskForm):
    brokerage = SelectField('Brokerage', choices=[
        ('groww', 'Groww'),
        ('zerodha', 'Zerodha'),
        ('upstox', 'Upstox')
    ], validators=[DataRequired()])
    api_key = StringField('API Key', validators=[DataRequired()])
    api_secret = PasswordField('API Secret', validators=[DataRequired()])
    submit = SubmitField('Connect')

class PredictionForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    days = IntegerField('Prediction Days', validators=[DataRequired()])
    submit = SubmitField('Predict')
