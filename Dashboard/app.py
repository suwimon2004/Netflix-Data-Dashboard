from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='labdb',
        user='postgres',
        password='password123',
        port='5432'
    )

@app.route('/api/all_stats')
def get_all_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    res = {}
    try:
        cur.execute("SELECT type, count(*) FROM netflix_titles GROUP BY type;")
        res['types'] = {item[0]: item[1] for item in cur.fetchall()}

        cur.execute("SELECT country, count(*) as c FROM netflix_titles WHERE country IS NOT NULL GROUP BY country ORDER BY c DESC LIMIT 10;")
        res['countries'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT CAST(release_year AS TEXT), count(*) as c FROM netflix_titles GROUP BY release_year ORDER BY c DESC LIMIT 10;")
        res['years'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT rating, count(*) as c FROM netflix_titles WHERE rating IS NOT NULL GROUP BY rating ORDER BY c DESC LIMIT 7;")
        res['ratings'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT director, count(*) as c FROM netflix_titles WHERE director IS NOT NULL GROUP BY director ORDER BY c DESC LIMIT 10;")
        res['directors'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT listed_in, count(*) as c FROM netflix_titles GROUP BY listed_in ORDER BY c DESC LIMIT 10;")
        res['genres'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT TRIM(SPLIT_PART(date_added, ' ', 1)) as m, count(*) as c FROM netflix_titles WHERE date_added IS NOT NULL GROUP BY m ORDER BY c DESC;")
        res['months'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT title, date_added FROM netflix_titles WHERE date_added IS NOT NULL ORDER BY date_added DESC LIMIT 5;")
        res['recent'] = [{"title": i[0], "date": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT title, CAST(SPLIT_PART(duration, ' ', 1) AS INTEGER) as s FROM netflix_titles WHERE type = 'TV Show' ORDER BY s DESC LIMIT 5;")
        res['seasons'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        cur.execute("SELECT title, CAST(SPLIT_PART(duration, ' ', 1) AS INTEGER) as m FROM netflix_titles WHERE type = 'Movie' AND duration LIKE '%min' ORDER BY m DESC LIMIT 5;")
        res['duration'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
    return jsonify(res)

@app.route('/api/search')
def search():
    query_param = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor()
    # ค้นหาข้อมูลครบถ้วน: นักแสดง, ผู้กำกับ, ระยะเวลา, เรตติ้ง, ปี
    cur.execute("""
        SELECT title, cast_members, duration, director, rating, release_year, description, type
        FROM netflix_titles 
        WHERE title ILIKE %s LIMIT 1;
    """, (f'%{query_param}%',))
    item = cur.fetchone()
    cur.close()
    conn.close()
    
    if item:
        return jsonify({
            "found": True, "title": item[0], "cast": item[1], "duration": item[2],
            "director": item[3], "rating": item[4], "year": item[5], "desc": item[6], "type": item[7]
        })
    return jsonify({"found": False})

if __name__ == '__main__':
    app.run(debug=True, port=5000)