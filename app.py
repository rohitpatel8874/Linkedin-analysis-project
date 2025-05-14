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
def industries_by_volume():
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



@app.route('/experience_seniority')
def experience_seniority():
    graph1_html = salary_ranges_by_job_function()
    graph2_html = salary_spread_by_seniority_level()
    graph3_html = salary()
    graph4_html = experience_vs_salary()

    return render_template('experience_seniority.html', graph1_html=graph1_html, graph2_html=graph2_html, graph3_html=graph3_html)



@app.route('/educatio_&_qualification')
def education_qualification():
    graph1_html = top_10_most_common_education_requirements()
    graph2_html = distribution_of_education_requirements()  
    graph3_html = education_level_within_seniority_levels()
    graph4_html = education_requirements_across_industries()
    graph5_html = education_requirements_by_employment_type()
    

  

    # Add more graphs as needed
    return render_template('education_qualification.html', graph1_html=graph1_html, graph2_html=graph2_html, graph3_html=graph3_html, graph4_html=graph4_html, graph5_html=graph5_html)




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

fig1 = px.bar(edu_counts, x='Education Level', y='Job Count',
              title='Top 10 Most Common Education Requirements',
              color='Job Count', text='Job Count')
fig1.update_layout(xaxis_tickangle=-45)


                           # 2
# Pie Chart – Distribution of Education Requirements
def distribution_of_education_requirements():
    fig2 = go.Figure()

    graph2_html = pio.to_html(fig2, full_html=False)
    return graph2_html   # Donut style
top_edu_pie = df['education'].value_counts().nlargest(7).reset_index()
top_edu_pie.columns = ['Education Level', 'Count']

fig2 = px.pie(top_edu_pie, names='Education Level', values='Count',
              title='Distribution of Education Requirements (Top 7)')



                            # 3 
# Sunburst Chart – Education Level within Seniority Levels
def education_level_within_seniority_levels():
    fig3 = go.Figure()
    # Breakdown of Education Level within Seniority Levels
edu_seniority = df.groupby(['Seniority level', 'education']).size().reset_index(name='Count')

fig3 = px.sunburst(edu_seniority, path=['Seniority level', 'education'], values='Count',
                   title='Breakdown of Education Level within Seniority Levels')

                            # 4
# Treemap – Education Level by Industry
def education_requirements_across_industries():
    fig4 = go.Figure()
    # Education Requirements Across Industries
edu_industry = df.groupby(['Industries', 'education']).size().reset_index(name='Count')

fig4 = px.treemap(edu_industry, path=['Industries', 'education'], values='Count',
                  title='Education Requirements Across Industries')

                            # 5
# Stacked Bar Chart – Education Requirements Across Employment Types
def education_requirements_by_employment_type():
    fig5 = go.Figure()
    # Education Requirements by Employment Type
edu_employment = df.groupby(['Employment type', 'education']).size().reset_index(name='Count')
edu_pivot = edu_employment.pivot(index='Employment type', columns='education', values='Count').fillna(0)

fig5 = go.Figure()

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





if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)