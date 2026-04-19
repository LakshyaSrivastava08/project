from flask import Flask, render_template, request, redirect, url_for, jsonify
from kundli import calculate_kundli, get_doshas, get_coordinates, get_nakshatra_pada, get_yogas
from database import save_kundli, get_all_kundlis, get_kundli_by_id, search_kundlis

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    name  = request.form.get('name', '').strip()
    dob   = request.form.get('dob', '').strip()
    tob   = request.form.get('tob', '').strip()
    place = request.form.get('place', '').strip()

    if not all([name, dob, tob, place]):
        return render_template('index.html', error="All fields are required.")

    coords = get_coordinates(place)
    if coords is None:
        return render_template('index.html',
            error=f"Could not find '{place}'. Try a more specific city name.")

    lat, lon = coords
    planets = calculate_kundli(dob, tob, lat, lon)
    doshas  = get_doshas(planets)
    yogas   = get_yogas(planets)

    kundli_data = {
        'name':    name,
        'dob':     dob,
        'tob':     tob,
        'place':   place,
        'lat':     lat,
        'lon':     lon,
        'planets': planets,
        'doshas':  doshas,
        'yogas':   yogas,
    }

    return render_template('result.html', kundli=kundli_data)


@app.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    record_id = save_kundli(data)
    return jsonify({'success': True, 'id': record_id})


@app.route('/dashboard')
def dashboard():
    kundlis = get_all_kundlis()
    return render_template('dashboard.html', kundlis=kundlis)


@app.route('/kundli/<kundli_id>')
def view_kundli(kundli_id):
    kundli = get_kundli_by_id(kundli_id)
    if not kundli:
        return redirect(url_for('dashboard'))
    return render_template('view_kundli.html', kundli=kundli)


@app.route('/search')
def search():
    query     = request.args.get('q', '').strip()
    planet    = request.args.get('planet', '').strip()
    rashi     = request.args.get('rashi', '').strip()
    nakshatra = request.args.get('nakshatra', '').strip()
    results   = search_kundlis(query=query, planet=planet, rashi=rashi, nakshatra=nakshatra)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)