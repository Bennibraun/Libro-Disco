from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from dateutil.parser import parse
import requests
import json
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booklog.db'
db = SQLAlchemy(app)

class Booklog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    author = db.Column(db.String(200),nullable=True)
    page_count = db.Column(db.Integer,nullable=True)
    pub_date = db.Column(db.String(4),nullable=True)
    volume_id = db.Column(db.String(15),nullable=True)
    img_url = db.Column(db.String(100),nullable=True)
    date_started = db.Column(db.Date, default=date.today)
    date_finished = db.Column(db.Date, default=None, nullable=True)

    # Called every time a new element is added to the db
    def __repr__(self):
        return '<book %r>' % self.id

books = Booklog.query.order_by(Booklog.date_started).all()
sort = ''
sortAtoZ = True
showImages = False

@app.route('/')
def index():
    global books
    global showImages
    global sort
    return render_template('index.html', books=books, showImages=showImages, sort=sort)

@app.route('/displayMode', methods=['POST'])
def switchDisplayMode():
    global showImages
    global books
    showImages = not showImages
    return redirect('/')

@app.route('/sort', methods=['POST'])
def sort():
    global books
    global sort
    global sortAtoZ
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
            return redirect('/')
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
            return redirect('/')
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
            return redirect('/')
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
            return redirect('/')
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
            return redirect('/')
        except:
            pass
    
    print('sorting by date added by default')
    books = Booklog.query.order_by(Booklog.date_started).all()
    return redirect('/')

@app.route('/query/', methods=['POST','GET'])
def search():
    # Searches the google books API with the given query
    if request.method == 'POST':
        searchTerm = request.form['query']
        searchTerm.replace(' ','+')
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + searchTerm + "&orderBy=relevance&maxResults=40")
        results = json.loads(response.text)
        print(results["totalItems"])
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
        volumeID = request.form['volumeID']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        try:
            img = book["imageLinks"]
        except:
            img = {'thumbnail':'https://images-na.ssl-images-amazon.com/images/I/618C21neZFL._SX331_BO1,204,203,200_.jpg'}
        db.session.add(Booklog(title=book["title"], author=book["authors"][0], page_count=book["pageCount"], pub_date=book["publishedDate"][0:4], img_url=img["thumbnail"], volume_id=volumeID))
        db.session.commit()
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

    return redirect('/refresh/')


@app.route('/delete/<int:id>')
def delete(id):
    print(id)
    book_to_delete = Booklog.query.get_or_404(id)
    print('deleting ' + book_to_delete.title)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('/refresh/')
    except:
        return render_template('error.html',msg='Error in delete() fn')

@app.route('/edit_listing/', methods=['POST','GET'])
def edit_listing():
    if request.method == "POST":
        edits = request.get_json()
        print(edits['id'])
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


@app.route('/refresh/')
def refresh():
    # Sort as it should be, by default
    global sort
    global books
    global showImages
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

    print('refreshing')
    return render_template('index.html', books=books, showImages=showImages, sort=sort)


if __name__ == "__main__":
    app.run(debug=True)