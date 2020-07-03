from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.db'
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200),nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Called every time a new element is added to the db
    def __repr__(self):
        return '<book %r>' % self.id

@app.route('/', methods=['POST','GET'])
def index():
    if request.method == 'POST':
        book_title = request.form['title']
        new_book = Book(title=book_title)
        try:
            db.session.add(new_book)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding the book.'
    else:
        books = Book.query.order_by(Book.date_added).all()
        return render_template('index.html', books=books)

@app.route('/delete/<int:id>')
def delete(id):
    book_to_delete = Book.query.get_or_404(id)
    try:
        db.session.delete(book_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem with the deletion'


if __name__ == "__main__":
    app.run(debug=True)