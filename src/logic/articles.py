import os, json, datetime
from flask import request, render_template, redirect, url_for
from datetime import datetime, timedelta
import os, json, pathlib, markdown, re, difflib

def load_article(filename):
    file_path = os.path.join('articles', filename + '.json')
    with open(file_path, 'r') as file:
        article_data = json.load(file)
    return article_data

def get_article_list():
    article_list = []
    for filename in os.listdir('articles'):
        if filename.endswith('.json'):
            article_data = load_article(filename[:-5])
            if article_data:
                article_list.append({
                    'filename': filename[:-5],
                    'title': article_data['versions'][-1]['title'],
                    'tags': article_data['versions'][-1]['tags']
                })
    return article_list

def create_or_edit_article(filename):
    filenameOrg = filename
    
    try:
        filename_work = request.form['filename']
    except:
        filename_work = filename
    
    if filename is None:
        article_data = None
    else:
        article_data = load_article(filename)
    
    if request.method == 'POST':
        filename_new = request.form['filename']
        title = request.form['title']
        tags = [tag.strip() for tag in request.form['tags'].split(',')]
        content = request.form['content']
        print(request.args)
        
        if filename is None:
            # Create a new article
            save_article(filename_new, title, tags, content)
            return redirect(url_for('articles.view_article', filename=filename_new))
        else:
            if article_data and article_data['versions']:
                latest_version = article_data['versions'][-1]
                
                # Check if the new version is different from the latest version
                if (title != latest_version['title'] or
                    tags != latest_version['tags'] or
                    content != latest_version['content']):
                    if filenameOrg != filename_new:  # Check if filename changed
                        rename_article_file(filenameOrg, filename_new)
                        
                    new_version = {
                        "title": title,
                        "tags": tags,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    save_new_version(filename_new, new_version)
                    
            return redirect(url_for('articles.view_article', filename=filename_new))
    
    return render_template('create_edit_article.html', article_data=article_data)

def save_article(filename, title, tags, content):
    file_path = os.path.join('articles', filename + '.json')

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


def rename_article_file(old_filename, new_filename):
    old_file_path = os.path.join('articles', f'{old_filename}.json')
    new_file_path = os.path.join('articles', f'{new_filename}.json')
    
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
    
def save_new_version(filename, new_version):
    article_data = load_article(filename)
    if article_data:
        article_data['versions'].append(new_version)
        save_article_data(filename, article_data)

def get_tagged_articles(tag):
    tagged_articles = []

    for filename in os.listdir('articles'):
        if filename.endswith('.json'):
            article_data = load_article(filename[:-5])
            if article_data:
                latest_version = article_data['versions'][-1]
                if tag in latest_version['tags']:
                    tagged_articles.append({
                        'filename': filename[:-5],
                        'title': latest_version['title'],
                        'content' : ' '.join(latest_version['content'].split()[:30])+' <em>(...)</em> ',
                        'timestamp': latest_version['timestamp']
                    })

    return tagged_articles

def render_diff(text1, text2):
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))

    result = []
    for line in diff:
        if line.startswith('+ '):
            result.append(f'<span class="diff-added">{line}</span>')
        elif line.startswith('- '):
            result.append(f'<span class="diff-removed">{line}</span>')
        else:
            result.append(line)

    return '\n'.join(result)
