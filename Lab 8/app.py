from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/joke')
def joke():
    url = "https://official-joke-api.appspot.com/random_joke"
    response = requests.get(url)
    data = response.json()

    return jsonify({
        "setup": data["setup"],
        "punchline": data["punchline"]
    })

if __name__ == '__main__':
    app.run(debug=True)