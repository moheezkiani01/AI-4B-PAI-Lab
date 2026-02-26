from flask import Flask, render_template
import requests
app = Flask(__name__)

@app.route('/')
def home():
    # Fetch joke
    url = "https://official-joke-api.appspot.com/random_joke"
    response = requests.get(url)
    data = response.json()

    return render_template('index.html', setup=data['setup'], punchline=data['punchline'])

if __name__ == '__main__':
    app.run(debug=True)