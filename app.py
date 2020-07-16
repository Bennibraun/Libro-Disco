from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.db'
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    author = db.Column(db.String(200),nullable=True)
    page_count = db.Column(db.Integer,nullable=True)
    pub_date = db.Column(db.String(15),nullable=True)
    volume_id = db.Column(db.String(15),nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Called every time a new element is added to the db
    def __repr__(self):
        return '<book %r>' % self.id

@app.route('/', methods=['POST','GET'])
def index():
    # Method inserts the given book title into the db
    if request.method == 'POST':
        book_title = request.form['title']
        new_book = Book(title=book_title)
        try:
            db.session.add(new_book)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding the book.'
    books = Book.query.order_by(Book.date_added).all()
    return render_template('index.html', books=books )

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
            titles = []
            authors = []
            pages = []
            publishDates = []
            volumeIDs = []
            for book in results["items"]:
                info = book["volumeInfo"]
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
            return render_template('search.html', results=results, titles=titles, authors=authors, pages=pages, publishDates=publishDates, volumeIDs=volumeIDs)
    else:
        return render_template('error.html', msg='failed to render search results')

@app.route('/select_volume/',methods=['POST'])
def select_volume():
    if request.method == 'POST':
        volumeID = request.form['volumeID']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        db.session.add(Book(title=book["title"], author=book["authors"][0], page_count=book["pageCount"], pub_date=book["publishedDate"], volume_id=volumeID))
        db.session.commit()
    return 'hurray'

@app.route('/delete/<int:id>')
def delete(id):
    book_to_delete = Book.query.get_or_404(id)
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
        book_list = Book.query.all()
        for book in book_list:
            db.session.delete(book)
        db.session.commit()
        # return redirect('/')
        return render_template('error.html',msg='Error in clear() fn')
    except:
        return 'Clear failed'


if __name__ == "__main__":
    app.run(debug=True)