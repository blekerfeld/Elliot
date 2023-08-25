import markdown, re, difflib
from datetime import datetime, timedelta
from humanize import naturaltime
from flask import Blueprint, url_for
from src.logic import articles as logic_articles

# Create a Blueprint instance for the filters
blueprint_filters = Blueprint('filters', __name__)

@blueprint_filters.app_template_filter('render_blocks')
def render_blocks(content):
    return logic_articles.render_article_with_blocks(content)

@blueprint_filters.app_template_filter('render_diff')
def render_diff(text1, text2):
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))
    return '\n'.join(diff)

@blueprint_filters.app_template_filter('format_timestamp')
def format_timestamp(timestamp):
    now = datetime.now()
    timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")

    if now.date() == timestamp_dt.date():
        return naturaltime(timestamp_dt)
    elif now.date() - timestamp_dt.date() == timedelta(days=1):
        return f"Yesterday at {timestamp_dt.strftime('%H:%M')}"
    else:
        return timestamp_dt.strftime("%A %b %d, %Y, %H:%M")

@blueprint_filters.app_template_filter('link_articles')
def link_articles(content):
    def replace_link(match):
        article_name = match.group(1)
        
        try:
            article_data = logic_articles.load_article(article_name)
        except FileNotFoundError:
            return f'<a href="#" class="invalid-link">{article_name}</a>'

        article_title = article_data['versions'][-1]['title']
        article_url = url_for('articles.view_article', filename=article_name)
        return f'<a href="{article_url}">{article_title}</a>'

    linked_content = re.sub(r'\[([^]]+)\]', replace_link, content)
    return linked_content


@blueprint_filters.app_template_filter('markdown_to_html')
def markdown_to_html(content):
    return markdown.markdown(content, extensions=['fenced_code', 'tables'])
