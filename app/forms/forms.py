# app/forms/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    department = StringField('Department', validators=[DataRequired(), Length(min=1, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')

class SigninForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign In')

class MenuForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(min=1, max=100)])
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class OrderForm(FlaskForm):
    menu_item_id = IntegerField('Menu Item ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Place Order')