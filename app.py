from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from dateutil.parser import parse
import requests
import json
import sys
import os
import redis

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booklog.db'
app.config['DEBUG'] = True
SQLALCHEMY_BINDS = {
    'readinglist': 'sqlite:///readinglist.db'
}

rdb = redis.from_url(os.environ.get("REDISCLOUD_URL"))

db = SQLAlchemy(app)

class Booklog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    author = db.Column(db.String(200),nullable=True)
    page_count = db.Column(db.Integer,nullable=True)
    pub_date = db.Column(db.String(4),nullable=True)
    volume_id = db.Column(db.String(15),nullable=True)
    img_url = db.Column(db.String(100),nullable=True)
    date_started = db.Column(db.Date,default=date.today)
    date_finished = db.Column(db.Date,default=None,nullable=True)
    genres = db.Column(db.Text(),nullable=True)

    # Called every time a new element is added to the db
    def __repr__(self):
        return '<book %r>' % self.id

class ReadingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    author = db.Column(db.String(200),nullable=True)
    page_count = db.Column(db.Integer,nullable=True)
    pub_date = db.Column(db.String(4),nullable=True)
    volume_id = db.Column(db.String(15),nullable=True)
    img_url = db.Column(db.String(100),nullable=True)

    def __repr__(self):
        return '<book %r>' % self.id

books = Booklog.query.order_by(Booklog.date_started).all()
readingListBooks = ReadingList.query.order_by(ReadingList.title).all()

rdb.set('sort','')
rdb.set('sortReadList','')
rdb.set('sortAtoZ','True')
rdb.set('sortAtoZReading','True')
rdb.set('showImages','False')
rdb.set('showImagesReadingList','False')


@app.route('/')
def index():
    global books
    global readingListBooks
    showImages = (rdb.get('showImages').decode('utf-8') == 'True')
    showImagesReadingList = (rdb.get('showImagesReadingList').decode('utf-8') == 'True')
    sort = rdb.get('sort').decode('utf-8')

    for book in books:
        books_json = {
            'title':book.title,
            'author':book.author,
            'page_count':book.page_count,
            'pub_date':book.pub_date
        }
        books_json = json.dumps(books_json)
    
    # Create 2d array for genre listings
    genres = []
    for book in books:
        genre_list = book.genres.split(',')
        genres.append(genre_list)

    print('rendering index.html as normal')

    return render_template('index.html', books=books, booksToRead=readingListBooks, showImages=showImages, showImagesReadingList=showImagesReadingList, sort=sort, sortReadList=sortReadList, genres=genres)


@app.route('/displayMode/', methods=['POST'])
def switchDisplayMode():
    showImages = (rdb.get('showImages').decode('utf-8') == 'True')

    showImages = not showImages

    img_str = 'True' if showImages else 'False'
    rdb.set('showImages',img_str)

    return redirect('/')


@app.route('/displayModeReadingList/', methods=['POST'])
def switchReadingDisplay():
    showImagesReadingList = (rdb.get('showImagesReadingList').decode('utf-8') == 'True')

    showImagesReadingList = not showImagesReadingList

    img_str = 'True' if showImagesReadingList else 'False'
    rdb.set('showImagesReadingList',img_str)

    return redirect('/')


@app.route('/sort_log/', methods=['POST','GET'])
def sortLog():
    global books
    sort = rdb.get('sort').decode('utf-8')
    sortAtoZ = (rdb.get('sortAtoZ').decode('utf-8') == 'True')

    if request.method == 'POST':
        try:
            request.form['sortAuthor']
            print('sorting by author')
            books = Booklog.query.order_by(Booklog.author).all()
            if not sortAtoZ:
                sort = 'authorUp'
                books.reverse()
                sortAtoZ = True
            else:
                sort = 'authorDown'
                sortAtoZ = False
        except:
            pass
        try:
            request.form['sortTitle']
            print('sorting by title')
            books = Booklog.query.order_by(Booklog.title).all()
            if not sortAtoZ:
                sort = 'titleUp'
                books.reverse()
                sortAtoZ = True
            else:
                sort = 'titleDown'
                sortAtoZ = False
        except:
            pass
        try:
            request.form['sortPageCount']
            print('sorting by page count')
            books = Booklog.query.order_by(Booklog.page_count).all()
            if not sortAtoZ:
                sort = 'pagesUp'
                books.reverse()
                sortAtoZ = True
            else:
                sort = 'pagesDown'
                sortAtoZ = False
        except:
            pass
        try:
            request.form['sortPubDate']
            print('sorting by publication date')
            books = Booklog.query.order_by(Booklog.pub_date).all()
            if not sortAtoZ:
                sort = 'pubUp'
                books.reverse()
                sortAtoZ = True
            else:
                sort = 'pubDown'
                sortAtoZ = False
        except:
            pass
        try:
            request.form['sortDateAdded']
            print('sorting by date added')
            books = Booklog.query.order_by(Booklog.date_started).all()
            if not sortAtoZ:
                sort = 'addedUp'
                books.reverse()
                sortAtoZ = True
            else:
                sort = 'addedDown'
                sortAtoZ = False
        except:
            pass

        sortAtoZ = 'True' if sortAtoZ else 'False'
        rdb.set('sort',sort)
        rdb.set('sortAtoZ',sortAtoZ)
        return redirect('/')


    else:
        if sort == 'titleUp':
            books = Booklog.query.order_by(Booklog.title).all()
        elif sort == 'titleDown':
            books = Booklog.query.order_by(Booklog.title).all()
            books.reverse()
        elif sort == 'authorUp':
            books = Booklog.query.order_by(Booklog.author).all()
        elif sort == 'authorDown':
            books = Booklog.query.order_by(Booklog.author).all()
            books.reverse()
        elif sort == 'pagesUp':
            books = Booklog.query.order_by(Booklog.page_count).all()
        elif sort == 'pagesDown':
            books = Booklog.query.order_by(Booklog.page_count).all()
            books.reverse()
        elif sort == 'pubUp':
            books = Booklog.query.order_by(Booklog.pub_date).all()
        elif sort == 'pubDown':
            books = Booklog.query.order_by(Booklog.pub_date).all()
            books.reverse()
        elif sort == 'addedUp':
            books = Booklog.query.order_by(Booklog.date_started).all()
        elif sort == 'addedDown':
            books = Booklog.query.order_by(Booklog.date_started).all()
            books.reverse()
        else:
            sort = 'addedUp'
            books = Booklog.query.order_by(Booklog.date_started).all()
    
    sortAtoZ = 'True' if sortAtoZ else 'False'
    rdb.set('sort',sort)
    rdb.set('sortAtoZ',sortAtoZ)
    return redirect('/')

@app.route('/sort_reading_list/', methods=['POST','GET'])
def sortReadingList():
    global readingListBooks
    sortReadList = rdb.get('sortReadList').decode('utf-8')
    sortAtoZReading = (rdb.get('sortAtoZReading').decode('utf-8') == 'True')

    if request.method == 'POST':
        try:
            request.form['sortAuthor']
            print('sorting by author')
            readingListBooks = ReadingList.query.order_by(ReadingList.author).all()
            if not sortAtoZReading:
                sortReadList = 'authorUp'
                readingListBooks.reverse()
                sortAtoZReading = True
            else:
                sortReadList = 'authorDown'
                sortAtoZReading = False
        except:
            pass
        try:
            request.form['sortTitle']
            print('sorting by title')
            readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
            if not sortAtoZReading:
                sortReadList = 'titleUp'
                readingListBooks.reverse()
                sortAtoZReading= True
            else:
                sortReadList = 'titleDown'
                sortAtoZReading = False
        except:
            pass
        try:
            request.form['sortPageCount']
            print('sorting by page count')
            readingListBooks = ReadingList.query.order_by(ReadingList.page_count).all()
            if not sortAtoZReading:
                sortReadList = 'pagesUp'
                readingListBooks.reverse()
                sortAtoZReading = True
            else:
                sortReadList = 'pagesDown'
                sortAtoZReading= False
        except:
            pass
        try:
            request.form['sortPubDate']
            print('sorting by publication date')
            readingListBooks = ReadingList.query.order_by(ReadingList.pub_date).all()
            if not sortAtoZReading:
                sortReadList = 'pubUp'
                readingListBooks.reverse()
                sortAtoZReading = True
            else:
                sortReadList = 'pubDown'
                sortAtoZReading = False
        except:
            pass
    else:
        if sortReadList == 'titleUp':
            readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
        elif sortReadList == 'titleDown':
            readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
            readingListBooks.reverse()
        elif sortReadList == 'authorUp':
            readingListBooks = ReadingList.query.order_by(ReadingList.author).all()
        elif sortReadList == 'authorDown':
            readingListBooks = ReadingList.query.order_by(ReadingList.author).all()
            readingListBooks.reverse()
        elif sortReadList == 'pagesUp':
            readingListBooks = ReadingList.query.order_by(ReadingList.page_count).all()
        elif sortReadList == 'pagesDown':
            readingListBooks = ReadingList.query.order_by(ReadingList.page_count).all()
            readingListBooks.reverse()
        elif sortReadList == 'pubUp':
            readingListBooks = ReadingList.query.order_by(ReadingList.pub_date).all()
        elif sortReadList == 'pubDown':
            readingListBooks = ReadingList.query.order_by(ReadingList.pub_date).all()
            readingListBooks.reverse()
        else:
            sortReadList = 'addedUp'
            readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
    
    sortAtoZReading = 'True' if sortAtoZReading else 'False'
    rdb.set('sortReadList',sortReadList)
    rdb.set('sortAtoZReading',sortAtoZReading)
    return redirect('/')

@app.route('/sort_all/', methods=['GET'])
def sortAll():
    global books
    global readingListBooks
    sort = rdb.get('sort').decode('utf-8')
    sortAtoZ = (rdb.get('sortAtoZ').decode('utf-8') == 'True')
    sortReadList = rdb.get('sortReadList').decode('utf-8')
    sortAtoZReading = (rdb.get('sortAtoZReading').decode('utf-8') == 'True')
    # Sort the log
    if sort == 'titleUp':
        books = Booklog.query.order_by(Booklog.title).all()
    elif sort == 'titleDown':
        books = Booklog.query.order_by(Booklog.title).all()
        books.reverse()
    elif sort == 'authorUp':
        books = Booklog.query.order_by(Booklog.author).all()
    elif sort == 'authorDown':
        books = Booklog.query.order_by(Booklog.author).all()
        books.reverse()
    elif sort == 'pagesUp':
        books = Booklog.query.order_by(Booklog.page_count).all()
    elif sort == 'pagesDown':
        books = Booklog.query.order_by(Booklog.page_count).all()
        books.reverse()
    elif sort == 'pubUp':
        books = Booklog.query.order_by(Booklog.pub_date).all()
    elif sort == 'pubDown':
        books = Booklog.query.order_by(Booklog.pub_date).all()
        books.reverse()
    elif sort == 'addedUp':
        books = Booklog.query.order_by(Booklog.date_started).all()
    elif sort == 'addedDown':
        books = Booklog.query.order_by(Booklog.date_started).all()
        books.reverse()
    else:
        sort = 'addedUp'
        books = Booklog.query.order_by(Booklog.date_started).all()
    
    # Sort the reading list
    if sortReadList == 'titleUp':
        readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
    elif sortReadList == 'titleDown':
        readingListBooks = ReadingList.query.order_by(ReadingList.title).all()
        readingListBooks.reverse()
    elif sortReadList == 'authorUp':
        readingListBooks = ReadingList.query.order_by(ReadingList.author).all()
    elif sortReadList == 'authorDown':
        readingListBooks = ReadingList.query.order_by(ReadingList.author).all()
        readingListBooks.reverse()
    elif sortReadList == 'pagesUp':
        readingListBooks = ReadingList.query.order_by(ReadingList.page_count).all()
    elif sortReadList == 'pagesDown':
        readingListBooks = ReadingList.query.order_by(ReadingList.page_count).all()
        readingListBooks.reverse()
    elif sortReadList == 'pubUp':
        readingListBooks = ReadingList.query.order_by(ReadingList.pub_date).all()
    elif sortReadList == 'pubDown':
        readingListBooks = ReadingList.query.order_by(ReadingList.pub_date).all()
        readingListBooks.reverse()
    else:
        sortReadList = 'addedUp'
        readingListBooks = ReadingList.query.order_by(ReadingList.title).all()

    sortAtoZ = 'True' if sortAtoZ else 'False'
    rdb.set('sort',sort)
    rdb.set('sortAtoZ',sortAtoZ)

    sortAtoZReading = 'True' if sortAtoZReading else 'False'
    rdb.set('sortReadList',sortReadList)
    rdb.set('sortAtoZReading',sortAtoZReading)
    return redirect('/')


@app.route('/query/', methods=['POST','GET'])
def search():
    # Searches the google books API with the given query
    if request.method == 'POST':
        searchTerm = request.form['query']
        searchTerm.replace(' ','+')
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + searchTerm + "&orderBy=relevance&maxResults=40")
        results = json.loads(response.text)
        if results["totalItems"] == 0:
            return render_template('error.html', msg='Search turned up empty, sorry.')
        else:
            img_url = []
            titles = []
            authors = []
            pages = []
            publishDates = []
            volumeIDs = []
            for book in results["items"]:
                info = book["volumeInfo"]
                try:
                    images = info["imageLinks"]
                    # print(images["thumbnail"], file=sys.stderr)
                    img_url.append(''.join(images["thumbnail"]))
                except:
                    img_url.append('')
                try:
                    titles.append(''.join(info["title"]))
                except:
                    titles.append('')
                try:
                    authors.append(''.join(info["authors"][0]))
                except:
                    authors.append('')
                try:
                    pages.append(info["pageCount"])
                except:
                    pages.append('')
                try:
                    publishDates.append(''.join(info["publishedDate"]))
                except:
                    publishDates.append('')
                try:
                    volumeIDs.append(''.join(book["id"]))
                except:
                    return redirect('/')
            return render_template('search.html', img_url=img_url, results=results, titles=titles, authors=authors, pages=pages, publishDates=publishDates, volumeIDs=volumeIDs)
    else:
        return render_template('error.html', msg='failed to render search results')

@app.route('/select_volume/',methods=['POST'])
def select_volume():
    if request.method == 'POST':
        data = request.get_json()
        volumeID = data['volumeID']
        author = data['author']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        # Get cover image
        try:
            img = book["imageLinks"]
        except:
            img = {'thumbnail':'https://images-na.ssl-images-amazon.com/images/I/618C21neZFL._SX331_BO1,204,203,200_.jpg'}
        # Parse genres
        genres = ''
        try:
            book_genres = [x.lower() for x in book["categories"]]
            for genre in book_genres:
                if 'philosophy' in genre and 'Philosophy' not in genres:
                    genres += 'Philosophy,'
                if 'fantasy' in genre and 'Fantasy' not in genres:
                    genres += 'Fantasy,'
                if 'science fiction' in genre and 'Sci-Fi' not in genres:
                    genres += 'Sci-Fi,'
                if 'life science' in genre and 'Biology' not in genres:
                    genres += 'Biology,'
                if 'astronomy' in genre and 'Astronomy' not in genres:
                    genres += 'Astronomy,'
                if 'biography' in genre and 'Biography' not in genres:
                    genres += 'Biography,'
                if 'business' in genre and 'Business' not in genres:
                    genres += 'Business,'
                if 'classic' in genre and 'Classic' not in genres:
                    genres += 'Classic,'
                if 'graphic novel' in genre and 'Graphic Novel' not in genres:
                    genres += 'Graphic Novel,'
                if 'computing' in genre and 'Computing' not in genres:
                    genres += 'Computing,'
                if 'engineering' in genre and 'Engineering' not in genres:
                    genres += 'Engineering,'
                if 'health' in genre and 'Health' not in genres:
                    genres += 'Health,'
                if 'history' in genre and 'History' not in genres:
                    genres += 'History,'
                if 'horror' in genre and 'Horror' not in genres:
                    genres += 'Horror,'
                if 'humor' in genre and 'Humor' not in genres:
                    genres += 'Humor,'
                if 'kids' in genre and 'Kids' not in genres:
                    genres += 'Kids,'
                if 'law' in genre and 'Law' not in genres:
                    genres += 'Law,'
                if 'math' in genre and 'Math' not in genres:
                    genres += 'Math,'
                if 'military' in genre and 'Military' not in genres:
                    genres += 'Military,'
                if 'music' in genre and 'Music' not in genres:
                    genres += 'Music,'
                if 'mystery' in genre and 'Mystery' not in genres:
                    genres += 'Mystery,'
                if 'nature' in genre and 'Nature' not in genres:
                    genres += 'Nature,'
                if 'poetry' in genre and 'Poetry' not in genres:
                    genres += 'Poetry,'
                if 'politics' in genre and 'Politics' not in genres:
                    genres += 'Politics,'
                if 'psychology' in genre and 'Psychology' not in genres:
                    genres += 'Psychology,'
                if 'religion' in genre and 'Religion' not in genres:
                    genres += 'Religion,'
                if 'romance' in genre and 'Romance' not in genres:
                    genres += 'Romance,'
                if 'science' in genre and 'Science' not in genres:
                    genres += 'Science,'
                if 'teen' in genre and 'Teen' not in genres:
                    genres += 'Teen,'
                if 'travel' in genre and 'Travel' not in genres:
                    genres += 'Travel,'
                
        except:
            print('no categories present :(')
        print(volumeID)
        db.session.add(Booklog(title=book["title"], author=author, page_count=book["pageCount"], pub_date=book["publishedDate"][0:4], img_url=img["thumbnail"], volume_id=volumeID, genres=genres))
        db.session.commit()
    return redirect('sort_log/')

@app.route('/set_genres/', methods=['POST'])
def set_genres():
    print('setting genres')
    genres_str = request.json['genres']
    print(genres_str)
    return redirect('/')

@app.route('/finish_book/', methods=['POST'])
def markFinished():
    if request.method == 'POST':
        bookID = request.form['finishedBook']
        finishDate = request.form['finishDate']
        try:
            formatted_date = parse(finishDate)
        except:
            formatted_date = date.today()
        
        book = Booklog.query.filter_by(id=bookID).first()
        book.date_finished = formatted_date
        db.session.commit()

    return redirect('sort_log/')


@app.route('/delete/<int:id>')
def delete(id):
    book_to_delete = Booklog.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('sort_log/')
    except:
        return render_template('error.html',msg='Error in delete() fn')


@app.route('/delete_reading_list/<int:id>', methods=['GET'])
def deleteReadingList(id):
    book_to_delete = ReadingList.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('/sort_reading_list/')
    except:
        return render_template('error.html',msg='Error in delete() fn')


@app.route('/edit_listing/', methods=['POST','GET'])
def edit_listing():
    if request.method == "POST":
        edits = request.get_json()
        old_book = Booklog.query.filter_by(id=edits['id']).first()
        
        try:
            edits['startDate'] = parse(edits['startDate'])
        except:
            edits['startDate'] = old_book.date_started
        
        try:
            edits['finishDate'] = parse(edits['finishDate'])
        except:
            edits['finishDate'] = old_book.date_finished

        db.session.add(Booklog(title=edits['title'], author=edits['author'], page_count=edits['pages'], pub_date=edits['published'][0:4], date_started=edits["startDate"], date_finished=edits["finishDate"], img_url=edits["thumbnail"], volume_id=edits['volumeID']))
        db.session.commit()

    return redirect('/')

@app.route('/add_reading_list/', methods=['POST','GET'])
def add_reading_list():
    if request.method == 'POST':
        data = request.get_json()
        volumeID = data['volumeID']
        author = data['author']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        try:
            img = book["imageLinks"]
        except:
            img = {'thumbnail':'https://images-na.ssl-images-amazon.com/images/I/618C21neZFL._SX331_BO1,204,203,200_.jpg'}
        db.session.add(ReadingList(title=book["title"], author=author, page_count=book["pageCount"], pub_date=book["publishedDate"][0:4], img_url=img["thumbnail"], volume_id=volumeID))
        db.session.commit()
    return redirect('sort_log/')


if __name__ == "__main__":
    app.run(debug=True)