import sys
import requests
from datetime import datetime
from flask import Flask, redirect, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from weather_api import API_KEY

app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)
url = 'https://api.openweathermap.org/data/2.5/weather'

try:
    api_key = API_KEY
except KeyError:
    sys.exit("Can't find api_key!")


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


db.drop_all()
db.create_all()


@app.route('/')
def index():
    query = City.query.all()
    cities_list = [(city.name, city.id) for city in query]
    cities_info = []
    for city_info in cities_list:
        city_name, city_id = city_info[0], str(city_info[1])
        r = requests.get(url, params={'q': city_name, 'appid': api_key, 'units': 'metric'})

        if r.status_code == 200:
            data = r.json()

            city = data.get('name').upper()
            degrees = round(int(data.get('main').get('temp')))
            state = data.get('weather')[0].get('main')
            offset = int(data.get('timezone'))
            ts = int(data.get('dt')) + offset
            local_hour = int(datetime.utcfromtimestamp(ts).strftime('%H'))

            # day
            if 11 <= int(local_hour) <= 16:
                day_state = 'day'
            # morning
            elif 6 <= int(local_hour) <= 10:
                day_state = 'evening-morning'
            # evening
            elif 17 <= int(local_hour) <= 21:
                day_state = 'evening-morning'
            # night
            else:
                day_state = 'night'

            weather_info = {'city': city,
                            'city_id': city_id,
                            'degrees': degrees,
                            'state': state,
                            'day_state': day_state}

            if all(weather_info.values()):
                cities_info.append(weather_info)

        else:
            flash("The city doesn't exist!")

    if cities_info:
        return render_template('index.html', cities=cities_info)
    else:
        return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add_city():
    city_name = request.form['city_name']
    exists = db.session.query(City.id).filter_by(name=city_name).first() is not None
    if exists:
        flash('The city has already been added to the list!')
    else:
        db.session.add(City(name=city_name))
        db.session.commit()
    return redirect('/')


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
