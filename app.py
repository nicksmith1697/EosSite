from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

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

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        service = request.form.get('service')
        message = request.form.get('message')
        
        if not all([name, email, company, service, message]):
            flash('All fields are required', 'error')
            return redirect(url_for('contact'))
        
        msg = Message(
            subject=f'New Contact Form Submission from {name}',
            recipients=['info@eoscloudconsulting.com'],
            body=f'''
New contact form submission:

Name: {name}
Email: {email}
Company: {company}
Service Interest: {service}
Message: {message}
            ''',
            reply_to=email
        )
        
        mail.send(msg)
        flash('Thank you for your message! We will get back to you soon.', 'success')
        
    except Exception as e:
        flash('Sorry, there was an error sending your message. Please try again.', 'error')
        
    return redirect(url_for('contact'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)