# migliorare la logica del virtual server 
# la duplicazione (vuol dire che quando vado a fare il POST questo si trova in due DB)

from flask import Flask, request, jsonify
import requests
import hashlib

app = Flask(__name__)

# List of backend servers
servers = [
    "http://localhost:6000",
    "http://localhost:6001",
    "http://localhost:6002"
]

current_server = 0


def hash_function(key):
    return int(hashlib.md5(key.encode()).hexdigest(), 16) # base 16 (esadecimale)

# Sceglie casualmente un server (db) su cui scrivere
# Devo distribuire la coppia key-value in modo uniforme tra i server,
# avrò un hash per ogni db e avrò un hash per ogni key
def get_server(key):
    # global current_server
    # server = servers[current_server]
    # current_server = (current_server + 1) % len(servers)
    # return server

    server_hashes1 = {hash_function(server+'1'): server for server in servers}
    server_hashes2 = {hash_function(server+'2'): server for server in servers}
    server_hashes = {}

    for key_, server in server_hashes1.items():
        server_hashes[key_] = server
    
    for key_, server in server_hashes2.items():
        server_hashes[key_] = server
    
    print(server_hashes)

    sorted_hashes = sorted(server_hashes.keys())
    key_hash = hash_function(key)

    # prendi il server se la chiave hashata è piu piccola del nome del server hashato (logica gioco)
    for server_hash in sorted_hashes:
        if key_hash < server_hash:
            return server_hashes[server_hash]
        
    return server_hashes[sorted_hashes[0]] # se la chiave hashata è piu grande di tutti i nomi dei server allora, chiudi l'anello e assegna al primo

@app.route('/get/<int:key>', methods=['GET'])
def get(key):
    server_url = get_server(str(key)) + '/get/' + str(key)
    try:
        response = requests.get(server_url)
        if response.status_code == 200: # status_code 200 -> ok
            result = response.json()
            result['server'] = server_url
            # result['key'] = hashlib.sha256(str(key).encode()).hexdigest()
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to get the (key, value) element', 'server': server_url}), 500
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Backend server error', 'server': server_url}), 500


@app.route('/add', methods=['POST'])
def add():
    data = request.json
    server_url = get_server(str(data['key'])) + '/add'
    header = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(server_url, json = data, headers = header)
        print(response.status_code)
        if response.status_code == 201: # status_code 201 -> created
            result = response.json()
            result['server'] = server_url 
            return jsonify(result), 201
        elif response.status_code == 200: # magari è gia stato creato
            result = response.json()
            result['server'] = server_url
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Failed to add a new element', 'server': server_url}), 500
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Backend server error', 'server': server_url}), 500


if __name__ == '__main__':
    app.run(debug=True)

