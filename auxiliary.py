import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(isbn):
    """Lookup goodreads review number and score
       from api of goodreads.com
    """
    # setup a return value if various errors
    default = {}
    default["review_num"] = "Not available"
    default["score"] = "Not available"

    # Check for environment variable
    if not os.getenv("API_KEY"):
        return default
    url = "https://www.goodreads.com/book/review_counts.json"
    parameters = {
        "key": os.getenv("API_KEY"),
        "isbns": isbn
    }
    try:
        response = requests.get("https://www.goodreads.com/book/review_counts.json", params=parameters)
        response.raise_for_status()
    except requests.RequestException:
        return default
    
    # Parse response
    try:
        data = response.json()
        return {
            "review_num": data["books"][0]["work_ratings_count"],
            "score": data["books"][0]["average_rating"]
        }
    except (KeyError, TypeError, ValueError):
        return default


def commafy(value):
    """Format value with commas."""
    return f"{value:,}"
