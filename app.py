from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_bcrypt import bcrypt
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import folium


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

# Load the dataset
df = pd.read_csv("Analysis/linkedin-company-information.csv")

# Group by country and count the number of companies
country_counts = df['Country'].value_counts().reset_index()
country_counts.columns = ['Country', 'CompanyCount']

# Load a world shapefile for mapping
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Merge the country data with the world shapefile
world = world.merge(country_counts, how='left', left_on='name', right_on='Country')

# Create a folium map
m = folium.Map(location=[0, 0], zoom_start=2)

# Add a choropleth layer
folium.Choropleth(
    geo_data=world,
    name='choropleth',
    data=world,
    columns=['name', 'CompanyCount'],
    key_on='feature.properties.name',
    fill_color='YlGnBu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of Companies'
).add_to(m)

# Save the map to an HTML file
m.save('static/img/company_distribution_heatmap.html')

# Plot the bar chart
plt.figure(figsize=(10, 6))
country_counts.set_index('Country')['CompanyCount'].plot(kind='bar', color='skyblue')
plt.title('Top 10 Countries with the Most Companies')
plt.xlabel('Country')
plt.ylabel('Number of Companies')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('static/img/top_10_countries_bar_chart.png')
plt.show()


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)