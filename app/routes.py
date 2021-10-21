import json

from app import app
from Upcloud_API import Upcloud_API
from flask import request, jsonify

api = Upcloud_API()


@app.route('/server', methods=['POST'])
def create_server():
    json_data = request.get_json()
    print(json_data)
    server = json.loads(json_data)
    new_server = api.create_server(server['plan'], server['zone'], server['hostname'], server['os'],
                                   int(server['size']), server['title'])
    if 'api_error' in new_server:
        return new_server
    return jsonify({
        "state": new_server['state'],
        "title": new_server['title'],
        "hostname": new_server['hostname'],
        "uuid": new_server['uuid']
    })


@app.route('/server', methods=['GET'])
def get_all_server():
    details = api.server_list()
    return jsonify(details)


@app.route('/server/<uuid>', methods=['GET'])
def get_server_uuid(uuid):
    details = api.single_server(uuid)
    return jsonify(details)


@app.route('/server/status/<uuid>', methods=['GET'])
def get_server_status(uuid):
    status = api.server_status(uuid)
    return status


@app.route('/server/perf/<uuid>', methods=['GET'])
def get_server_perf(uuid):
    response = api.perform_statistic_linux(uuid)
    print(response)
    return jsonify(response)


@app.route('/server/<uuid>', methods=['PUT'])
def modify_server(uuid):
    response = api.server_modify(uuid)
    return jsonify(response.json())


@app.route('/server/start/<uuid>', methods=['POST'])
def start_server(uuid):
    api.server_start(uuid)
    return "Staring server"


@app.route('/server/stop/<uuid>', methods=['POST'])
def stop_server(uuid):
    api.server_stop(uuid)
    return "Stopping server"


# TODO: Proper response
@app.route('/server/<uuid>', methods=['DELETE'])
def delete_server(uuid):
    response = api.rm_server(uuid)
    return response


@app.route('/zone', methods=['GET'])
def get_zones():
    response = api.get_zones()
    return jsonify(response)


@app.route('/plan', methods=['GET'])
def get_plans():
    print(api.planList)
    return jsonify(api.planList)


@app.route('/template', methods=['GET'])
def get_templates():
    response = api.get_templates()
    return jsonify(response)


@app.route('/logs/<uuid>', methods=['GET'])
def get_log(uuid):
    response = api.check_log(uuid)
    return jsonify(response)
