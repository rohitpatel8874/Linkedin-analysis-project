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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/job_analysis')
def job_analysis():
    # Generate the graphs
    graph1_html = common_job_titles()
    graph2_html = employment_type_distribution()
    graph3_html = seniority_level_distribution()
    graph4_html = seniority_level_by_employment_type()
    graph5_html = top_companies()
    # Add more graphs as needed
    return render_template('job_analysis.html', graph1_html=graph1_html, graph2_html=graph2_html, graph3_html=graph3_html, graph4_html=graph4_html, graph5_html=graph5_html)





#Graphs functions

#common job titles
def common_job_titles():
    top_titles = df['title'].value_counts().nlargest(15).reset_index()
    top_titles.columns = ['Job Title', 'Count']

    fig1 = px.bar(top_titles, 
                  x='Count', 
                  y='Job Title',
                  orientation='h',
                  title="Top 15 Most Common Job Titles",
                  color='Count',
                  color_continuous_scale='blues',
                  text='Count')
    
    fig1.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={
            'font_size': 24,
            'xanchor': 'center',
            'x': 0.5
        },
        yaxis=dict(
            title='',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        xaxis=dict(
            title='Number of Positions',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        showlegend=False,
        height=600
    )
    
    fig1.update_traces(
        textposition='outside',
        textfont=dict(size=12),
        hovertemplate="<b>%{y}</b><br>Positions: %{x}<extra></extra>"
    )

    graph1_html = pio.to_html(fig1, full_html=False)
    return graph1_html

# Distribution of Employment Types
def employment_type_distribution():
    employment_dist = df['Employment type'].value_counts().reset_index()
    employment_dist.columns = ['Employment Type', 'Count']

    fig2 = px.pie(employment_dist, names='Employment Type', values='Count',
                title="Distribution of Employment Types",
                hole=0.3) 

    graph2_html = pio.to_html(fig2, full_html=False)
    return graph2_html

# Distribution of Seniority Levels
def seniority_level_distribution():
    seniority_dist = df['Seniority level'].value_counts().reset_index()
    seniority_dist.columns = ['Seniority Level', 'Count']
    
    fig3 = px.bar(seniority_dist,
                  x='Seniority Level',
                  y='Count',
                  title="Distribution of Seniority Levels",
                  color='Count',
                  color_continuous_scale='blues',
                  text='Count')
    
    fig3.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={
            'font_size': 24,
            'xanchor': 'center',
            'x': 0.5
        },
        xaxis=dict(
            title='',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Number of Positions',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        showlegend=False,
        height=500
    )
    
    fig3.update_traces(
        textposition='outside',
        textfont=dict(size=12),
        hovertemplate="<b>%{x}</b><br>Positions: %{y}<extra></extra>"
    )

    graph3_html = pio.to_html(fig3, full_html=False)
    return graph3_html

# Seniority Level by Employment Type
def seniority_level_by_employment_type():
    combo = df.groupby(['Employment type', 'Seniority level']).size().reset_index(name='Count')
    
    colors = px.colors.sequential.Blues[2:]
    
    fig4 = px.bar(combo, 
                  x='Employment type', 
                  y='Count', 
                  color='Seniority level',
                  title="Seniority Level Distribution by Employment Type",
                  barmode='stack',
                  color_discrete_sequence=colors,
                  text='Count')
    
    fig4.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={
            'font_size': 24,
            'xanchor': 'center',
            'x': 0.5
        },
        xaxis=dict(
            title='Employment Type',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Number of Positions',
            tickfont=dict(size=12),
            gridcolor='lightgray'
        ),
        legend=dict(
            title='Seniority Level',
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    fig4.update_traces(
        textposition='inside',
        textfont=dict(size=10, color='white'),
        hovertemplate="<b>%{x}</b><br>%{data.name}<br>Positions: %{y}<extra></extra>"
    )

    graph4_html = pio.to_html(fig4, full_html=False)
    return graph4_html

# Top 10 Companies by Job Postings
def top_companies():
    top_companies = df['company'].value_counts().nlargest(10).reset_index()
    top_companies.columns = ['Company', 'Postings']
    
    colors = px.colors.sequential.Blues[2:]
    
    fig5 = px.pie(top_companies, 
                  names='Company', 
                  values='Postings',
                  title="Top 10 Companies by Job Postings",
                  hole=0.6,
                  color_discrete_sequence=colors)
    
    fig5.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        title={
            'font_size': 24,
            'xanchor': 'center',
            'x': 0.5
        },
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5
        ),
        annotations=[dict(text='Top 10<br>Companies', x=0.5, y=0.5, font_size=20, showarrow=False)],
        height=600
    )
    
    fig5.update_traces(
        textposition='outside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Positions: %{value}<br>Percentage: %{percent}<extra></extra>"
    )

    graph5_html = pio.to_html(fig5, full_html=False)
    return graph5_html





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)