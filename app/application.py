from flask import Flask, Response, request, url_for, redirect, jsonify, render_template, session, make_response, request, current_app
from secrets import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
from feedgen.feed import FeedGenerator
from datetime import timedelta, datetime
from functools import update_wrapper
from flask_oauth import OAuth
from os import environ
import requests

time_format = "%Y-%M-%d %H:%M:%s"
author = "Martyn Pratt"
email = "martynjamespratt@gmail.com"
if environ.get("env"):
    static_url = environ.get("static_host") + environ.get("static_path")
else:
    static_url = '/static'

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

def facebook_auth():
    try:
       data = facebook.get('/me').data
       return data
    except:
       return None

@app.route("/rss")
def rss_feed(feed="page", db="https://notdb.martyni.co.uk"):
    bucket = "authmartynicouk"
    if request.args.get("tag"):
        feed=request.args.get("tag")
    feed_url = "{db}/{bucket}/list/{feed}?reverse=true".format(
            db=db,
            bucket=bucket,
            feed=feed
            )
    episodes_links = requests.get(feed_url).json()
    episodes = [requests.get(db + link).json() for link in episodes_links]
    print episodes
    description = str(episodes[0].get('description'))
    author      = str(episodes[0].get('author'))
    title       = feed
    email       = "martynjamespratt@gmail.com"
    fg          = FeedGenerator()
    fg.load_extension('podcast')
    fg.id(request.url)
    fg.podcast.itunes_category('Technology', 'Podcasting')
    fg.author({'name': author, 'email': email})
    fg.link(href=request.url, rel='self')
    fg.description(description)
    fg.title(title)
    fg.image(url="{db}/{bucket}/file/{feed}_image.png".format(
            db=db,
            bucket=bucket,
            feed=feed
            ),
            title=feed.title(),
            link=request.url,
            width='123',
            height='123',
            description=description)
    counter = 1
    for i in episodes:
       fe = fg.add_entry()
       fe.id(str(counter) + "mp3")
       fe.title(i.get('title').title())
       fe.description(i.get("contents")[0].replace("`", "'"))
       if i.get("media"):
          fe.enclosure(i.get("media"), 0, 'audio/mpeg')
       fe.link(href=request.url, rel='alternate')
       fe.author(name=i.get("author"), email=i.get("email")) 
    return Response(fg.rss_str(), mimetype='text/xml')
       

@app.route("/")
def index():
    auth = facebook_auth()
    if auth:
        user_id = auth.get('id')
        user_name = auth.get('name')
    else:    
        user_name = 'None'
    if request.args.get("refer"):
       referrer= "https://notdb.martyni.co.uk" + request.args.get("refer")
    else:
       referrer = None
    print referrer
    return render_template("index.html", user_name=user_name, url_4=url_4, static_url=static_url, referrer=referrer)

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
