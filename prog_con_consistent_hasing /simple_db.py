from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
cache = {}
MAX_CACHE_SIZE = 10



def get_db_connection():
    conn = sqlite3.connect('db_one.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS db_one (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL  
        )
    ''')
    conn.commit()
    conn.close()

def add_to_cache(key, value):
    global cache
    if len(cache) >= MAX_CACHE_SIZE:
        # Evict the oldest item (FIFO for simplicity)
        cache.pop(next(iter(cache)))
    cache[key] = value

@app.route('/put', methods=['PUT'])
def update():
    data = request.json
    key= data.get('key')
    value = data.get('value')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the URL already exists in the database
    result = cursor.execute('SELECT value FROM db_one WHERE key = ?', (key,)).fetchone()
    if result:
        conn.close()
        content = jsonify({"key": key, "value": value}), 200

    # If not, insert new URL into the database
    try:
        cursor.execute('INSERT INTO db_one (original_url) VALUES (?)', (original_url,))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        add_to_cache(new_id, original_url)  # Add new URL to cache
        return jsonify({"success": True, "id": new_id}), 201
    except sqlite3.IntegrityError:  # Catch uniqueness constraint violation
        conn.close()
        return jsonify({"error": "URL already exists"}), 409

@app.route('/getById/<int:key>', methods=['GET'])
def getById(key):
    # # Check cache first
    # if id in cache:
    #     return jsonify({"id": id, "original_url": cache[id]})

    # If not in cache, query the database
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM urls WHERE id = ?', (key,)).fetchone()
    conn.close()
    if data is None:
        return jsonify({"error": "Not found"}), 404
    
    # Add to cache before returning
    # add_to_cache(url['id'], url['original_url'])
    return jsonify({"id": data['id'], "key": data['key'], 'value': data['value']})

init_db()  # Ensure the database is initialized before starting the app
app.run()

