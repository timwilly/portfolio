import json
from app.models import BusinessMontreal
from app.api import bp
from app.api.forms import SearchForm
from app.tasks import read_csv
from datetime import datetime, date, time
from flask import render_template, redirect, url_for, flash, request, jsonify
from itertools import islice
from json import JSONEncoder
from sqlalchemy import asc, func


@bp.route('/map', methods=['GET', 'POST'])
def map():
    form = SearchForm(request.form)
    result_name = request.args.get('result_name')
    if form.validate_on_submit():
        result = BusinessMontreal.query.filter_by(name=form.search.data) \
                                 .first()
        if result is None:
            flash('Data not found!')
            return redirect(url_for('api.map'))
        else:
            flash('Your search is successful!')
            return redirect(url_for('api.map', result_name=result.name))
    result = BusinessMontreal.query.filter_by(name=result_name).order_by \
                              (BusinessMontreal.date_statut.asc())
    latest_business_update = BusinessMontreal.query.with_entities(
        func.max(BusinessMontreal.date_last_update)
    ).scalar()
    business_montreal_before_data_update = read_csv(
        'before_update_data_business_montreal')
    #_, _, business_montreal_data_update=import_csv_to_database()
    #print(business_montreal_data_update)
    return render_template('api/map.html', title="Map", form=form,
                           result=result,
                           latest_business_update=latest_business_update,
                           business_montreal_before_data_update=
                           business_montreal_before_data_update)


@bp.route('/data_update', methods=['GET'])
def data_update():

    return render_template('api/data_update.html', title="Data update")


@bp.route('/search', methods=['GET'])
def search():
    term = request.args.get('term', '').strip()

    if len(term) < 2:
        return jsonify([])

    results = BusinessMontreal.query \
        .with_entities(BusinessMontreal.name) \
        .filter(BusinessMontreal.name.ilike(f'{term}%')) \
        .distinct() \
        .order_by(BusinessMontreal.name.asc()) \
        .limit(10) \
        .all()

    return jsonify([name for name, in results])


@bp.route('/food_business', methods=["GET", "POST"])
def get_food_business_json():
    food_business = request.args.get("business")
    result = BusinessMontreal.query.filter_by(name=food_business).all()
    result_json = []
    for r in result:
        r.date_statut = datetime_handler(r.date_statut)
        result_json.append(r.as_dict())
        
    return jsonify(json.loads(json.dumps({'Business': result_json}, ensure_ascii=False).encode('utf8')))


# Convertit un objet datetime en string
def datetime_handler(obj):
    if isinstance(obj, (datetime, date, time)):
        return str(obj)
    
def read_file(read_file_name):
    try:
        # Ouvre le fichier en mode lecture
        with open("app/static/data/{}.txt".format(read_file_name), "r") as file:
            # Lit les données du fichier
            data = file.read()
            return data
    except Exception as e:
        # En cas d'erreur, affiche le message d'erreur
        print(e)
"""
src = ['foo', 'bar', 'foobar', 'bar', 'barfoo']
tree = create(src)
print_tree(tree)

for word in src:
    print('search {0}, result: {1}'.format(word, search(tree, word)))

@bp.route('/process', methods=['POST'])
def process():
    search = request.form['search']
    if search:
        return jsonify({'name':search})
    return jsonify({'error': 'missing data..'})

@bp.route('/business', methods=["GET", "POST"])
def get_business_json():
    name = request.args.get("arrondissement")
  
    if not installations:
        return jsonify({'Erreur': 'Aucune installation trouvé'})

    return jsonify({'Installations': installations})
    """
