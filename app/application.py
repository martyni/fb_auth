from flask import Flask, Response, request, url_for, redirect, jsonify, render_template, session, make_response, request, current_app
from secrets import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
from datetime import timedelta, datetime
from functools import update_wrapper
from flask_oauth import OAuth
from os import environ

time_format = "%Y-%M-%d %H:%M:%s"
author = "Martyn Pratt"
email = "martynjamespratt@gmail.com"
if environ.get("env"):
    static_url = environ.get("static_host") + environ.get("static_path")
else:
    static_url = ''

app = Flask(__name__, static_url_path='/static')
def url_sanitizer(raw_path):
    if ".amazonaws.com" not in request.url:
        return raw_path.replace('/prod', '').replace('/stge', '').replace('/dev', '')
    else:
        return raw_path


def path_sanitizer(raw_path):
    return raw_path.lower().replace("_", " ")


def url_4(*args, **qwargs):
    raw_path = url_for(*args, **qwargs)
    return url_sanitizer(raw_path)


def time_dump():
    return datetime.utcnow().strftime(time_format)


def time_load(time_string):
    return datetime.strptime(time_string, time_format)


def time_diff(time_1, time_2):
    if type(time_1) == str:
        time_1 = datetime.strptime(time_1,  time_format)
    if type(time_2) == str:
        time_2 = datetime.strptime(time_2,  time_format)
    return time_1 - time_2

#----------------------------------------
# facebook authentication
#----------------------------------------


app.secret_key = FACEBOOK_APP_SECRET

oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',

    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': ('email, ')}
)

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('facebook_token', None)

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_4('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_4('index')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)
    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')

    return redirect(next_url)

@app.route("/logout")
def logout():
    pop_login_session()
    return redirect(url_4('index'))

@app.route("/")
def index():
    user_name = 'null'
    try:
       data = facebook.get('/me').data
       if 'id' in data and 'name' in data:
           user_id = data['id']
           user_name = data['name']
    except:
       pass
    print static_url
    return render_template("index.html", user_name=user_name, url_4=url_4, static_url=static_url)

@app.route("/style.css")
def style():
    template = render_template("style.css", static_url=static_url)
    r = Response(template, mimetype="text/css")
    return r

@app.route("/test")
def test():
    return "OMG"
if __name__ == '__main__':
    app.run(host='0.0.0.0')
