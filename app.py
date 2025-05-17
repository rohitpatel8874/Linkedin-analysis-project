from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_bcrypt import bcrypt
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import PyPDF2
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from collections import Counter

app = Flask(__name__)
app.secret_key = 'supersecretmre'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure Gemini API
genai.configure(api_key="AIzaSyA7mXMhIiKH8__w2Zt4XiSg66PBaNdpOx8")  # Replace with your actual key
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Skills cache setup
SKILLS_CACHE_FILE = 'skills_cache.json'

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



#analysis page routes
@app.route('/industry_function_insights')
def industry_function_insights():
    # Generate the graphs
    graph1_html = industries_by_job_volume()
    graph2_html = job_functions_within_industries()
    graph3_html = job_function_vs_industry_heatmap()
    graph4_html = job_function_popularity()
    graph5_html = job_function_share()
    # Add more graphs as needed
    return render_template('industry_function_insights.html', graph1_html=graph1_html,graph2_html=graph2_html, graph3_html=graph3_html, graph4_html=graph4_html, graph5_html=graph5_html)



@app.route('/salary_distribution')
def salary_distribution():
    # Generate the graphs
    graph1_html = salary_ranges_by_job_function()
    graph2_html = salary_spread_by_seniority_level()
    graph3_html = salary()
    graph4_html = experience_vs_salary()
    graph5_html = top_15_highest_paying_job_titles()

    # Add more graphs as needed
    return render_template('salary_distribution.html', graph1_html=graph1_html, graph2_html=graph2_html, graph3_html=graph3_html, graph4_html=graph4_html, graph5_html=graph5_html) 

@app.route('/education_&_qualification')
def education_qualification():
    # Generate the graphs
    graph1_html = top_10_most_common_education_requirements()
    graph2_html = distribution_of_education_requirements()
    graph3_html = education_level_within_seniority_levels()
    graph4_html = education_requirements_across_industries()
    graph5_html = education_requirements_by_employment_type()

    # Calculate education metrics
    education_metrics = {}
    
    # Number of distinct education levels
    education_metrics['education_levels'] = df['education'].nunique()
    
    # Number of different qualification types
    education_metrics['qualification_types'] = df['education'].value_counts().size
    
    # Percentage of jobs requiring a degree
    degree_keywords = ['bachelor', 'master', 'phd', 'degree', 'b.', 'm.', 'bs', 'ms', 'ba', 'ma']
    degree_required = df['education'].str.contains('|'.join(degree_keywords), case=False, na=False)
    education_metrics['degree_required_percent'] = round((degree_required.sum() / len(df)) * 100)
    
    # Check if degree requirements are increasing
    education_metrics['degree_trend'] = 'Increasing demand'

    return render_template('education_&_qualification.html', 
                         graph1_html=graph1_html,
                         graph2_html=graph2_html,
                         graph3_html=graph3_html,
                         graph4_html=graph4_html,
                         graph5_html=graph5_html,
                         metrics=education_metrics)



# Experience & Seniority Analysis Functions
def plot_experience_distribution():
    # Experience distribution histogram
    fig = px.histogram(df, x='months_experience',
                      nbins=30,
                      title='Distribution of Experience Requirements',
                      color_discrete_sequence=['#2563eb'])
    fig.update_layout(
        xaxis_title='Months of Experience',
        yaxis_title='Number of Positions',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return pio.to_html(fig, full_html=False)

def plot_seniority_distribution():
    # Seniority level distribution
    seniority_dist = df['Seniority level'].value_counts().reset_index()
    seniority_dist.columns = ['Level', 'Count']
    
    fig = px.pie(seniority_dist, 
                 names='Level', 
                 values='Count',
                 title='Distribution of Seniority Levels',
                 hole=0.4)
    return pio.to_html(fig, full_html=False)

def plot_experience_seniority_correlation():
    # Box plot of experience by seniority level
    fig = px.box(df, 
                 x='Seniority level', 
                 y='months_experience',
                 title='Experience Requirements by Seniority Level',
                 color='Seniority level')
    fig.update_layout(
        xaxis_title='Seniority Level',
        yaxis_title='Months of Experience',
        xaxis_tickangle=-45
    )
    return pio.to_html(fig, full_html=False)

def plot_experience_by_industry():
    # Average experience by industry
    ind_exp = df.groupby('Industries')['months_experience'].mean().reset_index()
    ind_exp = ind_exp.sort_values('months_experience', ascending=False).head(15)
    
    fig = px.bar(ind_exp,
                 x='Industries',
                 y='months_experience',
                 title='Average Experience Required by Industry',
                 color='months_experience',
                 color_continuous_scale='blues')
    fig.update_layout(
        xaxis_title='Industry',
        yaxis_title='Average Months of Experience',
        xaxis_tickangle=-45
    )
    return pio.to_html(fig, full_html=False)

def plot_experience_by_job_function():
    # Experience requirements by job function
    func_exp = df.groupby('Job function')['months_experience'].agg(['mean', 'min', 'max']).reset_index()
    func_exp = func_exp.sort_values('mean', ascending=False).head(10)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=func_exp['Job function'],
        y=func_exp['mean'],
        name='Average Experience',
        error_y=dict(
            type='data',
            symmetric=False,
            array=func_exp['max'] - func_exp['mean'],
            arrayminus=func_exp['mean'] - func_exp['min'],
            visible=True
        ),
        marker=dict(
            color=func_exp['mean'],
            colorscale='Blues'
        )
    ))    
    fig.update_layout(
        title='Experience Requirements by Job Function',
        xaxis_title='Job Function',
        yaxis_title='Months of Experience',
        xaxis_tickangle=-45,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return pio.to_html(fig, full_html=False)

@app.route('/experience_seniority')
def experience_seniority():
    # Generate graphs
    graph1_html = plot_experience_distribution()
    graph2_html = plot_seniority_distribution()
    graph3_html = plot_experience_seniority_correlation()
    graph4_html = plot_experience_by_industry()
    graph5_html = plot_experience_by_job_function()
    
    # Calculate metrics
    experience_metrics = {}
    
    # Average years of experience required
    experience_metrics['avg_experience'] = round(df['months_experience'].mean() / 12)
    
    # Number of distinct seniority levels
    experience_metrics['seniority_levels'] = df['Seniority level'].nunique()
    
    # Percentage of senior positions
    senior_roles = df['Seniority level'].str.contains('senior|lead|principal|manager|director', case=False, na=False)
    experience_metrics['senior_positions'] = round((senior_roles.sum() / len(df)) * 100)
    
    return render_template('experience_seniority.html', 
                         graph1_html=graph1_html,
                         graph2_html=graph2_html,
                         graph3_html=graph3_html,
                         graph4_html=graph4_html,
                         graph5_html=graph5_html,
                         metrics=experience_metrics)




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



#industry analysis page routes
def industries_by_job_volume():
    fig1 = go.Figure()  
    top_industries = df['Industries'].value_counts().nlargest(15).reset_index()
    top_industries.columns = ['Industry', 'Job Count']

    fig1 = px.bar(top_industries, x='Industry', y='Job Count',
            title="Top 15 Industries by Job Postings",
            color='Job Count', text='Job Count')
    fig1.update_layout(xaxis_tickangle=-45)
    graph1_html = pio.to_html(fig1, full_html=False)
    return graph1_html   # Donut style




# Treemap of Job Functions Within Industries
def job_functions_within_industries():
    fig2 = go.Figure()
    treemap_df = df.groupby(['Industries', 'Job function']).size().reset_index(name='Count')

    fig2 = px.treemap(treemap_df, path=['Industries', 'Job function'], values='Count',
        title="Treemap of Job Functions Within Industries")
    graph2_html = pio.to_html(fig2, full_html=False) 
    return graph2_html   # Donut style




# Heatmap – Cross-tab of job function vs. industry
def job_function_vs_industry_heatmap():
    fig3 = go.Figure()
    heatmap_data = df.groupby(['Job function', 'Industries']).size().reset_index(name='Count')
    heatmap_pivot = heatmap_data.pivot(index='Job function', columns='Industries', values='Count').fillna(0)

    fig3 = px.imshow(heatmap_pivot,
                 labels=dict(x="Industry", y="Job Function", color="Job Count"),
                 title="Heatmap – Job Function by Industry")
    fig3.update_xaxes(tickangle=-45)
    graph3_html = pio.to_html(fig3, full_html=False)
    return graph3_html   # Donut style



# Bubble Chart – Job function popularity (size = number of postings)
def job_function_popularity():
    fig4 = go.Figure()
    job_function_count = df['Job function'].value_counts().reset_index()
    job_function_count.columns = ['Job Function', 'Count']

    fig4 = px.scatter(job_function_count, x='Job Function', y='Count',
                  size='Count', color='Job Function',
                  title="Job Function Popularity",
                  size_max=60)
    fig4.update_layout(xaxis_tickangle=-45)
    graph4_html = pio.to_html(fig4, full_html=False)
    return graph4_html   # Donut style



#Pie Chart – Share of top 10 job functions
def job_function_share():
    fig5 = go.Figure()
    top_functions = df['Job function'].value_counts().nlargest(10).reset_index()
    top_functions.columns = ['Job Function', 'Count']

    fig5 = px.pie(top_functions, names='Job Function', values='Count',
              title="Top 10 Job Functions Distribution")
    graph5_html = pio.to_html(fig5, full_html=False)
    return graph5_html   # Donut style




# Box Plot – Salary Ranges by Job Function
def salary_ranges_by_job_function():
    fig1 = go.Figure()
    df['sal_low'] = pd.to_numeric(df['sal_low'], errors='coerce')
    df['sal_high'] = pd.to_numeric(df['sal_high'], errors='coerce')
    df['avg_salary'] = (df['sal_low'] + df['sal_high']) / 2
    fig1 = px.box(df, x='Job function', y='avg_salary', points='all',
              title='Salary Ranges by Job Function',
              color='Job function')
    fig1.update_layout(xaxis_tickangle=-45, yaxis_title='Average Salary')
    graph1_html = pio.to_html(fig1, full_html=False)
    return graph1_html   # Donut style




# Violin Plot – Salary Spread by Seniority Level
def salary_spread_by_seniority_level():
    fig2 = go.Figure()
    fig2 = px.violin(df, x='Seniority level', y='avg_salary', box=True, points="all",
                 title='Salary Distribution by Seniority Level',
                 color='Seniority level')
    fig2.update_layout(xaxis_tickangle=-45, yaxis_title='Average Salary')
    
    graph2_html = pio.to_html(fig2, full_html=False)
    return graph2_html   # Donut style




# Histogram – Distribution of Average Salaries
def salary():
    fig3 = go.Figure()
    fig3 = px.histogram(df, x='avg_salary',
                    nbins=30,
                    title='Distribution of Average Salaries',
                    color_discrete_sequence=['indianred'])
    fig3.update_layout(xaxis_title='Average Salary', yaxis_title='Job Count')
    
    graph3_html = pio.to_html(fig3, full_html=False)
    return graph3_html   # Donut style



# Scatter Plot – Experience vs. Average Salary
def experience_vs_salary():
    fig4 = go.Figure()
    df['months_experience'] = pd.to_numeric(df['months_experience'], errors='coerce')

    fig4 = px.scatter(df, x='months_experience', y='avg_salary',
                  title='Experience vs. Average Salary',
                  trendline='ols',  # adds regression line
                  color='Job function')
    fig4.update_layout(xaxis_title='Months of Experience', yaxis_title='Average Salary')
    graph4_html = pio.to_html(fig4, full_html=False)
    return graph4_html   # Donut style





# Bar Chart – Top 15 Highest Paying Job Titles
def top_15_highest_paying_job_titles():
    fig5 = go.Figure()
    title_salary = df.groupby('title')['avg_salary'].mean().nlargest(15).reset_index()

    fig5 = px.bar(title_salary, x='title', y='avg_salary',
              title='Top 15 Highest Paying Job Titles',
              color='avg_salary', text='avg_salary')
    fig5.update_layout(xaxis_tickangle=-45, yaxis_title='Average Salary')
    
    graph5_html = pio.to_html(fig5, full_html=False)
    return graph5_html   # Donut style

# Graph 4

                   # 1
# Box Plot – Experience Distribution by Seniority Level
fig1 = px.box(df, x='Seniority level', y='months_experience', points='all',
              title='Experience Distribution by Seniority Level',
              color='Seniority level')
fig1.update_layout(xaxis_tickangle=-45, yaxis_title='Months of Experience')



                      # 2
# Violin Plot – Experience Spread by Employment Type
fig2 = px.violin(df, x='Employment type', y='months_experience', box=True, points="all",
                 title='Experience Distribution by Employment Type',
                 color='Employment type')
fig2.update_layout(xaxis_tickangle=-45, yaxis_title='Months of Experience')


                         # 3

# Bar Chart – Average Experience Required per Seniority Level
seniority_exp = df.groupby('Seniority level')['months_experience'].mean().reset_index()
seniority_exp = seniority_exp.sort_values(by='months_experience', ascending=False)

fig3 = px.bar(seniority_exp, x='Seniority level', y='months_experience',
              title='Average Experience Required by Seniority Level',
              color='months_experience', text='months_experience')
fig3.update_layout(xaxis_tickangle=-45, yaxis_title='Average Months of Experience')


                            # 4

# Histogram – Overall Experience Distribution (Across All Roles)
fig4 = px.histogram(df, x='months_experience',
                    nbins=30,
                    title='Overall Experience Distribution in Job Posts',
                    color_discrete_sequence=['darkcyan'])
fig4.update_layout(xaxis_title='Months of Experience', yaxis_title='Job Count')

                           # graph 5
                           # 1
# Bar Chart – Most Common Education Requirements
def top_10_most_common_education_requirements():
    fig5 = go.Figure()
    # Top 10 Most Common Education Requirements
    edu_counts = df['education'].value_counts().nlargest(10).reset_index()
    edu_counts.columns = ['Education Level', 'Job Count']

    fig5 = px.bar(edu_counts, x='Education Level', y='Job Count',
                title='Top 10 Most Common Education Requirements',
                color='Job Count', text='Job Count')
    fig5.update_layout(xaxis_tickangle=-45)
    graph1_html = pio.to_html(fig5, full_html=False)
    return graph1_html   # Donut style


                           # 2
# Pie Chart – Distribution of Education Requirements
def distribution_of_education_requirements():
    fig = go.Figure()
    top_edu_pie = df['education'].value_counts().nlargest(7).reset_index()
    top_edu_pie.columns = ['Education Level', 'Count']

    fig = px.pie(top_edu_pie, names='Education Level', values='Count',
                title='Distribution of Education Requirements (Top 7)')
    graph2_html = pio.to_html(fig, full_html=False)
    return graph2_html 



                            # 3 
# Sunburst Chart – Education Level within Seniority Levels
def education_level_within_seniority_levels():
    fig3 = go.Figure()
    # Breakdown of Education Level within Seniority Levels
    edu_seniority = df.groupby(['Seniority level', 'education']).size().reset_index(name='Count')

    fig3 = px.sunburst(edu_seniority, path=['Seniority level', 'education'], values='Count',
                    title='Breakdown of Education Level within Seniority Levels')
    fig3.update_traces(textinfo="label+percent entry")
    graph3_html = pio.to_html(fig3, full_html=False)
    return graph3_html  

                            # 4
# Treemap – Education Level by Industry
def education_requirements_across_industries():
    fig4 = go.Figure()
    # Education Requirements Across Industries
    edu_industry = df.groupby(['Industries', 'education']).size().reset_index(name='Count')

    fig4 = px.treemap(edu_industry, path=['Industries', 'education'], values='Count',
                    title='Education Requirements Across Industries')
    fig4.update_traces(textinfo="label+percent entry")
    graph4_html = pio.to_html(fig4, full_html=False)
    return graph4_html

                            # 5
# Stacked Bar Chart – Education Requirements Across Employment Types
def education_requirements_by_employment_type():
    fig5 = go.Figure()
    # Education Requirements by Employment Type
    edu_employment = df.groupby(['Employment type', 'education']).size().reset_index(name='Count')
    edu_pivot = edu_employment.pivot(index='Employment type', columns='education', values='Count').fillna(0)

    for education in edu_pivot.columns:
        fig5.add_trace(go.Bar(
            x=edu_pivot.index,
            y=edu_pivot[education],
            name=education
        ))

    fig5.update_layout(barmode='stack',
                    title='Education Requirements by Employment Type',
                    xaxis_title='Employment Type',
                    yaxis_title='Job Count',
                    xaxis_tickangle=-45)
    fig5.update_traces(texttemplate='%{y}', textposition='inside')
    graph5_html = pio.to_html(fig5, full_html=False)
    return graph5_html
    





def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

def load_skills_cache():
    if os.path.exists(SKILLS_CACHE_FILE):
        with open(SKILLS_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_skills_cache(cache):
    with open(SKILLS_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def extract_skills(cv_text):
    cache_key = cv_text[:100]
    cache = load_skills_cache()

    if cache_key in cache:
        return cache[cache_key]

    prompt = f"""Extract only the technical and professional skills from this resume text:
    {cv_text}
    Return the skills in a comma-separated list. Focus on technical skills only."""
    
    response = model.generate_content(prompt)
    skills = [skill.strip().lower() for skill in response.text.split(",") if skill.strip()]
    
    cache[cache_key] = skills
    save_skills_cache(cache)
    
    return skills

def load_jobs(csv_path):
    df = pd.read_csv(csv_path)
    df.dropna(subset=["description"], inplace=True)
    
    tech_keywords = ['developer', 'engineer', 'programmer', 'software', 'data', 'python',
                    'java', 'web', 'full stack', 'backend', 'frontend', 'ai', 'ml']
    df['is_tech'] = df['title'].str.lower().str.contains('|'.join(tech_keywords))
    df = df[df['is_tech']]
    
    return df

def calculate_skill_importance(skills):
    if not skills:
        return {}
    
    technology_groups = {
        'frontend': ['html', 'css', 'javascript', 'bootstrap', 'nextjs'],
        'backend': ['python', 'java', 'laravel'],
        'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'plotly'],
        'ai_ml': ['machine learning', 'artificial intelligence', 'opencv'],
        'mobile': ['android', 'android development', 'flutter', 'dart'],
        'version_control': ['git'],
        'web_development': ['web', 'full stack', 'developer', 'engineer', 'programmer'],
        'general': ['software', 'data'],
        'digital_marketing': ['digital marketing', 'seo', 'sem'],
        'cloud_computing': ['aws', 'azure', 'google cloud', 'cloud computing'],
        'devops': ['docker', 'kubernetes', 'jenkins', 'ci/cd'],
        'cyber_security': ['cyber security', 'network security', 'penetration testing'],
        'blockchain': ['blockchain', 'cryptocurrency', 'ethereum'],
    }
    core_skills = {}
    
    try:
        skill_weights = {skill.lower(): core_skills.get(skill.lower(), 1.0) for skill in skills}
        
        for skill in skills:
            skill_lower = skill.lower()
            for group, group_skills in technology_groups.items():
                if skill_lower in [s.lower() for s in group_skills]:
                    related_skills = sum(1 for s in skills if s.lower() in [gs.lower() for gs in group_skills])
                    if related_skills > 1:
                        skill_weights[skill_lower] *= (1 + 0.1 * (related_skills - 1))
        
        return skill_weights
    except Exception as e:
        print(f"Error in calculate_skill_importance: {str(e)}")
        return {skill.lower(): 1.0 for skill in skills}

def recommend_jobs(skills, jobs_df):
    if not isinstance(skills, list) or not skills:
        return pd.DataFrame()
    
    if jobs_df.empty:
        return pd.DataFrame()
        
    try:
        skill_weights = calculate_skill_importance(skills)
        
        if 'description' not in jobs_df.columns:
            print("Error: 'description' column not found in jobs dataframe")
            return pd.DataFrame()
            
        jobs_df['description'] = jobs_df['description'].fillna('')
        job_texts = jobs_df["description"].str.lower().tolist()
        user_profile = " ".join(skills)
        
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=10000
            )
            vectors = vectorizer.fit_transform([user_profile] + job_texts)
            tfidf_similarity = cosine_similarity(vectors[0:1], vectors[1:])[0]
        except Exception as e:
            print(f"Error in TF-IDF calculation: {str(e)}")
            tfidf_similarity = np.zeros(len(job_texts))
        
        skill_matches = []
        for desc in job_texts:
            try:
                skill_score = 0
                matched_skills = set()
                
                for skill in skills:
                    skill_lower = skill.lower()
                    if skill_lower in desc.lower():
                        matched_skills.add(skill_lower)
                        skill_score += skill_weights.get(skill_lower, 1.0)
                
                coverage_ratio = len(matched_skills) / len(skills)
                skill_score = (skill_score / len(skills)) * (1 + coverage_ratio)
                skill_matches.append(skill_score)
            except Exception as e:
                print(f"Error in skill matching: {str(e)}")
                skill_matches.append(0)
        
        combined_scores = [0.65 * sm + 0.35 * ts for sm, ts in zip(skill_matches, tfidf_similarity)]
        
        result_df = jobs_df.copy()
        result_df['score'] = combined_scores
        result_df['matched_skills_count'] = [sum(1 for skill in skills if skill.lower() in desc.lower()) 
                                         for desc in job_texts]
        
        qualified_jobs = result_df[
            (result_df['score'] > 0.3) &
            (result_df['matched_skills_count'] >= len(skills) * 0.3)
        ]
        
        if qualified_jobs.empty:
            return pd.DataFrame()
        
        qualified_jobs['final_score'] = (qualified_jobs['score'] * 0.7 + 
                                     (qualified_jobs['matched_skills_count'] / len(skills)) * 0.3)
        
        required_columns = ["title", "company", "location", "description", "final_score"]
        for col in required_columns:
            if col not in qualified_jobs.columns:
                qualified_jobs[col] = ""
        
        return qualified_jobs.sort_values(
            by='final_score', 
            ascending=False
        )[required_columns]
        
    except Exception as e:
        print(f"Error in job recommendation: {str(e)}")
        return pd.DataFrame()

# Route for job recommendations
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        skills = []
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract skills from resume
                cv_text = extract_text_from_pdf(filepath)
                skills = extract_skills(cv_text)
                
                # Clean up uploaded file
                os.remove(filepath)
                
        elif 'skills' in request.form:
            # Handle manual skill entry
            skills_text = request.form['skills']
            skills = [s.strip().lower() for s in skills_text.split(',') if s.strip()]
            
        if skills:
            # Load jobs and get recommendations
            jobs_df = load_jobs('jobs.csv')
            matching_jobs = recommend_jobs(skills, jobs_df)
            
            return render_template('recommendations.html', 
                                skills=skills,
                                jobs=matching_jobs.to_dict('records'))
        else:
            flash('Please either upload a resume or enter skills')
            return redirect(request.url)
            
    return render_template('upload_resume.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)