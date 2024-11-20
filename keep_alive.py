import os
from flask import Flask, render_template
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # This serves the HTML page

@app.route('/ping')
def ping():
    return 'Pong!'

def run():
    app.run(host='0.0.0.0', port=8080)  # Host on port 8080 for Render

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

if __name__ == '__main__':
    keep_alive()
