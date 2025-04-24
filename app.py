from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_bcrypt import bcrypt
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)
app.secret_key = 'supersecretmre'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
    def __init__(self, username, password, email, name):
        self.username = username
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.email = email
        self.name = name

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    

with app.app_context():
    db.create_all()



fig4 = go.Figure()
df = pd.read_csv('jobs.csv')

@app.route('/')
def index():
    # flash('Welcome to the Flask App', 'info')
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
        if user and user.check_password(password):
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, password=password, email=email, name=name)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    return render_template('Registration.html')



#Graphs functions

#common job titles
def common_job_titles():
    fig1 = go.Figure()
    top_titles = df['title'].value_counts().nlargest(15).reset_index()
    top_titles.columns = ['Job Title', 'Count']

    fig1 = px.bar(top_titles, x='Job Title', y='Count',
              title="Top 15 Most Common Job Titles",
              color='Count', text='Count')
    fig1.update_layout(xaxis_tickangle=-45)

    graph1_html = pio.to_html(fig1, full_html=False)
    return graph1_html

# Distribution of Employment Types
def employment_type_distribution():
    fig2 = go.Figure()
    employment_dist = df['Employment type'].value_counts().reset_index()
    employment_dist.columns = ['Employment Type', 'Count']

    fig2 = px.pie(employment_dist, names='Employment Type', values='Count',
              title="Distribution of Employment Types",
              hole=0.3)
    graph2_html = pio.to_html(fig2, full_html=False)
    return graph2_html   # Donut style


# Distribution of Seniority Levels
def seniority_level_distribution():
    fig3 = go.Figure()
    fig3 = px.histogram(df, x='Seniority level',
                    title="Distribution of Seniority Levels",
                    color='Seniority level')
    fig3.update_layout(xaxis_title='Seniority Level', yaxis_title='Count')
    graph3_html = pio.to_html(fig3, full_html=False)
    return graph3_html   # Donut style

   


# Seniority Level by Employment Type
def seniority_level_by_employment_type():
    fig4 = go.Figure()
    combo = df.groupby(['Employment type', 'Seniority level']).size().reset_index(name='Count')

    fig4 = px.bar(combo, x='Employment type', y='Count', color='Seniority level',
              title="Seniority Level by Employment Type",
              barmode='stack')
    graph4_html = pio.to_html(fig4, full_html=False)
    return graph4_html   # Donut style


#analysis page routes
@app.route('/job_analysis')
def job_analysis():
    # Generate the graphs
    graph1_html = common_job_titles()
    graph2_html = employment_type_distribution()
    graph3_html = seniority_level_distribution()
    graph4_html = seniority_level_by_employment_type() 

    # Add more graphs as needed
    return render_template('job_analysis.html', graph1_html=graph1_html, graph2_html=graph2_html, graph3_html=graph3_html, graph4_html=graph4_html)





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)