import base64
import json
import os
from collections import OrderedDict
from datetime import datetime

import paramiko
import requests
from cryptography import x509
import upcloud_api
# from upcloud_api.storage import BackupDeletionPolicy
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from upcloud_api import Server, Storage, login_user_block, UpCloudAPIError
import logs
import os
import requests
import json


apiURL = 'https://api.upcloud.com/1.3'
api_username = 'tapaug2021ee'
api_password = 'gr4D334uG2021'


class Upcloud_API:
    def __init__(self):
        self.mylogger = logs.Logs()
        self.manager = upcloud_api.CloudManager(api_username, api_password)
        self.manager.authenticate()
        if os.path.isfile('private_key.pem'):
            self.login_user = self.get_login_user()
        else:
            self.login_user = self.key_pair_create()
        self.planList = OrderedDict(
            [("1xCPU-2GB", 25), ("1xCPU-1GB", 50), ("2xCPU-4GB", 80), ("4xCPU-8GB", 160), ("6xCPU-16GB", 320),
             ("8xCPU-32GB", 640), ("12xCPU-48GB", 960),
             ("16xCPU-64GB", 1280), ("20xCPU-96GB", 1920), ("20xCPU-128G", 2048)])
        self.auth = base64.b64encode(f"{api_username}:{api_password}".encode())

    # get public key from the existing private key
    def get_login_user(self):
        with open('private_key.pem', 'rb') as file:
            private_key = serialization.load_pem_private_key(file.read(), None, default_backend())
            public_key = private_key.public_key().public_bytes(serialization.Encoding.OpenSSH,
                                                               serialization.PublicFormat.OpenSSH)
            public_key = public_key.decode(encoding='UTF-8')
        login_user = login_user_block(
            username='root',
            ssh_keys=[public_key],
            create_password=False
        )
        return login_user

    # create new key pair
    def key_pair_create(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        # generate the public key
        public_key = private_key.public_key().public_bytes(serialization.Encoding.OpenSSH,
                                                           serialization.PublicFormat.OpenSSH)
        public_key = public_key.decode(encoding='UTF-8')
        # get private key in PEM container format
        pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                                        encryption_algorithm=serialization.NoEncryption())
        login_user = login_user_block(
            username='root',
            ssh_keys=[public_key],
            create_password=False
        )
        self.mylogger.info_logger('A private_key.pem file is generated and stored for user: root.')
        with open('private_key.pem', 'wb') as f:
            f.write(pem)
        return login_user

    def get_zones(self):
        zones = self.manager.get_zones()['zones']['zone']
        zone_list = []
        for zone in zones:
            zone_list.append(zone['id'])
        return zone_list

    def get_templates(self):
        templates = self.manager.get_templates()
        return templates

    # new server creation
    def create_server(self, plan, zone, hostname, os, os_size, title):
        try:
            server = Server(
                plan=plan,
                hostname=hostname,
                zone=zone,  # All available zones with ids can be retrieved by using manager.get_zones()
                storage_devices=[
                    Storage(os=os, size=os_size),
                ],
                title=title,
                login_user=self.login_user  # user and ssh-keys
            )
            server = self.manager.create_server(server)
            server_uuid = server.to_dict()['uuid']
            server_name = server.to_dict()['hostname']
            self.mylogger.info_logger(server_name + ' with uuid:' + server_uuid + ' was created.')
            return server.to_dict()
        except UpCloudAPIError as e:
            return {'api_error': str(e)}

    # get current server status
    def server_status(self, uuid):
        server_status = self.manager.get_server(uuid).to_dict()['state']
        server_name = self.manager.get_server(uuid).to_dict()['hostname']
        return server_status

    # get all server list
    def server_list(self):
        servers = self.manager.get_servers()
        server_list = []
        for server in servers:
            server_list.append(server.to_dict())
        return server_list

    # get one server details
    def single_server(self, uuid):
        try:
            server = self.manager.get_server(uuid).to_dict()
            return server
        except UpCloudAPIError as e:
            return {'api_error': str(e)}

    # check the performance of linux server
    def perform_statistic_linux(self, uuid):
        try:
            server = self.manager.get_server(uuid).to_dict()
            ip_addr = server['ip_addresses']
            perform_info = []
            for ip in ip_addr:
                if ip['access'] == 'public' and ip['family'] == 'IPv4':
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip['address'], port=22, username='root', key_filename='private_key.pem')
                    command = 'export TERM=xterm && top -n 1 -b'
                    # command = 'export TERM=xterm && mpstat'
                    stdin, stdout, stderr = ssh.exec_command(command)
                    lines = stdout.readlines()[0:5]
                    lines.insert(0, '--------------------------------Resource Usage-----------------------------------')
                    err_lines = stderr.readlines()
                    command = 'export TERM=xterm && df'
                    stdin, stdout, stderr = ssh.exec_command(command)
                    lines.append('----------------------------------Disk Filesystem--------------------------------')
                    lines.extend(stdout)
                    err_lines.extend(stderr)
                    break
            if err_lines:
                return err_lines
            else:
                return lines
        except Exception as e:
            raise e

    def server_stop(self, uuid):
        server = self.manager.get_server(uuid)
        if server.to_dict()['state'] != 'stopped':
            server.shutdown(hard=True)
        self.mylogger.info_logger('Server: ' + uuid + ' has been stopped.')

    def server_start(self,uuid):
        server = self.manager.get_server(uuid)
        server.start()
        self.mylogger.info_logger('Server: ' + uuid + ' has been started.')

    def server_modify(self,uuid,plan):
        response = requests.put(f'{apiURL}/server/{uuid}',
                                   headers={"Authorization": "Basic " + self.auth.decode(),"Content-Type": "application/json"},
                                data=json.dumps({
                                                  "server" : {
                                                    "plan" : plan
                                                  }
                                                }))
        self.mylogger.info_logger('The plan of Server: '+uuid+' has been changed to '+str(plan) +'.')
        return response.json()

    # delete a vm based on the uuid
    def rm_server(self, uuid, storages=1, backups='delete'):
        response = requests.delete(f'{apiURL}/server/{uuid}?storages={storages}&backups={backups}',
                                   headers={"Authorization": "Basic " + self.auth.decode(),"Content-Type": "application/json"})
        return response.text

    # check log of a specific server
    def check_log(self, uuid):
        with open("app.log", 'r') as file:
            lines = file.readlines()
            server_log = []
            for line in lines:
                if uuid in line:
                    server_log.append(line)
        return server_log


if __name__ == '__main__':
    ins = Upcloud_API()
    # ins.server_start('00ffd05c-8f9c-4f5f-95d5-e8eae992c3d8')
    # print(ins.server_stop('00ffd05c-8f9c-4f5f-95d5-e8eae992c3d8'))
    # print(ins.server_modify('00ffd05c-8f9c-4f5f-95d5-e8eae992c3d8','2xCPU-4GB'))
    # ins.get_login_user()
    # print(ins.check_log('00c9f070-5cee-482f-97a8-24fb848d948d'))
    # print(ins.server_list())
    # print(ins.get_zones())
    # print(ins.get_templates())
    # print(ins.single_server('00effc4b-47f5-4394-a357-0750c810b096'))
    # print(ins.access_console('00effc4b-47f5-4394-a357-0750c810b096'))
    # print(ins.server_list())
    print(ins.server_status('00ffd05c-8f9c-4f5f-95d5-e8eae992c3d8'))
    ins.server_start('00ffd05c-8f9c-4f5f-95d5-e8eae992c3d8')
    # print(ins.perform_statistic_linux('0028ea76-cb26-43e7-9862-d89d164e2a6a'))
    # print(ins.create_server("1xCPU-1GB","uk-lon1","maggie.modify-test.com", "01000000-0000-4000-8000-000030200200", "10",'modify-test'))
    # print(ins.server_stop('00c9f070-5cee-482f-97a8-24fb848d948d'))
    # print(ins.rm_server("00c9f070-5cee-482f-97a8-24fb848d948d"))
# get server details
# print(self.manager.get_server("0021e1da-be14-4440-8de6-f04b0650926b").to_dict())
# get server states
# print(manager.get_server("0021e1da-be14-4440-8de6-f04b0650926b").to_dict()['state'])
# delete vms (stop first)
