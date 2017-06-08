from flask import Flask, Response, request, url_for, redirect, jsonify, render_template, session
from secrets import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
import datetime
from flask_oauth import OAuth

app = Flask(__name__)

time_format = "%Y-%M-%d %H:%M:%s"
author = "Martyn Pratt"
email = "martynjamespratt@gmail.com"

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
    return datetime.datetime.utcnow().strftime(time_format)


def time_load(time_string):
    return datetime.datetime.strptime(time_string, time_format)


def time_diff(time_1, time_2):
    if type(time_1) == str:
        time_1 = datetime.datetime.strptime(time_1,  time_format)
    if type(time_2) == str:
        time_2 = datetime.datetime.strptime(time_2,  time_format)
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

    return render_template("base.html", user_name=user_name)

@app.route("/test")
def test():
    return "OMG"
if __name__ == '__main__':
    app.run(host='0.0.0.0')