import os, json, datetime, re
from flask import request, render_template, redirect, url_for
from datetime import datetime, timedelta
from src.logic import articles

def search_articles(query):
    search_results = []

    for filename in os.listdir('content'):
        if filename.endswith('.json'):
            article_data = articles.load_article(filename[:-5])
            if article_data:
                latest_version = article_data['versions'][-1]
                title = latest_version['title']
                content = latest_version['content']
                content_lower = content.lower()

                if query.lower() in title.lower() or query.lower() in content_lower:
                    matches = re.finditer(re.escape(query), content_lower)
                    highlighted_content = highlight_matches(' '.join(content.split()[:30])+' <em>(...)</em> ', matches)

                    search_results.append({
                        'title': title,
                        'filename': filename[:-5],
                        'highlighted_content': highlighted_content
                    })

    return search_results

def highlight_matches(content, matches):
    highlighted_content = ""

    prev_end = 0
    for match in matches:
        start, end = match.span()
        highlighted_content += content[prev_end:start] + '<span class="highlight">' + content[start:end] + '</span>'
        prev_end = end

    highlighted_content += content[prev_end:]
    return highlighted_content

