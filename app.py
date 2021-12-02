import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///databases.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get info on username and cash remaining
    user_info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    username = user_info[0]["username"]
    cash_remaining = usd(float(user_info[0]["cash"]))

    # Get info about stock porfolio info from database
    stock_info = db.execute("SELECT user_id, stock, SUM(shares) AS total_shares FROM portfolio WHERE user_id = ? GROUP BY stock ORDER BY stock", session["user_id"])

    # If user does not own any stocks load page with special note
    if not stock_info:
        screenload = 0
        cummulative_value = cash_remaining
        return render_template("index.html", username=username, cash_remaining=cash_remaining, screenload=screenload, cummulative_value=cummulative_value)

    # Create list to store stock info for webpage
    stocks_owned = []
    cummulative_value = float(user_info[0]["cash"])

    # Get info about each stock and store into dictionary
    for i in range(len(stock_info)):
        # Ticker and stock info
        ticker = stock_info[i]["stock"]
        total_shares = stock_info[i]["total_shares"]

        # Get current info on stock
        lookup_results = lookup(ticker)
        company = lookup_results["name"]
        current_price = lookup_results["price"]
        total_value = float(current_price) * float(total_shares)

        # Update total value of all assets
        cummulative_value += total_value

        # define dictionary that has all values for table for stock
        stock_details = {}
        stock_details["ticker"] = ticker
        stock_details["name"] = company
        stock_details["shares"] = total_shares
        stock_details["value"] = usd(current_price)
        stock_details["total_value"] = usd(total_value)

        # apprend each dictionary into list
        stocks_owned.append(stock_details)

    # load screen and load appropriate variables into HTML
    screenload = 1
    return render_template("index.html", username=username, cash_remaining=cash_remaining, screenload=screenload, stocks_owned=stocks_owned, cummulative_value=usd(cummulative_value))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password is re-entered
        elif not request.form.get("confirmation"):
            return apology("must re-enter password", 400)

        # Ensure password is re-entered correctly
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("please reenter: passwords do not match", 400)

        # Ensure that username does not exist
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) >= 1:
            return apology("username already in use", 400)

        # Temporarily save username and password for entry into database
        input1 = request.form.get("username")
        input2 = generate_password_hash(request.form.get("password"))
        
        # save username and password into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", input1, input2)

        # LOG IN USER: Get user_id and get session_id to log in user
        user = db.execute("SELECT * FROM users WHERE username = ?", input1)
        session["user_id"] = user[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # load page for register
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # Ensure user provided form input
        ticker_sym = request.form.get("symbol")
        shares_number = request.form.get("shares")
        if not ticker_sym or not shares_number:
            return apology("Stock Ticker or Shares Amount is Incomplete")

        # Ensure provided shares values are positive integers
        try:
            n = int(shares_number) 
        except ValueError:
            return apology("invalid shares entry")
        else:
            if n <= 0:
                return apology("invalid shares entry")

        # saving search query
        lookup_results = lookup(ticker_sym)
        if lookup_results == None:
            return apology("Stock does not exist")

        # Determine if stock ticker submitted is in portfolio
        stocks_summary = db.execute("SELECT user_id, stock, SUM(shares) AS total_shares FROM portfolio WHERE stock = ? AND user_id = ? GROUP BY user_id, stock", ticker_sym, session["user_id"])
        if not stocks_summary:
            return apology("Stock not owned")

        # Ensure user is not selling more stocks than they already own
        if float(stocks_summary[0]["total_shares"]) < float(shares_number):
            return apology("Selected more shares than currently owned")

        # Get user info on cash in their account (to accurately update cash amount later)
        user_info = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash_update = float(user_info[0]["cash"])

        # Iteratively update portfolio database to accurately reflect the number of shares left
        shares_to_be_sold = int(shares_number)
        while shares_to_be_sold > 0:

            # Querey for potfolio entrey with the lowest initial price and first/oldest entry for a given stock
            # This allows the user to maximize profit at the time of selling 
            portfolio_entry = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND stock = ? AND status = 'owned' GROUP BY stock HAVING MIN(unit_purchase_price) AND MIN(purchase_id)", session["user_id"], ticker_sym)
            
            # If porfolio entry has fewer shares than the number of shares being sold, sell and delete all the shares in log
            # Then repeat process until the intended number of shares to sell are sold
            if float(portfolio_entry[0]["shares"]) <= float(shares_to_be_sold):
                db.execute("DELETE FROM portfolio WHERE purchase_id = ?", portfolio_entry[0]["purchase_id"])
                shares_to_be_sold -= int(portfolio_entry[0]["shares"])

            # If the portfolio entry has more shares than are being sold, sell only the applicable number of shares
            # and keep the porfolio entry with remaining number of stocks
            else:
                shares_left = float(portfolio_entry[0]["shares"]) - shares_to_be_sold
                db.execute("UPDATE portfolio SET shares = ? WHERE purchase_id = ?", shares_left, portfolio_entry[0]["purchase_id"])
                shares_to_be_sold = 0

        # Determine sell value for stocks and update transaction history database and cash amount
        sell_value = float(shares_number) * lookup_results["price"]
        cash_update += sell_value
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash_update, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, type, stock, shares, unit_price, cash_balance) VALUES (?, 'Sale', ?, ?, ?, ?)", session["user_id"], ticker_sym, shares_number, lookup_results["price"], cash_update)

        # Redirect to main page
        return redirect('/')

    else:
        # Save all stocks that are part of portfolio in list for HTML page
        tickers = db.execute("SELECT DISTINCT stock FROM portfolio WHERE user_id = ?", session["user_id"])
        
        # Load page with HTML
        return render_template("sell.html", tickers=tickers)


#### ERROR HANDLING ####
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)