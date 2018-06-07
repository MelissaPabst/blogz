from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
# user:password@server:portNumber/databaseName
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
# secret_key required for session
app.secret_key = 'aksdfjkaasdfadf'


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    #password = db.Column(db.String(120))
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, username, password):
        self.username = username
        #self.password = password
        self.pw_hash = make_pw_hash(password)



# relational database established between Blog & User through a foreign key
class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    post = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    blog_date = db.Column(db.DateTime)

    def __init__(self, title, post, owner, blog_date=None):
        self.title = title
        self.post = post
        self.owner = owner
        if blog_date is None:
            blog_date = datetime.utcnow()
        self.blog_date = blog_date


# endpoint is the name of the view function, not url path. hence routes are '' and not '/'
@app.before_request
def require_login():
    allowed_routes = ['login', 'list_blogs', 'index', 'signup']
    #if request.endpoint.startswith("/static/") == False and 
    if request.endpoint not in allowed_routes and 'username' not in session and not request.path.startswith('/static/'):
        return redirect('/login')




@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['Password']

        # query to match username to username in db, nets first result, unique
        # if username not in db, returns none
        user = User.query.filter_by(username=username).first()

        username_error = ''
        password_error = ''

        # check for blank fields
        if not username and not password:
            #flash("Username and password cannot be blank. Try again.")
            username_error = "Username cannot be blank."
            password_error = "Password cannot be blank."
            return render_template('login.html', username_error = username_error, password_error = password_error)
        if not password:
            #flash("Password cannot be blank. Try again.")
            password_error = "Password cannot be blank."
            return render_template('login.html', password_error = password_error, username = username)
        if not username:
            #flash("Username cannot be blank. Try again.")
            username_error = "Username cannot be blank."
            return render_template('login.html', username_error = username_error)

        # check for matching username & password, existing user
        #if user and user.password == password:
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            #flash("You are logged in")
            return redirect('/newpost')
        if user and not user.password == password:
            #flash("Incorrect password. Please try again.")
            password_error = "Incorrect password. Please try again."
            return render_template('login.html', password_error = password_error, username = username)
        if not user:
            #flash("User does not exist.")
            username_error = "User does not exist."
            return render_template('login.html', username_error = username_error)

    # if GET request   
    else:
        return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['Password']
        verify = request.form['VerifyPassword']

        username_error = ''
        password_error = ''
        password2_error = ''

        # query to look for username in db to check if username already registered.
        # if username not in db, returns none
        existing_user = User.query.filter_by(username=username).first()
        
        # check for blank fields
        if not username or not password or not verify:
            #flash("One or more fields invalid. Fields cannot be blank. Try again.")
            username_error = "Username required."
            return render_template('signup.html', username_error = username_error)
        
        # check for matching passwords
        #if not password==verify:
            #flash("Passwords must match.")
            #password2_error = "Passwords must match."
            #return render_template('signup.html', password2_error = password2_error)

        # check for valid inputs
        if len(username) < 3:
            #flash("Invalid username. Must be at least three characters.")
            username_error = "Invalid username. Must be at least three characters."
            return render_template('signup.html', username_error = username_error)
        if len(password) < 3:
            #flash("Invalid password. Must be at least three characters.")
            password_error = "Invalid password. Must be at least three characters."
            return render_template('signup.html', password_error = password_error, username = username)

        if existing_user:
            #flash("Username already exists.")
            username_error = "Username already exists."
            return render_template('signup.html', username_error = username_error)

        if not existing_user and not password==verify:
            #flash("Passwords do not match.")
            password_error = "Passwords do not match"
            password2_error = "Passwords do not match"
            return render_template('signup.html', username = username, password_error = password_error, password2_error = password2_error)


        # add user to db and create session, redirect to newpost
        if not existing_user and password==verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        
        
    # if GET request
    else: 
        return render_template('signup.html')



#@app.route('/blog', methods=['POST', 'GET'])
#def display_all_posts():
    #all_posts = Blog.query.all()
    #return render_template('blog.html', posts=all_posts)


@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():
    post_id = request.args.get('id')
    author_id = request.args.get('owner_id')
    all_posts = Blog.query.all()
    if post_id:
        indv_post = Blog.query.get(post_id)
        return render_template('indvpost.html', posts=indv_post)
    if author_id:
        posts_from_author = Blog.query.filter_by(owner_id=author_id)
        return render_template('indvauthor.html', posts=posts_from_author)
    
    return render_template('blog.html', posts=all_posts)


def is_empty(x):
    if len(x) == 0:
        return True
    else:
        return False


#@app.route('/newpost')
#def make_new_post():
    #return render_template('newpost.html')

@app.route('/newpost', methods=['GET', 'POST'])
def add_entry():

    if request.method == 'POST':
        title_error = ''
        blog_entry_error = ''

        post_title = request.form['blog_title']
        post_entry = request.form['blog_post']
        owner = User.query.filter_by(username=session['username']).first()
        new_post = Blog(post_title, post_entry, owner)

        if not is_empty(post_title) and not is_empty(post_entry):
            db.session.add(new_post)
            db.session.commit()
            post_link = "/blog?id=" + str(new_post.id)
            return redirect(post_link)
        else:
            if is_empty(post_title) and is_empty(post_entry):
                title_error = "Text for blog title is missing."
                blog_entry_error = "Text for blog entry is missing."
                return render_template('newpost.html', title_error=title_error, blog_entry_error=blog_entry_error)
            elif is_empty(post_title) and not is_empty(post_entry):
                title_error = "Text for blog title is missing."
                return render_template('newpost.html', title_error=title_error, post_entry=post_entry)
            elif is_empty(post_entry) and not is_empty(post_title):
                blog_entry_error = "Text for blog entry is missing."
                return render_template('newpost.html', blog_entry_error=blog_entry_error, post_title=post_title)

    else: 
        return render_template('newpost.html')

@app.route('/logout')
def logout():
    del session['username']
    #flash("You are logged out.")
    return redirect('/blog')
    

#@app.route('/', methods=['POST', 'GET'])
#def display_blog():
    #return render_template('blog.html')

@app.route('/')
def index():
    all_users = User.query.distinct()
    #author_id = request.args.get('owner_id')
    #posts_from_author = Blog.query.filter_by(owner_id=author_id)
    #if author_id:
        #return render_template('indvauthor.html', posts=posts_from_author)
    return render_template('index.html', usernames=all_users)



if __name__ == '__main__':
    app.run()