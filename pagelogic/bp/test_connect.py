from flask import jsonify, render_template, Blueprint, request

test_connect = Blueprint('test_connect', __name__)

@test_connect.route('/ping', methods=['GET'])
def pingpong():
    return jsonify(
        "pong"
    ), 200