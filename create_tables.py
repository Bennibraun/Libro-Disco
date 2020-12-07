import psycopg2
import os


conn = ''
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
except:
    conn = psycopg2.connect(r'postgres://nicezipewxxlao:1472fb03b8bd3e997b12a13299286bc00fe0c274d11785feee18487757e48525@ec2-34-197-141-7.compute-1.amazonaws.com:5432/ddf9rpbt51qrpp')

cur = conn.cursor()
def create_tables():
    commands = (
        """
        CREATE TABLE books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(50),
            page_count INTEGER,
            pub_date DATE,
            volume_id VARCHAR(30),
            img_url VARCHAR(300),
            date_started DATE,
            date_finished DATE,
            genres VARCHAR(100),
            rating FLOAT,
            review VARCHAR(3000)
        )
        """,
        """
        CREATE TABLE reading_list (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(50),
            page_count INTEGER,
            pub_date DATE,
            volume_id VARCHAR(30)
        )
        """
    )


    # for command in commands:
    #     cur.execute(command)
    #     conn.commit()
    cur.execute("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """)
    conn.commit()
    print('table created')

def clear_tables():
    command = 'DELETE FROM books;'

    cur.execute(command)

    conn.commit()

# clear_tables()

# create_tables()

command = """
DELETE FROM users WHERE username='john';
"""

cur.execute(command)
conn.commit()