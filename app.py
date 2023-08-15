from flask import Flask, render_template, request, url_for, redirect, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from flask_paginate import Pagination
import os, json, pathlib, markdown, re
import difflib
from datetime import datetime

app = Flask(__name__, template_folder='templates')
bootstrap = Bootstrap(app)

UPLOAD_FOLDER = 'uploads'
ARTICLES_DIR = 'articles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

def create_or_edit_article(filename):
    if filename == None:
        article_data = None
    else:
        article_data = load_article(filename)

    if request.method == 'POST':
        filenameOrg = filename
        filenameNew = request.form['filename']  # Use provided filename or generate one
        title = request.form['title']
        tags = [tag.strip() for tag in request.form['tags'].split(',')]
        content = request.form['content']
        print(request.args)
        if filenameNew != filename:
            rename_article_file(filename, filenameNew)

        if filenameOrg == None:
            save_article(filename, title, tags, content)
        else:
            new_version = {
                "title": title,
                "tags": tags,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            save_new_version(filenameNew, new_version)

        return redirect(url_for('view_article', filename=filenameNew))

    return render_template('create_edit_article.html', article_data=article_data)

@app.route('/confirm_delete/<filename>')
def confirm_delete(filename):
    article_data = load_article(filename)
    return render_template('confirm_delete.html', article=article_data)

@app.route('/delete_article/<filename>', methods=['GET', 'POST'])
def delete_article(filename):
    article_data = load_article(filename)
    if article_data:
        os.remove(os.path.join(ARTICLES_DIR, filename + '.json'))
    return redirect(url_for('manage_articles'))

@app.route('/new', methods=['GET', 'POST'])
def new_article():
    return create_or_edit_article(None)

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_article(filename):
    return create_or_edit_article(filename)

def save_new_version(filename, new_version):
    article_data = load_article(filename)
    if article_data:
        article_data['versions'].append(new_version)
        save_article_data(filename, article_data)

@app.route('/article/<filename>')
def view_article(filename):
    article = load_article(filename)
    return render_template('article.html', article=article)

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if query:
        search_results = search_articles(query)
    else:
        search_results = []

    return render_template('search_results.html', query=query, results=search_results)

def search_articles(query):
    search_results = []

    for filename in os.listdir('articles'):
        if filename.endswith('.json'):
            article_data = load_article(filename[:-5])
            if article_data:
                latest_version = article_data['versions'][-1]
                title = latest_version['title']
                content = latest_version['content']
                content_lower = content.lower()

                if query.lower() in title.lower() or query.lower() in content_lower:
                    matches = re.finditer(re.escape(query), content_lower)
                    highlighted_content = highlight_matches(content, matches)

                    search_results.append({
                        'title': title,
                        'filename': filename[:-5],
                        'highlighted_content': highlighted_content
                    })

    return search_results


@app.route('/article/<filename>/versions')
def view_article_versions(filename):
    article = load_article(filename)
    return render_template('article_versions.html', article=article)

@app.route('/article/<filename>/compare_versions', methods=['POST'])
def compare_versions(filename):
    selected_versions = request.form.getlist('selected_versions')

    if len(selected_versions) != 2:
        return "Please select exactly two versions to compare.", 400

    article_data = load_article(filename)
    version1 = next((v for v in article_data['versions'] if v['timestamp'] == selected_versions[0]), None)
    version2 = next((v for v in article_data['versions'] if v['timestamp'] == selected_versions[1]), None)

    if not version1 or not version2:
        return "Selected versions not found.", 404

    return render_template('compare_versions.html', article_data=article_data, version1=version1, version2=version2, render_diff=render_diff)


@app.route('/article/<filename>/version/<timestamp>')
def view_specific_version(filename, timestamp):
    article_data = load_article(filename)
    version = next((v for v in article_data['versions'] if v['timestamp'] == timestamp), None)
    if version:
        return render_template('view_specific_version.html', article_data=article_data, version=version)
    else:
        return "Version not found", 404

@app.route('/manage_articles', methods=['GET', 'POST'])
def manage_articles():
    page = request.args.get('page', type=int, default=1)
    articles_per_page = 10  # Adjust as needed
    articles = get_article_list()
    pagination = Pagination(page=page, total=len(articles), per_page=articles_per_page, css_framework='bootstrap4')
    articles_to_display = articles[(page-1)*articles_per_page:page*articles_per_page]
    return render_template('manage_articles.html', articles=articles_to_display, pagination=pagination)

@app.route('/article/<filename>/restore/<timestamp>')
def restore_version(filename, timestamp):
    article_data = load_article(filename)
    version = next((v for v in article_data['versions'] if v['timestamp'] == timestamp), None)

    if version:
        version['timestamp'] = datetime.now().isoformat()
        article_data['versions'].append(version)  # Replace versions with the selected version
        save_article_data(filename, article_data)
        return redirect(url_for('view_article', filename=filename))
    else:
        return "Version not found", 404


@app.route('/article/<filename>/delete/<timestamp>')
def delete_version(filename, timestamp):
    article = load_article(filename)
    version = next((v for v in article.versions if v['timestamp'] == timestamp), None)
    if version:
        article.versions.remove(version)
        save_article_data(filename, article)
        return redirect(url_for('view_article_versions', filename=filename))
    else:
        return "Version not found", 404

# Logic

def get_article_list():
    article_list = []
    for filename in os.listdir(ARTICLES_DIR):
        if filename.endswith('.json'):
            article_data = load_article(filename[:-5])
            if article_data:
                article_list.append({
                    'filename': filename[:-5],
                    'title': article_data['versions'][-1]['title']
                })
    return article_list

def highlight_matches(content, matches):
    highlighted_content = ""

    prev_end = 0
    for match in matches:
        start, end = match.span()
        highlighted_content += content[prev_end:start] + '<span class="highlight">' + content[start:end] + '</span>'
        prev_end = end

    highlighted_content += content[prev_end:]
    return highlighted_content

def save_article(filename, title, tags, content):
    file_path = os.path.join(ARTICLES_DIR, filename + '.json')

    timestamp = datetime.now().isoformat()
    version = {
        'title': title,
        'tags': tags,
        'content': content,
        'timestamp': timestamp
    }

    article_data = {
        'filename': filename,
        'versions': [version]
    }

    with open(file_path, 'w') as file:
        json.dump(article_data, file, indent=4)

def save_article_data(filename, article_data):
    file_path = os.path.join('articles', f'{filename}.json')
    with open(file_path, 'w') as file:
        json.dump(article_data, file, indent=4)

def load_article(filename):
    file_path = os.path.join(ARTICLES_DIR, filename + '.json')
    with open(file_path, 'r') as file:
        article_data = json.load(file)
    return article_data

def rename_article_file(old_filename, new_filename):
    old_file_path = os.path.join(ARTICLES_DIR, f'{old_filename}.json')
    new_file_path = os.path.join(ARTICLES_DIR, f'{new_filename}.json')
    
    if os.path.exists(old_file_path):
        # Load the article data from the old JSON file
        article_data = load_article(old_filename)
        
        if article_data:
            # Update the 'filename' value in the loaded article data
            article_data['filename'] = new_filename
            
            # Save the updated article data to the new JSON file
            with open(new_file_path, 'w') as new_file:
                json.dump(article_data, new_file, indent=4)
            
            # Remove the old JSON file
            os.remove(old_file_path)
    else:
        raise FileNotFoundError(f"Article file '{old_filename}.json' not found.")

@app.template_filter('render_diff')
def render_diff(text1, text2):
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))
    return '\n'.join(diff)  



@app.template_filter('link_articles')
def link_articles(content):
    def replace_link(match):
        link_info = match.group(1)
        parts = link_info.split('|')
        
        if len(parts) == 1:
            article_name = parts[0]
            article_data = load_article(article_name)
            if not article_data:
                return f'<a href="#" class="invalid-link">{article_name}</a>'
            
            article_title = article_data['versions'][-1]['title']
            article_url = url_for('view_article', filename=article_name)
            return f'<a href="{article_url}">{article_title}</a>'
        
        elif len(parts) == 2:
            article_name = parts[0]
            custom_text = parts[1]
            article_data = load_article(article_name)
            if not article_data:
                return f'<a href="#" class="invalid-link">{custom_text}</a>'
            
            article_url = url_for('view_article', filename=article_name)
            return f'<a href="{article_url}">{custom_text}</a>'
        
        return match.group(0)  # Return unchanged if format not recognized

    linked_content = re.sub(r'\[([^]]+)\]', replace_link, content)
    return linked_content


@app.template_filter('markdown_to_html')
def markdown_to_html(content):
    return markdown.markdown(content, extensions=['fenced_code', 'tables'])



if __name__ == '__main__':
    app.run(debug=True)