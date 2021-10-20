import json

from app import app
from Upcloud_API import Upcloud_API
from flask import request, jsonify

api = Upcloud_API()


# 00c522f1-2e86-4d49-b5fe-5920cd855fff

@app.route('/server', methods=['POST'])
def create_server():
    json_data = request.get_json()
    print(json_data)
    server = json.loads(json_data)
    new_server = api.create_server(server['plan'], server['zone'], server['hostname'], server['os'],
                                   int(server['size']))
    new_server_dict = new_server.to_dict()
    return jsonify({
        "state": new_server_dict['state'],
        "hostname": new_server_dict['hostname'],
        "uuid": new_server_dict['uuid']
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


@app.route('/server/stop/<uuid>', methods=['DELETE'])
def stop_server(uuid):
    api.stop_server(uuid)
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
    return jsonify(api.planList)


@app.route('/template', methods=['GET'])
def get_templates():
    response = api.get_templates()
    return jsonify(response)
