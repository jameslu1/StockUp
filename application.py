'''
This is a Flask application
API_KEY=REYK3P8B6YFO2GL6
'''

import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp

from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *

# import SQL
import sqlite3

# connect to database
connection = sqlite3.connect("database.db")
db = connection.cursor()

# initialize database
db.execute("CREATE TABLE IF NOT EXISTS 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 )")
connection.commit()

# Ensure environment variable is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Configure application
app = Flask(__name__)

'''
Beginning of starter code
'''

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Handle errors
def errorhandler(e):
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

'''
End of starter code
Credit to Harvard's CS50 pset7
'''

@app.route("/")
@login_required
def index():

    # Create a table to keep track of portfolio
    db = connection.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS 'portfolio' ('id' INTEGER NOT NULL, 'symbol' TEXT NOT NULL, 'shares' INTEGER NOT NULL, 'current_price' NUMERIC NOT NULL, 'total' NUMERIC NOT NULL)")
    connection.commit()

    # Get symbols
    db.execute("SELECT symbol, shares, current_price, total FROM portfolio WHERE id = ?", (session["user_id"],))
    portfolio=db.fetchall()
    size=len(portfolio)


    # Create list of stocks
    stocks=[]
    value=0.0
    for i in range(size):

        symbol=portfolio[i][0]
        shares=portfolio[i][1]
        price=portfolio[i][2]
        total=portfolio[i][3]

        # Check if symbol is recieved from API
        error=0
        getSymbol=lookup(symbol)
        if not getSymbol:
            error=1

        if error==0:
            # Update current stock price if symbol is recieved
            db.execute("UPDATE portfolio SET current_price=? WHERE id=? AND symbol=?", (getSymbol['price'], session["user_id"], symbol,))
            connection.commit()
            db.execute("SELECT current_price FROM portfolio WHERE id=? AND symbol=?", (session["user_id"], symbol,))
            price=db.fetchone()[0]

        # Calculate percent change
        pChange=(float(shares)*price-total)/total
        if pChange>0:
            growth=1
        elif pChange<0:
            growth=-1
        else:
            growth=0

        # Populate list
        stock={
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": float(shares)*price,
            "growth": growth if error==0 else 0,
            "pChange": percent(pChange) if error==0 else percent(0)
        }
        value+=stock['total']
        stocks.append(stock)

    # Get user balance
    db.execute("SELECT cash FROM users WHERE id = ?", (session["user_id"],))
    balance=db.fetchone()[0]
    value+=balance

    return render_template("index.html", stocks=stocks, balance=usd(balance), total=usd(value))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology_buy("Please provide a valid stock symbol")

        #Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology_buy("Please provide a number of shares")
        elif not int(request.form.get("shares"))>0:
            return apology_buy("Please provide a valid number of shares")

        # Ensure symbol is valid
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology_buy("Invalid stock symbol")

        # Select user balance
        db = connection.cursor()
        db.execute("SELECT cash FROM users WHERE id = ?", (session["user_id"],))
        row=db.fetchone()
        balance=float(row[0])

        # Check if user has enough money
        total=float(request.form.get("shares"))*float(stock['price'])
        if balance-total < 0:
            return apology_buy("Insufficient balance")

        # Populate table
        db.execute("SELECT symbol FROM portfolio WHERE id = ? AND symbol = ?", (session["user_id"], stock['symbol'],))
        symbol=db.fetchone()

        if symbol:

            # If symbol already exists, update existing shares and total
            db.execute("SELECT shares FROM portfolio where id = ? AND symbol = ?", (session["user_id"], stock['symbol'],))
            shares=db.fetchone()
            shares=shares[0]+int(request.form.get("shares"))
            db.execute("SELECT total FROM portfolio where id = ? AND symbol = ?", (session["user_id"], stock['symbol'],))
            totalValue=db.fetchone()
            totalValue=totalValue[0]+total
            db.execute("UPDATE portfolio SET shares=?, total=? WHERE id=? AND symbol=?", (shares, totalValue, session["user_id"], stock['symbol'],))
            connection.commit()

        else:

            # If symbol is new, insert new row
            db.execute("INSERT INTO portfolio (id, symbol, shares, total) VALUES(?, ?, ?, ?)", (session["user_id"], stock['symbol'], int(request.form.get("shares")), total,))
            connection.commit()

        # Update balance
        balance -= total
        db.execute("UPDATE users SET cash=? WHERE id=?", (balance, session["user_id"],))
        connection.commit()
        return render_template("buy.html", stock=stock, shares=request.form.get("shares"), total=usd(total), balance=usd(balance))

    # User reached route via GET
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology_login("Please provide a username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology_login("Please provide a password", 403)

        # Query database for username
        db = connection.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))

        # Ensure username exists and password is correct
        row=db.fetchone()
        if not row or not check_password_hash(row[2], request.form.get("password")):
            return apology_login("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology_quote("Please provide a valid stock symbol")

        # Ensure symbol is valid
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology_quote("Invalid symbol")
        return render_template("quote.html", stock=stock, value=usd(float(stock['price'])))

    # User reached route via GET
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology_register("Please provide a valid username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology_register("Please provide a valid password")

        # Ensure password and verified password are the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology_register("Passwords do not match")

        # Ensure username doesn't already exist
        db = connection.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        row=db.fetchone()
        if row:
            return apology_register("Username already exists")

        # insert the new user into users, storing the hash of the user's password
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (request.form.get("username"), generate_password_hash(request.form.get("password")),))
        connection.commit()

        # remember which user has logged in
        db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        row=db.fetchone()
        session["user_id"] = row[0]

        # redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    return render_template("sell.html")


# Run flask program
if __name__=='__main__':
    app.run()