from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date
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
    pub_date = db.Column(db.String(15),nullable=True)
    volume_id = db.Column(db.String(15),nullable=True)
    img_url = db.Column(db.String(100),nullable=True)
    date_added = db.Column(db.Date, default=date.today)

    # Called every time a new element is added to the db
    def __repr__(self):
        return '<book %r>' % self.id

books = Booklog.query.order_by(Booklog.date_added).all()
sortAtoZ = True
showImages = False

@app.route('/')
def index():
    return render_template('index.html', books=books, showImages=showImages)

@app.route('/displayMode', methods=['POST'])
def switchDisplayMode():
    global showImages
    global books
    showImages = not showImages
    return redirect('/')

@app.route('/sort', methods=['POST'])
def sort():
    global books
    global sortAtoZ
    try:
        request.form['sortAuthor']
        print('sorting by author')
        books = Booklog.query.order_by(Booklog.author).all()
        if not sortAtoZ:
            books.reverse()
            sortAtoZ = True
        else:
            sortAtoZ = False
        return redirect('/')
    except:
        pass
    try:
        request.form['sortTitle']
        print('sorting by title')
        books = Booklog.query.order_by(Booklog.title).all()
        if not sortAtoZ:
            books.reverse()
            sortAtoZ = True
        else:
            sortAtoZ = False
        return redirect('/')
    except:
        pass
    try:
        request.form['sortPageCount']
        print('sorting by page count')
        books = Booklog.query.order_by(Booklog.page_count).all()
        if not sortAtoZ:
            books.reverse()
            sortAtoZ = True
        else:
            sortAtoZ = False
        return redirect('/')
    except:
        pass
    try:
        request.form['sortPubDate']
        print('sorting by publication date')
        books = Booklog.query.order_by(Booklog.pub_date).all()
        if not sortAtoZ:
            books.reverse()
            sortAtoZ = True
        else:
            sortAtoZ = False
        return redirect('/')
    except:
        pass
    try:
        request.form['sortDateAdded']
        print('sorting by date added')
        books = Booklog.query.order_by(Booklog.date_added).all()
        if not sortAtoZ:
            books.reverse()
            sortAtoZ = True
        else:
            sortAtoZ = False
        return redirect('/')
    except:
        pass
    
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
                    return render_template('index.html')
            return render_template('search.html', img_url=img_url, results=results, titles=titles, authors=authors, pages=pages, publishDates=publishDates, volumeIDs=volumeIDs)
    else:
        return render_template('error.html', msg='failed to render search results')

@app.route('/select_volume/',methods=['POST'])
def select_volume():
    if request.method == 'POST':
        volumeID = request.form['volumeID']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        img = book["imageLinks"]
        db.session.add(Booklog(title=book["title"], author=book["authors"][0], page_count=book["pageCount"], pub_date=book["publishedDate"], img_url=img["thumbnail"], volume_id=volumeID))
        db.session.commit()
    return 'hurray'

@app.route('/delete/<int:id>')
def delete(id):
    book_to_delete = Booklog.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        # return redirect('/')
        return render_template('error.html',msg='Error in delete() fn')
    except:
        return 'There was a problem with the deletion'

@app.route('/clear/')
def clear():
    try:
        book_list = Booklog.query.all()
        for book in book_list:
            db.session.delete(book)
        db.session.commit()
        # return redirect('/')
        return render_template('error.html',msg='Error in clear() fn')
    except:
        return 'Clear failed'


if __name__ == "__main__":
    app.run(debug=True)