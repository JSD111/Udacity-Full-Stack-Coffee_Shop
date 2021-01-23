import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

#------------------------------------------------------
## ROUTES
#------------------------------------------------------
@app.route('/drinks', methods=['GET'])
def get_drinks():

    all_drinks = Drink.query.all()
    formatted_drinks = [d.short() for d in all_drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    }), 200
 
#------------------------------------------------------
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):

    all_drinks = Drink.query.all()
    formatted_drinks = [d.long() for d in all_drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    }), 200

#------------------------------------------------------
@app.route('/drinks', methods=['POST'], endpoint='post_drink')
@requires_auth('post:drinks')
def drinks(payload):

    body = request.get_json()

    try:
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(422)
#------------------------------------------------------
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):

    body = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    try:
        title = body.get('title', None)
        recipe = body.get('recipe', None)

        if title:
            drink.title = title
        if recipe:
            drink.recipe = json.dumps(recipe)

        drink.update()
    except Exception:
        abort(400)

    return jsonify({
        'success': True, 
        'drinks': [drink.long()]
    }), 200
    
#------------------------------------------------------
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):

    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except Exception:
        abort(400)

    return jsonify({
        'success': True, 
        'delete': id
    }), 200

##-----------------------------------------------
## Error Handling
##-----------------------------------------------
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False, 
        "error": 500,
        "message": "internal server error"
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
