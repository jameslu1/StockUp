# Contains helper functions for flask application

import csv
import os
import urllib.request

from flask import redirect, render_template, request, session
from functools import wraps

#Error checking
def apology(message, code=400):
    return render_template("apology.html", message=message, code=code), code

def apology_login(message, code=400):
    return render_template("login.html", message=message, code=code), code

def apology_register(message, code=400):
    return render_template("register.html", message=message, code=code), code

def apology_quote(message, code=400):
    return render_template("quote.html", message=message, code=code), code

def apology_buy(message, code=400):
    return render_template("buy.html", message=message, code=code), code

def apology_sell(message, symbols, code=400):
    return render_template("sell.html", symbols=symbols, message=message, code=code), code

#Checks if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # Reject symbol if it contains comma
    if "," in symbol:
        return None

    # Query Alpha Vantage for quote
    # https://www.alphavantage.co/documentation/
    try:

        # Get CSV file
        # Use following code only if running flask from command line:
        # url = f"https://www.alphavantage.co/query?apikey={os.getenv('API_KEY')}&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol={symbol}"
        # Otherwise, use next line
        url = f"https://www.alphavantage.co/query?apikey=REYK3P8B6YFO2GL6&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol={symbol}"
        webpage = urllib.request.urlopen(url)
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
        next(datareader)
        row = next(datareader)

        # Ensure stock exists
        try:
            price = float(row[4])
        except:
            return None

        # Return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
        return {
            "price": price,
            "symbol": symbol.upper()
        }

    except:
        return None

# Formats value as US Dollar
def usd(value):
    return f"${value:,.2f}"

# Formats value as percent
def percent(value):
    value*=100
    if value>0:
        value=abs(value)
        return f"{value:,.2f}%"
    elif value<0:
        value=abs(value)
        return f"-{value:,.2f}%"
    else:
        return "0.00%"