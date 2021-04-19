import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy import text
# from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from psycopg2.errors import UniqueViolation
import requests


app = Flask(__name__, instance_relative_config=True)

app.config.from_pyfile('config.py')
# # Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# # Configure session to use filesystem
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"


Session(app)

# Set up database
engine = create_engine(app.config['DATABASE_URL'])
# db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if(session.get('user')):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return decorated


@app.route("/")
def index():
    title = "<p>Project One: Book Review site</p>"
    content = "<p>Wesen Tadesse - ATR/5878/10 - IT </p>"
    link = "<a href=\"{}\"><p>click to login</p></a>".format(url_for('login'))
    return "{title}<br>{content}<br>{link}".format(title=title, content=content, link=link)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if(request.method == 'POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        if(remember == 'on'):
            session.permanent = True
        else:
            session.permanent = False

        user = User(username, password)
        try:
            sql = text("select id, username, password from public.\"Users\" where username=\'{username}\';".format(
                username=username))
            result = engine.execute(sql).fetchone()
        except Exception as e:
            return "Server connection refused"

        if(not result):
            return render_template('login.html', error='Username not found')

        print(result, password)
        user.setID(result[0])

        if(check_password_hash(result[2], password)):
            session['user'] = user.id
            return redirect(url_for('searchBooks'))
        else:
            return render_template('login.html', error='Password incorrect')

    return render_template('login.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():

    if(request.method == 'POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username, password)

        if(len(password) < 8):
            return render_template('signup.html', error="Password is needs to be 8 characters")

        hashed_password = generate_password_hash(password, 'sha256')

        try:
            engine.execute("insert into public.\"Users\" (username, password) values ('{username}', '{password}')".format(
                username=username, password=hashed_password))
        except:
            return render_template('signup.html', error="Username not unique")

        try:
            result = engine.execute('select id from public.\"Users\" where username=\'{username}\''.format(
                username=username)).fetchone()
        except Exception as e:
            return render_template('signup.html', error="Error:{}".format(e))

        session['user'] = result[0]

        return redirect(url_for('searchBooks'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session['user'] = None
    return redirect(url_for('login'))


@app.route('/import')
def importBooks():
    return ''

# Search looks throught book database and finds all the books that match
# search parameters


@app.route('/search', methods=['GET', 'POST'])
@login_required
def searchBooks():
    print(session)
    searchResult = []
    if(request.method == 'POST'):
        # DATABASE CODE
        searchInput = request.form.get('search')

        # check to see if any portion of the text matches with the search input
        sqlISBN = "select * from \"Books\" where isbn like '%{}%'".format(
            searchInput)
        sqlBookTitle = "select * from \"Books\" where book_title like '%{}%'".format(
            searchInput)
        sqlBookAuthor = "select * from \"Books\" where book_author like '%{}%'".format(
            searchInput)

        statement = text(sqlISBN + ' union ' + sqlBookTitle +
                         ' union ' + sqlBookAuthor + ' limit 20;')
        try:
            results = engine.execute(statement)
        except Exception as e:
            return render_template('search.html', results=[], error="Error: {}".format(e))

        for book in results:
            searchResult.append(
                Book(book[0].strip(), book[1].strip(), book[2].strip(), book[3]))

        print(searchResult)
        if(len(searchResult) == 0):
            return render_template('search.html', result=searchResult,
                                   error="No books match search")
    if(len(searchResult) > 9):
        searchResult = searchResult[0:9]

    return render_template('search.html', result=searchResult)

# Book page lets users query specific books and get info about them
# Also shows reviews


@app.route('/book/<isbn>', methods=['GET', 'POST'])
@login_required
def viewBook(isbn):

    # BOOK DATABASE CODE
    sqlBook = "select * from \"Books\" where isbn like '%{}%';".format(isbn)

    try:
        result = engine.execute(text(sqlBook)).fetchone()
    except Exception as e:
        return 'Error:{}'.format("174 - " + str(e) + " 0~ " + sqlBook)

    if(not result):
        return 'Error:{}'.format('book not found - ' + sqlBook)

    # CREATE BOOK
    book = Book(result[0], result[1], result[2], result[3])

    # Review
    userReviews = []

    # user review are searched seperately so that they can remain at the top
    # USER REVIEW DATABASE CODE
    sqlUserReview = "select * from \"Review\" where userid={userid} AND isbn like '%{isbn}%'".format(
        userid=session['user'], isbn=book.ISBN)
    try:
        reviewResult = engine.execute(text(sqlUserReview)).fetchone()
    except Exception as e:
        return 'Error:{}'.format(e)

    if(reviewResult):
        userReview = Review(reviewResult[0], reviewResult[1],
                            reviewResult[2], reviewResult[3],
                            reviewResult[4])
        userReviews.append(userReview)
        print("user review", userReview)

    # OTHER REVIEW DATABASE CODE
    sqlOtherReview = "select * from \"Review\" where isbn like '%{isbn}%' and userid!={userid}".format(
        isbn=book.ISBN, userid=session['user'])

    try:
        oReviewResult = engine.execute(text(sqlOtherReview))
    except Exception as e:
        return 'Error:{}'.format(e)

    # Fill arrray
    for r in oReviewResult:
        oReview = Review(r[0], r[1],
                         r[2], r[3], r[4])
        userReviews.append(oReview)

    # AVERAGE RATING
    # AVERAGE FROM THIS DATABASE
    average = 0
    if(len(userReviews) != 0):
        sum = 0
        for r in userReviews:
            sum += r.rating
        average = sum / len(userReviews)
    book.setAverageRating(int(average))

    # Get data from openlibrary api
    apiData = getAPIData(book.ISBN.strip())

    if(not apiData):
        apiData = {}
        apiData['subjects'] = ['subjects cannot be found']

    if(not apiData.get('description')):
        apiData['description'] = 'description cannot be found'

    if(request.method == 'POST'):
        # Username
        sqlUser = "select username from \"Users\" where id={};".format(
            session['user'])
        try:
            sqlUsername = engine.execute(text(sqlUser)).fetchone()
        except Exception as e:
            return 'Error:{}'.format(e)

        # POST DATABASE CODE
        # PUSH REVIEW TO DATABASE
        starRating = request.form.get('rating')
        comment = request.form.get('comment')

        sqlInsertReview = "insert into \"Review\" (userid, isbn, username, review, rating)"
        sqlInsertReview += "values ({userID},'{ISBN}','{username}','{review}',{rating});"
        sqlInsertReview = sqlInsertReview.format(userID=session['user'], ISBN=book.ISBN,
                                                 username=sqlUsername[0], review=comment, rating=int(starRating))

        try:
            engine.execute(text(sqlInsertReview))
            userReviews.insert(0, Review(
                session['user'], book.ISBN, sqlUsername[0], comment, int(starRating)))
        except Exception as e:
            print(e)

    return render_template('book.html', book=book, reviews=userReviews[0:10], subjects=apiData['subjects'], description=apiData['description'])

# Get Data from Open Library API online
# Data includes subjects and descriptions


def getAPIData(ISBN):
    OLE = requests.get('https://openlibrary.org/api/books?bibkeys=ISBN:{}&jscmd=details&format=json'.format(
        ISBN
    ))

    jsonOLE = OLE.json()
    if(len(jsonOLE) == 0):
        return
    # The Open Library tends to be inconsistent with the API
    if(not jsonOLE['ISBN:{}'.format(ISBN)]['details'].get('subjects')):
        return

    subjects = jsonOLE['ISBN:{}'.format(ISBN)]['details']['subjects'][0:]

    worklink = jsonOLE['ISBN:{}'.format(
        ISBN)]['details']['works'][0]['key']

    worklink = 'https://openlibrary.org' + worklink + '.json'

    OLW = requests.get(worklink)

    jsonOLW = OLW.json()

    if(len(jsonOLW) == 0):
        return {'subjects': subjects}

    if(not jsonOLW.get('description')):
        return {'subjects': subjects}

    description = jsonOLW["description"]

    return {'subjects': subjects, 'description': description}

# Let user access data as json file


@app.route('/api/<isbn>')
@login_required
def apiBook(isbn):
    # BOOK DATABASE CODE
    sqlBook = "select * from \"Books\" where isbn like '%{}%';".format(isbn)

    try:
        result = engine.execute(text(sqlBook)).fetchone()
    except Exception as e:
        return 'Error:{}'.format("174 - " + str(e) + " 0~ " + sqlBook)

    if(not result):
        return jsonify({'message': 'ISBN not found'})
    # CREATE BOOK
    book = Book(result[0], result[1], result[2], result[3])

    jsonDict = {'isbn': book.ISBN.strip(),
                'title': book.bookTitle,
                'author': book.bookAuthor,
                'date': book.publicationDate}

    # Review
    userReviews = []

    # REVIEW DATABASE CODE
    sqlOtherReview = "select * from \"Review\" where isbn like '%{isbn}%'".format(
        isbn=book.ISBN, userid=session['user'])

    try:
        oReviewResult = engine.execute(text(sqlOtherReview))
    except Exception as e:
        return jsonify({'message': str(e)}), 404

    if(not oReviewResult):
        jsonDict['average_rating'] = 0
        return jsonify(jsonDict)

    # Fill list
    for r in oReviewResult:
        oReview = Review(r[0], r[1],
                         r[2], r[3], r[4])
        userReviews.append(oReview)

    # AVERAGE RATING
    # AVERAGE FROM THIS DATABASE
    average = 0
    if(len(userReviews) != 0):
        sum = 0
        for r in userReviews:
            sum += r.rating
        average = sum / len(userReviews)
    book.setAverageRating(int(average))
    jsonDict['average_rating'] = book.rating

    return jsonify(jsonDict)


if __name__ == "__main__":
    app.run()
