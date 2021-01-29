from flask import Flask, render_template, url_for, request, redirect
from datetime import date
from dateutil.parser import parse
import requests
import json
import sys
import os
import redis
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter 
# import urllib.parse as urlparse

app = Flask(__name__)
app.config['DEBUG'] = False


# Connect to redis db for variable consistency
# rdb = ''
# try:
#     url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
#     rdb = redis.Redis(host=url.hostname, port=url.port, password=url.password)
# except:
rdb = redis.Redis(host='redis-18733.c15.us-east-1-4.ec2.cloud.redislabs.com', port=18733, password='ZGeq34DqphcnS0lkuBOLLKHPLlbEevEc')

# Set default vars
rdb.set('sort','date_finished')
rdb.set('sortReadList','title')
rdb.set('sortAtoZ', 'False')
rdb.set('sortAtoZReading','True')
rdb.set('showImages','False')
rdb.set('showImagesReadingList','False')
rdb.set('currentUser','')

# Connect to postgresql db
conn = ''
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    print('connected through heroku')
except:
    conn = psycopg2.connect(r'postgres://nicezipewxxlao:1472fb03b8bd3e997b12a13299286bc00fe0c274d11785feee18487757e48525@ec2-34-197-141-7.compute-1.amazonaws.com:5432/ddf9rpbt51qrpp')
    print('connected through url directly')

# Set cursor
cur = conn.cursor()

# Make default queries
books_def_query = 'SELECT * FROM books \nWHERE username=\''+rdb.get('currentUser').decode('utf-8')+'\'\nORDER BY date_started DESC;'

cur.execute(books_def_query)
books = cur.fetchall()

readinglist_def_query = 'SELECT * FROM reading_list\nWHERE username=\''+rdb.get('currentUser').decode('utf-8')+'\'\nORDER BY title ASC;'

cur.execute(readinglist_def_query)
readingListBooks = cur.fetchall()


# Classes to use to bridge the gap between sql query and jinja2-usable object
class logBook:
    def __init__(self,id,title,author,page_count,pub_date,volume_id,img_url,date_started,date_finished,genres,rating,review):
        self.id = id
        self.title = title
        self.author = author
        self.page_count = page_count
        self.pub_date = pub_date
        self.volume_id = volume_id
        self.img_url = img_url
        self.date_started = date_started
        self.date_finished = date_finished
        self.genres = genres
        self.rating = rating
        self.review = review

class readingListBook:
    def __init__(self,id,title,author,page_count,pub_date,volume_id):
        self.id = id
        self.title = title
        self.author = author
        self.page_count = page_count
        self.pub_date = pub_date
        self.volume_id = volume_id
        # self.img_url = img_url

# Begin app

@app.route('/')
def index():

    if rdb.get('currentUser').decode('utf-8') == '':
        print('no one is logged in yet.')
        return render_template('login.html')

    showImages = (rdb.get('showImages').decode('utf-8') == 'True')
    showImagesReadingList = (rdb.get('showImagesReadingList').decode('utf-8') == 'True')
    sort = rdb.get('sort').decode('utf-8')
    sortReadList = rdb.get('sortReadList').decode('utf-8')
    sortAtoZ = (rdb.get('sortAtoZ').decode('utf-8') == 'True')
    sortAtoZReading = (rdb.get('sortAtoZReading').decode('utf-8') == 'True')
    
    # Get books from db
    book_query = 'SELECT * FROM books \nWHERE username=\''+rdb.get('currentUser').decode('utf-8')+'\'\nORDER BY ' + sort + ' '
    if sortAtoZ:
        if sort == 'pub_date':
            book_query += 'DESC;'
        else:
            book_query += 'ASC;'
    else:
        if sort == 'pub_date':
            book_query += 'ASC;'
        else:
            book_query += 'DESC'
    cur.execute(book_query)
    books_result = cur.fetchall()

    # Get reading list from db
    reading_query = 'SELECT * FROM reading_list\nWHERE username=\''+rdb.get('currentUser').decode('utf-8')+'\'\n ORDER BY ' + sortReadList + ' '
    if sortAtoZReading:
        if sortReadList == 'pub_date':
            reading_query += 'DESC;'
        else:
            reading_query += 'ASC;'
    else:
        if sortReadList == 'pub_date':
            reading_query += 'ASC;'
        else:
            reading_query += 'DESC'
    cur.execute(reading_query)
    readingListBooks_result = cur.fetchall()

    books = []
    for result in books_result:
        book = logBook(result[0],result[1],result[2],result[3],result[4],result[5],result[6],result[7],result[8],result[9],result[10],result[11])
        book.pub_date = str(book.pub_date)[:4]
        if not book.genres:
            book.genres = []
        else:
            book.genres = book.genres.split(',')
        books.append(book)
        # print(book.genres)
    
    booksToRead = []
    for result in readingListBooks_result:
        book = readingListBook(result[0],result[1],result[2],result[3],result[4],result[5])
        book.pub_date = str(book.pub_date)[:4]
        booksToRead.append(book)
    
    stats = fetch_stats()

    print('rendering index.html')

    return render_template('index.html', books=books, booksToRead=booksToRead, showImages=showImages, showImagesReadingList=showImagesReadingList, sort=sort, sortAtoZ=sortAtoZ, sortReadList=sortReadList, sortAtoZReading=sortAtoZReading, stats=stats)


# @app.route('/displayMode/', methods=['POST'])
# def switchDisplayMode():
#     showImages = (rdb.get('showImages').decode('utf-8') == 'True')

#     showImages = not showImages

#     img_str = 'True' if showImages else 'False'
#     rdb.set('showImages',img_str)

#     return redirect('/')


# @app.route('/displayModeReadingList/', methods=['POST'])
# # def switchReadingDisplay():
#     showImagesReadingList = (rdb.get('showImagesReadingList').decode('utf-8') == 'True')

#     showImagesReadingList = not showImagesReadingList

#     img_str = 'True' if showImagesReadingList else 'False'
#     rdb.set('showImagesReadingList',img_str)

#     return redirect('/')


@app.route('/sort_log/', methods=['POST','GET'])
def sortLog():
    sort = rdb.get('sort').decode('utf-8')
    sortAtoZ = (rdb.get('sortAtoZ').decode('utf-8') == 'True')

    if request.method == 'POST':
        try:
            request.form['sortTitle']
            print('sorting by title')
            sort = 'title'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortAuthor']
            print('sorting by author')
            sort = 'author'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortPageCount']
            print('sorting by page count')
            sort = 'page_count'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortPubDate']
            print('sorting by publication date')
            sort = 'pub_date'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortDateAdded']
            print('sorting by date added')
            sort = 'date_started'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortDateFinished']
            print('sorting by date finished')
            sort = 'date_finished'
            sortAtoZ = not sortAtoZ
        except:
            pass
        try:
            request.form['sortRating']
            print('sorting by rating')
            sort = 'rating'
            sortAtoZ = not sortAtoZ
        except:
            pass

    sortAtoZ = 'True' if sortAtoZ else 'False'
    rdb.set('sort',sort)
    rdb.set('sortAtoZ',sortAtoZ)
    return redirect('/')


@app.route('/sort_reading_list/', methods=['POST','GET'])
def sortReadingList():
    print('sorting reading list')
    sortReadList = rdb.get('sortReadList').decode('utf-8')
    sortAtoZReading = (rdb.get('sortAtoZReading').decode('utf-8') == 'True')

    if request.method == 'POST':
        try:
            request.form['sortTitleRL']
            print('sorting by title')
            sortReadList = 'title'
            sortAtoZReading = not sortAtoZReading
        except:
            pass
        try:
            request.form['sortAuthorRL']
            print('sorting by author')
            sortReadList = 'author'
            sortAtoZReading = not sortAtoZReading
        except:
            pass
        try:
            request.form['sortPageCountRL']
            print('sorting by page count')
            sortReadList = 'page_count'
            sortAtoZReading = not sortAtoZReading
        except:
            pass
        try:
            request.form['sortPubDateRL']
            print('sorting by publication date')
            sortReadList = 'pub_date'
            sortAtoZReading = not sortAtoZReading
        except:
            pass
    
    sortAtoZReading = 'True' if sortAtoZReading else 'False'
    rdb.set('sortReadList',sortReadList)
    rdb.set('sortAtoZReading',sortAtoZReading)
    return redirect('/')


@app.route('/query/', methods=['POST','GET'])
def search():
    # Searches the google books API with the given query
    if request.method == 'POST':
        searchTerm = request.form['query']
        searchTerm = searchTerm.replace(' ','+')
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + searchTerm + "&orderBy=relevance&maxResults=40")
        results = json.loads(response.text)
        if results["totalItems"] == 0:
            return render_template('error.html', msg='Search turned up empty (evidently you suck at googling).')
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
            return render_template('search.html', searchTerm=searchTerm, img_url=img_url, results=results, titles=titles, authors=authors, pages=pages, publishDates=publishDates, volumeIDs=volumeIDs)
    else:
        return render_template('error.html', msg='failed to render search results')

@app.route('/select_volume/',methods=['POST'])
def select_volume():
    if request.method == 'POST':
        try:
            data = request.get_json()
            volumeID = data['volumeID']
            author = data['author']
            bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
            book = json.loads(bookResponse.text)["volumeInfo"]
            startDate = str(date.today())
        except:
            print('failed to retrieve book info')
            return
        # Get cover image
        try:
            img = book["imageLinks"]
        except:
            img = {'thumbnail':'https://images-na.ssl-images-amazon.com/images/I/618C21neZFL._SX331_BO1,204,203,200_.jpg'}
        # Parse genres
        genres = []
        try:
            book_genres = [x.lower() for x in book["categories"]]
            print(book_genres)
            for genre in book_genres:
                if 'fiction' in genre and 'Fiction' not in genres:
                    genres.append('Fiction')
                if 'nonfiction' in genre and 'Non-Fiction' not in genres:
                    genres.append('Non-Fiction')
                if 'philosophy' in genre and 'Philosophy' not in genres:
                    genres.append('Philosophy')
                if 'fantasy' in genre and 'Fantasy' not in genres:
                    genres.append('Fantasy')
                if 'science fiction' in genre and 'Sci-Fi' not in genres:
                    genres.append('Sci-Fi')
                if 'life science' in genre and 'Biology' not in genres:
                    genres.append('Biology')
                if 'astronomy' in genre and 'Astronomy' not in genres:
                    genres.append('Astronomy')
                if 'biography' in genre and 'Biography' not in genres:
                    genres.append('Biography')
                if 'business' in genre and 'Business' not in genres:
                    genres.append('Business')
                if 'classic' in genre and 'Classic' not in genres:
                    genres.append('Classic')
                if 'graphic novel' in genre and 'Graphic Novel' not in genres:
                    genres.append('Graphic Novel')
                if 'computing' in genre and 'Computing' not in genres:
                    genres.append('Computing')
                if 'engineering' in genre and 'Engineering' not in genres:
                    genres.append('Engineering')
                if 'health' in genre and 'Health' not in genres:
                    genres.append('Health')
                if 'history' in genre and 'History' not in genres:
                    genres.append('History')
                if 'horror' in genre and 'Horror' not in genres:
                    genres.append('Horror')
                if 'humor' in genre and 'Humor' not in genres:
                    genres.append('Humor')
                if 'kids' in genre and 'Kids' not in genres:
                    genres.append('Kids')
                if 'law' in genre and 'Law' not in genres:
                    genres.append('Law')
                if 'math' in genre and 'Math' not in genres:
                    genres.append('Math')
                if 'military' in genre and 'Military' not in genres:
                    genres.append('Military')
                if 'music' in genre and 'Music' not in genres:
                    genres.append('Music')
                if 'mystery' in genre and 'Mystery' not in genres:
                    genres.append('Mystery')
                if 'nature' in genre and 'Nature' not in genres:
                    genres.append('Nature')
                if 'poetry' in genre and 'Poetry' not in genres:
                    genres.append('Poetry')
                if 'politics' in genre and 'Politics' not in genres:
                    genres.append('Politics')
                if 'psychology' in genre and 'Psychology' not in genres:
                    genres.append('Psychology')
                if 'religion' in genre and 'Religion' not in genres:
                    genres.append('Religion')
                if 'romance' in genre and 'Romance' not in genres:
                    genres.append('Romance')
                if 'science' in genre and 'Science' not in genres:
                    genres.append('Science')
                if 'teen' in genre and 'Teen' not in genres:
                    genres.append('Teen')
                if 'travel' in genre and 'Travel' not in genres:
                    genres.append('Travel')
        except:
            genres = []
            print('no categories present :(')
        
        genres = ','.join(genres)

        print(volumeID)

        book['title'] = book['title'].replace('\'','\'\'')
        author = author.replace('\'', '\'\'')
        pageCount = None
        try:
            pageCount = str(book["pageCount"])
        except:
            pageCount = '0'


        cur.execute('INSERT INTO books (title,author,page_count,pub_date,date_started,img_url,volume_id,genres,rating,review,username) VALUES (\''+book["title"]+'\',\''+author+'\','+pageCount+',\''+str(book["publishedDate"][0:4])+'-01-01\',\''+str(startDate)+'\',\''+img["thumbnail"]+'\',\''+str(volumeID)+'\',\''+genres+'\',0,\'Not yet reviewed\',\''+rdb.get('currentUser').decode('utf-8')+'\');')
        conn.commit()
    
    return redirect(url_for('sortLog'))

# @app.route('/set_genres/', methods=['POST'])
# def set_genres():
#     print('setting genres')
#     genres_str = request.json['genres']
#     print(genres_str)
#     return redirect('/')

@app.route('/finish_book/', methods=['POST'])
def markFinished():
    if request.method == 'POST':
        bookID = request.form['finishedBook']
        formatted_date = "'"+str(date.today())+"'"
        
        cur.execute('UPDATE books SET date_finished = '+str(formatted_date)+' WHERE id='+bookID)
        conn.commit()

    return redirect('/sort_log/')


@app.route('/delete/<int:id>')
def delete(id):
    try:
        cur.execute('DELETE FROM books WHERE id='+str(id)+';')
        conn.commit()
        return redirect('/sort_log/')
    except:
        print('delete failed')
        return render_template('error.html',msg='Error in delete() fn')


@app.route('/delete_reading_list/<int:id>')
def deleteReadingList(id):
    try:
        cur.execute('DELETE FROM reading_list WHERE id='+str(id)+';')
        conn.commit()
        return redirect('/sort_reading_list/')
    except:
        return render_template('error.html',msg='Error in delete() fn')


@app.route('/edit_listing/', methods=['POST','GET'])
def edit_listing():
    if request.method == "POST":
        edits = request.get_json()
        cur.execute("SELECT * FROM books WHERE id="+edits['id']+" LIMIT 1;")
        old_book = cur.fetchone()

        edits['title'] = edits['title'].replace('\'','\'\'')
        edits['author'] = edits['author'].replace('\'', '\'\'')
        
        try:
            edits['startDate'] = parse(edits['startDate'])
        except:
            edits['startDate'] = old_book[7]
        
        try:
            edits['finishDate'] = "'"+str(parse(edits['finishDate']))+"'"
        except:
            try:
                edits['finishDate'] = "'"+str(parse(old_book[8]))+"'"
            except:
                edits['finishDate'] = 'Null'
        
        genresStr = ','.join(edits['genres'])


        review = str(old_book[11]).replace('\'', '\'\'')
        
        if not edits['rating']:
            edits['rating'] = '0'

        cur.execute('INSERT INTO books (title,author,page_count,pub_date,date_started,date_finished,img_url,volume_id,genres,rating,review,username) VALUES (\''+edits['title']+'\',\''+edits['author']+'\','+edits['pages']+',\''+str(edits['published'])[0:4]+'-01-01\',\''+str(edits["startDate"])+'\','+str(edits["finishDate"])+',\''+edits["thumbnail"]+'\',\''+edits['volumeID']+'\',\''+genresStr+'\','+str(edits['rating'])+',\''+review+'\',\''+rdb.get('currentUser').decode('utf-8')+'\');')
        conn.commit()


    return redirect('/')

@app.route('/edit_review/', methods=['POST'])
def edit_review():
    if request.method == 'POST':
        data = request.get_json()
        review = data['review'].replace('\'','\'\'')
        cur.execute('UPDATE books SET review = \'' + review + '\' WHERE id=' + str(data['id']) + ';')
        conn.commit()
    
    return redirect('/')

@app.route('/add_reading_list/', methods=['POST','GET'])
def add_reading_list():
    if request.method == 'POST':
        data = request.get_json()
        volumeID = data['volumeID']
        author = data['author']
        bookResponse = requests.get("https://www.googleapis.com/books/v1/volumes/"+volumeID)
        book = json.loads(bookResponse.text)["volumeInfo"]
        book['title'] = book['title'].replace('\'','\'\'')
        author = author.replace('\'','\'\'')
        
        # print('attempting to add book to reading list, likely to fail')
        cur.execute('INSERT INTO reading_list (title,author,page_count,pub_date,volume_id,username) VALUES (\''+book["title"]+'\',\''+author+'\','+str(book["pageCount"])+',\''+str(book["publishedDate"][0:4])+'-01-01\',\''+str(volumeID)+'\',\''+rdb.get('currentUser').decode('utf-8')+'\');')
        conn.commit()

    return redirect('/sort_reading_list/')


@app.route('/register/', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    
    try:
        # User(username, generate_password_hash(password)).save_to_db()
        password = generate_password_hash(password)
        cur.execute('INSERT INTO users (username, password) VALUES (\''+username+'\',\''+password+'\');')
        conn.commit()
    except:
        return render_template('error.html',msg='failed to register user')
    
    return redirect('/')

@app.route('/login/', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cur.execute("""
    SELECT * FROM users;
    """)
    users = cur.fetchall()

    for user in users:
        if user[1] == username:
            # Check password
            if check_password_hash(user[2],password):
                # Successful login
                rdb.set('currentUser',username)
                return redirect('/')

    print('login failed')
    return redirect('/')

@app.route('/logout/', methods=['POST'])
def logout():
    rdb.set('currentUser','')
    return redirect('/')

def fetch_stats():
    stats = []

    # Frequency of Genres
    cur.execute("""
    SELECT genres FROM books;
    """ )
    genres = cur.fetchall()
    genre_instances = []
    for g in genres:
        genre_instances.extend(g[0].split(','))
    genre_counts = Counter(genre_instances)
    # print(genre_counts)
    stats.append({'genre_freq_labels': genre_counts.keys()})
    stats.append({'genre_freq_values': genre_counts.values()})

    # Timeline


    return []


if __name__ == "__main__":
    app.run(debug=False,threaded=True)