from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2

app = Flask(__name__, template_folder='.')
CORS(app)

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='labdb',
        user='postgres',
        password='password123',
        port='5432'
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/all_stats')
def get_all_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    res = {}
    try:
        # 1. สัดส่วน Movies vs TV Shows
        cur.execute("SELECT type, COUNT(*), ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) FROM netflix_titles GROUP BY type;")
        res['type_ratio'] = [{"label": i[0], "value": i[1], "pct": float(i[2])} for i in cur.fetchall()]

        # 2. แนวโน้มการเติบโตย้อนหลัง (2010 เป็นต้นไป)
        cur.execute("""
            SELECT release_year, COUNT(*) AS total, 
                   COUNT(CASE WHEN type = 'Movie' THEN 1 END) AS movies,
                   COUNT(CASE WHEN type = 'TV Show' THEN 1 END) AS tv_shows
            FROM netflix_titles WHERE release_year >= 2010 GROUP BY release_year ORDER BY release_year ASC;
        """)
        res['growth_trend'] = [{"year": i[0], "total": i[1], "movies": i[2], "tv_shows": i[3]} for i in cur.fetchall()]

        # 3. Top 10 ประเทศยุทธศาสตร์
        cur.execute("""
            SELECT TRIM(c) AS country_name, COUNT(*) AS total_titles
            FROM netflix_titles, UNNEST(STRING_TO_ARRAY(country, ',')) AS c
            WHERE country IS NOT NULL AND TRIM(c) != ''
            GROUP BY TRIM(c) ORDER BY total_titles DESC LIMIT 10;
        """)
        res['top_countries'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        # 4. กลุ่มเป้าหมายผู้ชม (Audience Demographics)
        cur.execute("""
            SELECT CASE 
                WHEN rating IN ('TV-MA', 'R', 'NC-17') THEN 'Mature (18+)'
                WHEN rating IN ('PG-13', 'TV-14') THEN 'Teens / Young Adults'
                WHEN rating IN ('PG', 'TV-PG', 'G', 'TV-G', 'TV-Y', 'TV-Y7') THEN 'Kids & Family'
                ELSE 'Other / Unrated' END AS target_segment, COUNT(*) AS total_count
            FROM netflix_titles GROUP BY target_segment ORDER BY total_count DESC;
        """)
        res['audience_ratings'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        # 5. Top 10 หมวดหมู่คอนเทนต์ (Genres)
        cur.execute("""
            SELECT TRIM(g) AS genre_name, COUNT(*) AS total_titles
            FROM netflix_titles, UNNEST(STRING_TO_ARRAY(listed_in, ',')) AS g
            WHERE listed_in IS NOT NULL AND TRIM(g) != ''
            GROUP BY TRIM(g) ORDER BY total_titles DESC LIMIT 10;
        """)
        res['top_genres'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        # 6. โครงสร้างความยาวหนัง (Movie Duration)
        cur.execute("""
            SELECT CASE 
                WHEN CAST(SPLIT_PART(duration, ' ', 1) AS INTEGER) < 90 THEN 'Under 90 Mins'
                WHEN CAST(SPLIT_PART(duration, ' ', 1) AS INTEGER) BETWEEN 90 AND 120 THEN '90-120 Mins'
                ELSE 'Over 120 Mins' END AS duration_range, COUNT(*) AS total_movies
            FROM netflix_titles WHERE type = 'Movie' AND duration LIKE '%min'
            GROUP BY duration_range ORDER BY total_movies DESC;
        """)
        res['movie_durations'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        # 7. จำนวนซีซันของซีรีส์ (TV Show Longevity)
        cur.execute("""
            SELECT CASE 
                WHEN duration = '1 Season' THEN '1 Season Only'
                WHEN duration IN ('2 Seasons', '3 Seasons') THEN '2-3 Seasons'
                ELSE '4+ Seasons' END AS season_depth, COUNT(*) AS total_shows
            FROM netflix_titles WHERE type = 'TV Show'
            GROUP BY season_depth ORDER BY total_shows DESC;
        """)
        res['tv_seasons'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

        # 8. Top 10 ผู้กำกับสร้างผลงานสูงสุด
        cur.execute("""
            SELECT TRIM(d) AS director_name, COUNT(*) AS total_works
            FROM netflix_titles, UNNEST(STRING_TO_ARRAY(director, ',')) AS d
            WHERE director IS NOT NULL AND TRIM(d) != ''
            GROUP BY TRIM(d) ORDER BY total_works DESC LIMIT 10;
        """)
        res['top_directors'] = [{"label": i[0], "value": i[1]} for i in cur.fetchall()]

    finally:
        cur.close()
        conn.close()
        
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=5000)