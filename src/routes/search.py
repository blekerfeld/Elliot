from flask import Blueprint, render_template, request
from flask_paginate import Pagination, get_page_parameter
from src.logic import search as search_logic

# Create a Blueprint instance for the search routes
blueprint_search = Blueprint('search', __name__)

@blueprint_search.route('/search')
def search():
    query = request.args.get('query', '').strip()
    page = request.args.get(get_page_parameter(), type=int, default=1)

    if query:
        search_results = search_logic.search_articles(query)
    else:
        search_results = []

    per_page = 10  # Adjust as needed
    total_results = len(search_results)
    pagination = Pagination(page=page, total=total_results, per_page=per_page, css_framework='bootstrap4')

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = search_results[start_idx:end_idx]

    return render_template('search_results.html', query=query, results=paginated_results, pagination=pagination)
