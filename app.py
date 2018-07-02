from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'motherofgod2'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize MySQL
mysql = MySQL(app)

Articles = Articles()

# Home page
@app.route('/')
def index():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
	return render_template('article.html', id=id)	


# User registration class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='passwords do not match')
		])
	confirm = PasswordField('confirm password')


# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# create a cursor to mysqldb
		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

		# commit changes to db
		mysql.connection.commit()

		# close connection to db
		cur.close()
		flash('Registration completed successfully', 'success')

		return redirect(url_for('login'))

	return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# get form data
		username = request.form['username']
		passwordEntered = request.form['password']

		# create mysql cursor
		cur = mysql.connection.cursor()

		# get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			# get stored hash
			data = cur.fetchone()
			correctPassword = data['password']

			# compare hash with entered hash
			if sha256_crypt.verify(passwordEntered, correctPassword):
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)	
			cur.close()	
		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')


# Disable dashboard if user is logged in:
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):	
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Please login to view dashboard', 'danger')
			return redirect(url_for('login'))
	return wrap


# log out
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('Successfully logged out', 'success')
	return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
	return render_template('dashboard.html')


# Article form class
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])


# Add article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		# create cursor to mysql
		cur = mysql.connection.cursor()	

		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

		# commit to DB
		mysql.connection.commit()
		cur.close()
		flash('Article Created!', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)


if __name__ == '__main__':
	app.secret_key = 'secret123'
	app.run(debug=True)
