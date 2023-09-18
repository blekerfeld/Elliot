from flask import Blueprint, render_template, request, redirect, url_for
from flask_paginate import Pagination, get_page_parameter
from src.logic import articles
from datetime import datetime
import os

# Create a Blueprint instance for the search routes
blueprint_article = Blueprint('articles', __name__)

@blueprint_article.context_processor
def inject_articles_functions():
    return dict(load_article=articles.load_article, parse_menu_content = articles.parse_menu_content)

@blueprint_article.route('/')
def index():
    try:
        homepage_article = articles.load_article("_sp_Homepage")
        menu_article = articles.load_article('_sp_Menu')
        latest_version = menu_article['versions'][-1]
        menu_content = latest_version['content']
        parsed_menu = articles.parse_menu_content(menu_content)
        print(menu_content)
        return render_template('special_page.html', article=homepage_article)
    except:
        return render_template('index.html')
    
@blueprint_article.route('/about')
def about():
    try:
        about = articles.load_article("_sp_About")
        return render_template('special_page.html', article=about)
    except:
        return render_template('index.html')


@blueprint_article.route('/article/<filename>')
def view_article(filename):
    try:
        articleFile = articles.load_article(filename)
    except FileNotFoundError:
        return "Article not found", 404
    
    if articleFile:
        return render_template('article.html', article=articleFile)
    else:
        return render_template('article.html', article=None)
    
@blueprint_article.route('/article/<filename>/versions')
def view_article_versions(filename):
    article = articles.load_article(filename)
    return render_template('article_versions.html', article=article)

@blueprint_article.route('/article/<filename>/compare_versions', methods=['POST'])
def compare_versions(filename):
    selected_versions = request.form.getlist('selected_versions')

    if len(selected_versions) != 2:
        return "Please select exactly two versions to compare.", 400

    article_data = articles.load_article(filename)
    version1 = next((v for v in article_data['versions'] if v['timestamp'] == selected_versions[0]), None)
    version2 = next((v for v in article_data['versions'] if v['timestamp'] == selected_versions[1]), None)

    if not version1 or not version2:
        return "Selected versions not found.", 404

    return render_template('compare_versions.html', article_data=article_data, version1=version1, version2=version2, render_diff=articles.render_diff)

@blueprint_article.route('/article/<filename>/restore/<timestamp>')
def restore_version(filename, timestamp):
    article_data = articles.load_article(filename)
    version = next((v for v in article_data['versions'] if v['timestamp'] == timestamp), None)

    if version:
        version['timestamp'] = datetime.now().isoformat()
        article_data['versions'].append(version)  # Replace versions with the selected version
        articles.save_article_data(filename, article_data)
        return redirect(url_for('articles.view_article', filename=filename))
    else:
        return "Version not found", 404


@blueprint_article.route('/article/<filename>/version/<timestamp>')
def view_specific_version(filename, timestamp):
    article_data = articles.load_article(filename)
    version = next((v for v in article_data['versions'] if v['timestamp'] == timestamp), None)
    if version:
        return render_template('view_specific_version.html', article_data=article_data, version=version)
    else:
        return "Version not found", 404

@blueprint_article.route('/new', methods=['GET', 'POST'])
def new_article():
    return articles.create_or_edit_article(None)

@blueprint_article.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_article(filename):
    return articles.create_or_edit_article(filename)

@blueprint_article.route('/tag/<tag>')
def tagged_articles(tag):
    page = request.args.get(get_page_parameter(), type=int, default=1)
    articles_per_page = 10  # Adjust as needed

    # Get a list of articles with the specified tag
    tagged_articles = articles.get_tagged_articles(tag)

    # Paginate the tagged articles
    pagination = Pagination(page=page, total=len(tagged_articles), per_page=articles_per_page, css_framework='bootstrap4')
    articles_to_display = tagged_articles[(page - 1) * articles_per_page:page * articles_per_page]

    return render_template('tagged_articles.html', tag=tag, articles=articles_to_display, pagination=pagination)

@blueprint_article.route('/article/<filename>/delete/<timestamp>')
def delete_version(filename, timestamp):
    article = articles.load_article(filename)
    version = next((v for v in article.versions if v['timestamp'] == timestamp), None)
    if version:
        article.versions.remove(version)
        articles.save_article_data(filename, article)
        return redirect(url_for('view_article_versions', filename=filename))
    else:
        return "Version not found", 404
    
@blueprint_article.route('/manage_articles', methods=['GET', 'POST'])
def manage_articles():
    page = request.args.get('page', type=int, default=1)
    articles_per_page = 10  # Adjust as needed
    articles_list = articles.get_article_list()
    pagination = Pagination(page=page, total=len(articles_list), per_page=articles_per_page, css_framework='bootstrap4')
    articles_to_display = articles_list[(page-1)*articles_per_page:page*articles_per_page]
    print(articles_list)
    return render_template('manage_articles.html', articles=articles_to_display, pagination=pagination)

@blueprint_article.route('/confirm_delete/<filename>')
def confirm_delete(filename):
    article_data = articles.load_article(filename)  
    return render_template('confirm_delete.html', article=article_data)

@blueprint_article.route('/delete_article/<filename>', methods=['GET', 'POST'])
def delete_article(filename):
    article_data = articles.load_article(filename)
    if article_data:
        os.remove(os.path.join('content', filename + '.json'))
    return redirect(url_for('manage_articles'))


@blueprint_article.route('/perform_bulk_action', methods=['POST'])
def perform_bulk_action():
    if request.method == 'POST':
        bulk_action = request.form.get('bulk_action')
        selected_articles = request.form.getlist('selected_articles')

        if bulk_action == 'delete':
            for filename in selected_articles:
                article_data = articles.load_article(filename)
                if article_data:
                    os.remove(os.path.join('content', filename + '.json'))

    return redirect(url_for('articles.manage_articles'))