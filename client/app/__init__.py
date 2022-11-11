from flask import Flask

app = Flask(__name__)
app.config.from_mapping(WTF_CSRF_ENABLED=True, SECRET_KEY='dev')


from app import views