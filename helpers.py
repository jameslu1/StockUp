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
        # use the following code if app is executed on a command line
        #url = f"https://www.alphavantage.co/query?apikey={os.getenv('API_KEY')}&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol={symbol}"
        url = "https://www.alphavantage.co/query?apikey="+str(os.getenv('API_KEY'))+"&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol="+str(symbol)
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

# Sort users using merge sort
def sort_users(users):

    if len(users)>1:
        mid = len(users)//2
        lefthalf = users[:mid]
        righthalf = users[mid:]

        sort_users(lefthalf)
        sort_users(righthalf)

        i=0
        j=0
        k=0
        while i < len(lefthalf) and j < len(righthalf):
            if lefthalf[i]['total'] > righthalf[j]['total']:
                users[k]=lefthalf[i]
                i+=1
            else:
                users[k]=righthalf[j]
                j+=1
            k+=1

        while i < len(lefthalf):
            users[k]=lefthalf[i]
            i=i+1
            k=k+1

        while j < len(righthalf):
            users[k]=righthalf[j]
            j=j+1
            k=k+1

    return(users)

def percent_change(a,b):
    return float((a-b)/b)

# Formats value as US Dollar
def usd(value):
    return "$"+str(round(value, 2))

# Formats value as percent
def percent(value):
    value*=100
    if value>0:
        value=abs(value)
        return str(round(value, 2))+"%"
    elif value<0:
        value=abs(value)
        return "-"+str(round(value, 2))+"%"
    else:
        return "0.00%"
