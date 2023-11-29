from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form
    distance = data.get('distance')
    location = data.get('location')
    genre = data.get('genre')
    intensity = data.get('intensity')

    # Here you would add the logic to generate the running route and playlist
    # For now, let's just return the received data
    return jsonify({
        'distance': distance,
        'location': location,
        'genre': genre,
        'intensity': intensity,
        'route': 'Route generation logic goes here',
        'playlist': 'Playlist generation logic goes here'
    })

if __name__ == '__main__':
    app.run(debug=True)
