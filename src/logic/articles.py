import os
import re
import json
import difflib
from flask import request, render_template, redirect, url_for
from datetime import datetime
import xml.etree.ElementTree as ET

def load_article(filename):
    file_path = os.path.join('content', filename + '.json')
    with open(file_path, 'r') as file:
        article_data = json.load(file)
    return article_data

def get_article_list():
    article_list = []
    for filename in os.listdir('content'):
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
    file_path = os.path.join('content', filename + '.json')

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
    file_path = os.path.join('content', f'{filename}.json')
    with open(file_path, 'w') as file:
        json.dump(article_data, file, indent=4)


def rename_article_file(old_filename, new_filename):
    old_file_path = os.path.join('content', f'{old_filename}.json')
    new_file_path = os.path.join('content', f'{new_filename}.json')
    
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

    for filename in os.listdir('content'):
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

def render_block_content(content, variables):
    for variable, value in variables.items():
        content = content.replace(r'@$' + variable, value)
    return content

def render_article_with_blocks(article_content):
    block_reference_pattern = r'\{\{([a-zA-Z0-9_]+)(.*?)\}\}'
    rendered_content = article_content

    matches = re.findall(block_reference_pattern, article_content)
    for block_name, variable_string in matches:
        # Load block data if it exists
        try:
            block_data = load_article("_bl_" + block_name)
        except FileNotFoundError:
            block_data = None

        if block_data:
            variables = {}
            if variable_string:
                variable_pairs = variable_string.split('|')
                for variable_pair in variable_pairs:
                    parts = variable_pair.split('=')
                    if len(parts) == 2:
                        variable, value = parts
                        variables[variable] = value

            # Render block content with variables
            block_content = render_block_content(block_data['versions'][-1]['content'], variables)
            rendered_content = rendered_content.replace('{{' + block_name + variable_string + '}}', block_content)
        else:
            # If block not found, keep the text as is
            rendered_content = rendered_content.replace('{{' + block_name + variable_string + '}}', '{{' + block_name + variable_string + '}}')

    return rendered_content


def parse_menu_content(menu_content):
    root = ET.fromstring(menu_content)
    parsed_menu = []

    def parse_item(item):
        item_type = item.get("type")
        title = item.text.strip()
        link = item.get("link", "/") if item_type == "page" else url_for('articles.view_article', filename=item.get("filename"))
        sub_items = [parse_item(sub) for sub in item.findall("subitem")]
        return {"type": item_type, "link": link, "title": title, "sub_items": sub_items}

    for item in root.findall("item"):
        parsed_menu.append(parse_item(item))

    return parsed_menu