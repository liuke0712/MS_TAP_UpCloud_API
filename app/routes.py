from app import app
from Upcloud_API import Upcloud_API
from flask import request, jsonify

api = Upcloud_API()

sample_start_server = [
    {
        "plan": "2xCPU-4GB",
        "zone": "uk-lon1",
        "hostname": "jwm-jason",
        "os": "01000000-0000-4000-8000-000030200200",
        "size": 80
    },
    {
        "plan": "2xCPU-4GB",
        "zone": "uk-lon1",
        "hostname": "jwm-jason",
        "os": "01000000-0000-4000-8000-000030200200"
    }
]


# 002305a9-5437-429a-b6cf-8afdd6558908

@app.route('/server', methods=['POST'])
def create_server():
    json_data = request.get_json()
    login_user = api.logon_user()
    new_servers = []
    for server in json_data:
        server = api.create_server(server['plan'], server['zone'], server['hostname'], server['os'], server['os_size'])
        new_servers.append(server.to_dict())
    return jsonify(new_servers)


@app.route('/server', methods=['GET'])
def get_all_server():
    details = api.server_list()
    return jsonify(details)


@app.route('/server/<uuid>', methods=['GET'])
def get_server(uuid):
    details = api.single_server(uuid)
    return jsonify(details)


# TODO: Proper response
@app.route('/server/<uuid>', methods=['DELETE'])
def delete_server(uuid):
    api.rm_server(uuid)
    return "Success response"
