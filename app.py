from flask import Flask
from src.routes import articles, search, auth
from src.filters import blueprint_filters

app = Flask(__name__)
app.secret_key = 'ElliotDebug'

app.register_blueprint(auth.blueprint_auth)
app.register_blueprint(articles.blueprint_article)
app.register_blueprint(search.blueprint_search)
app.register_blueprint(blueprint_filters)

if __name__ == '__main__':
    app.run(debug=True)