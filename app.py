from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
import os
import glob
from bs4 import BeautifulSoup
import re
from datetime import datetime

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

def get_blog_articles():
    blog_posts = []
    blog_dir = os.path.join(os.path.dirname(__file__), 'blog_posts')
    
    if not os.path.exists(blog_dir):
        return blog_posts
    
    # Group files by date from filename
    date_groups = {}
    all_files = os.listdir(blog_dir)
    
    for filename in all_files:
        if filename.endswith(('.txt', '.html')):
            # Extract date from filename
            date_match = re.search(r'\(([^)]+)\)', filename)
            if date_match:
                date_str = date_match.group(1)
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(filename)
    
    # Process each date group as a single blog post
    for date_str, files in date_groups.items():
        try:
            title = "Untitled Article"
            content_file = None
            thumbnail_path = None
            
            # Find title file and content file
            for filename in files:
                if 'title' in filename.lower():
                    # Read title from title file
                    title_path = os.path.join(blog_dir, filename)
                    with open(title_path, 'r', encoding='utf-8') as f:
                        title = f.read().strip()
                elif filename.endswith(('.txt', '.html')) and 'title' not in filename.lower():
                    content_file = filename
            
            # Find thumbnail
            possible_thumbnails = [
                f"thumbnail({date_str}).png",
                f"thumbnail({date_str}).jpg",
                f"thumbnail({date_str}).jpeg"
            ]
            
            for thumb_name in possible_thumbnails:
                thumb_path = os.path.join(blog_dir, thumb_name)
                if os.path.exists(thumb_path):
                    thumbnail_path = thumb_name
                    break
            
            # Read content for preview
            if content_file:
                content_path = os.path.join(blog_dir, content_file)
                with open(content_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read().strip()
                
                # Extract text for preview
                if content_file.endswith('.html') and '<p>' in raw_content:
                    soup = BeautifulSoup(raw_content, 'html.parser')
                    text_content = soup.get_text()
                else:
                    text_content = raw_content
                
                blog_posts.append({
                    'title': title,
                    'filename': content_file,  # Use content file for the article link
                    'thumbnail': thumbnail_path,
                    'date': date_str,
                    'preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
                })
            
        except Exception as e:
            print(f"Error processing date group {date_str}: {e}")
            continue
    
    return sorted(blog_posts, key=lambda x: x['date'], reverse=True)

@app.route('/blog')
def blog():
    articles = get_blog_articles()
    return render_template('blog.html', articles=articles)

@app.route('/blog/<filename>')
def blog_article(filename):
    blog_dir = os.path.join(os.path.dirname(__file__), 'blog_posts')
    file_path = os.path.join(blog_dir, filename)
    
    if not os.path.exists(file_path) or not (filename.endswith('.txt') or filename.endswith('.html')):
        return "Article not found", 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read().strip()
        
        # Handle different content types
        if filename.endswith('.html') and '<p>' in raw_content and not '<table>' in raw_content:
            # Clean HTML file with proper paragraphs - use directly
            soup = BeautifulSoup(raw_content, 'html.parser')
            # Extract body content if it exists, otherwise use all content
            body = soup.find('body') or soup
            article_content = str(body)
            text_content = soup.get_text()
        elif '<html>' in raw_content and '<table>' in raw_content:
            # Old SheetJS table format
            soup = BeautifulSoup(raw_content, 'html.parser')
            table_cell = soup.find('td', {'data-t': 's'})
            if table_cell and table_cell.get('data-v') != 'output':
                raw_text = table_cell.get('data-v')
                import html
                raw_text = html.unescape(raw_text)
                text_content = raw_text.replace('<br/><br/>', '\n\n').replace('<br/>', ' ').replace('<br>', ' ')
                paragraphs = raw_text.split('<br/><br/>')
                article_content = ''
                for paragraph in paragraphs:
                    if paragraph.strip():
                        clean_p = paragraph.strip().replace('<br/>', ' ').replace('<br>', ' ')
                        article_content += f'<p>{clean_p}</p>'
            else:
                text_content = soup.get_text()
                article_content = f'<p>{text_content}</p>'
        else:
            # Plain text
            text_content = raw_content
            paragraphs = raw_content.split('\n\n')
            article_content = ''
            for paragraph in paragraphs:
                if paragraph.strip():
                    article_content += f'<p>{paragraph.strip()}</p>'
        
        # Find matching thumbnail
        file_stem = os.path.splitext(filename)[0]
        thumbnail_path = None
        possible_thumbnails = [
            f"thumbnail{file_stem.replace('Blog_Article', '')}.png",
            f"thumbnail({file_stem.split('(')[-1].split(')')[0]}).png" if '(' in file_stem else None,
            f"{file_stem}.png"
        ]
        
        for thumb_name in possible_thumbnails:
            if thumb_name:
                thumb_path = os.path.join(blog_dir, thumb_name)
                if os.path.exists(thumb_path):
                    thumbnail_path = thumb_name
                    break
        
        # Extract title - first check for title file
        title = "Untitled Article"
        date_match = re.search(r'\(([^)]+)\)', filename)
        if date_match:
            date_str = date_match.group(1)
            # Look for title file with same date
            title_file = f"Blog_Article_Title({date_str}).txt"
            title_path = os.path.join(blog_dir, title_file)
            if os.path.exists(title_path):
                try:
                    with open(title_path, 'r', encoding='utf-8') as f:
                        title = f.read().strip()
                except Exception:
                    pass
        
        # Fallback to old method if no title file found
        if title == "Untitled Article":
            if "observability" in text_content.lower():
                title = "Cloud-Native Observability: Beyond Digital Transformation"
            elif "Confidential Computing" in text_content:
                title = "Confidential Computing: The Missing Piece of Cloud Security"
            else:
                sentences = text_content.split('.')[:2]
                if sentences and len(sentences[0].strip()) > 10:
                    clean_sentence = sentences[0].strip()[:80]
                    clean_sentence = clean_sentence.replace('"', '').replace('?', '').strip()
                    if clean_sentence:
                        title = clean_sentence + "..." if len(sentences[0]) > 80 else clean_sentence
        
        # Extract date from filename
        date_match = re.search(r'\(([^)]+)\)', filename)
        date_str = date_match.group(1) if date_match else "Unknown"
        
        return render_template('blog_article.html', 
                             content=article_content, 
                             filename=filename,
                             thumbnail=thumbnail_path,
                             title=title,
                             date=date_str)
    except Exception as e:
        return f"Error loading article: {e}", 500

@app.route('/blog_posts/<filename>')
def blog_image(filename):
    blog_dir = os.path.join(os.path.dirname(__file__), 'blog_posts')
    return send_from_directory(blog_dir, filename)

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
    app.run(debug=True, host='0.0.0.0', port=5000)