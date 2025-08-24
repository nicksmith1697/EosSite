from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('index.html', section='services')

@app.route('/about')
def about():
    return render_template('index.html', section='about')

@app.route('/contact')
def contact():
    return render_template('index.html', section='contact')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)