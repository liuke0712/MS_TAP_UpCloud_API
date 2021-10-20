import upcloud_api
from upcloud_api import Server, Storage, Tag, login_user_block
import paramiko
# from upcloud_api.storage import BackupDeletionPolicy
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import json

class Upcloud_API:
    def __init__(self):
        self.manager = upcloud_api.CloudManager('tapaug2021ee', 'gr4D334uG2021')
        self.manager.authenticate()
        self.tag = Tag('JWM_TEAM')
        self.plan1 = "1xCPU-2GB"
        self.plan2 = "1xCPU-1GB"
        self.plan3 = "2xCPU-4GB"
        self.plan4 = "4xCPU-8GB"
        self.plan5 = "6xCPU-16GB"
        self.plan6 = "8xCPU-32GB"
        self.plan7 = "12xCPU-48GB"
        self.plan8 = "16xCPU-64GB"
        self.plan9 = "20xCPU-96GB"
        self.plan10 = "20xCPU-128G"
        self.planList=[ "1xCPU-2GB","1xCPU-1GB","2xCPU-4GB","4xCPU-8GB","6xCPU-16GB","8xCPU-32GB","12xCPU-48GB","16xCPU-64GB","20xCPU-96GB","20xCPU-128G"]
        # self.logs


    # login user
    def key_pair_login(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        #generate the public key
        public_key = private_key.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
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
        with open('private_key.pem','wb') as f:
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


    #new server creation
    def create_server(self, plan, zone, hostname, os, os_size, login_user):
        server = Server(
            plan=plan,
            hostname=hostname,
            zone=zone,  # All available zones with ids can be retrieved by using manager.get_zones()
            storage_devices=[
                Storage(os=os, size=os_size),
            ],
            login_user=login_user  # user and ssh-keys
        )
        self.manager.create_server(server)
        self.server_status(server)
        return server


    #get current server status
    def server_status(self,uuid):
        server_status = self.manager.get_server(uuid).to_dict()['state']
        server_name = self.manager.get_server(uuid).to_dict()['hostname']
        return "Current status of server: "+server_name+ ":"+uuid+"  is "+server_status
    def server_name(self,uuid):
        return self.manager.get_server(uuid).to_dict()['hostname']
    def server_ip(self, uuid):
        for i in self.manager.get_server(uuid).to_dict()['ip_addresses']:
            if i['access']=='public' and i['family']== 'IPv4':
                return i['address']


    #get all server list
    def server_list(self):
        servers = self.manager.get_servers()
        server_list=[]
        for server in servers:
            server_list.append(server.to_dict())
        return server_list


    #get one server details
    def single_server(self,uuid):
        server = self.manager.get_server(uuid).to_dict()
        return server


    def access_console(self,uuid):
        try:
            server = self.manager.get_server(uuid).to_dict()
            ip_addr = server['ip_addresses']
            for ip in ip_addr:
                if ip['access'] =='public' and ip['family'] == 'IPv4':
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip['address'],port=22,username='test_user',key_filename='.\private_key.pem')
                    command = 'uname -r '
                    stdin, stdout, stderr = ssh.exec_command(command)
                    lines = stdout.readlines()
                    print(lines)
                    break
        except Exception as e:
            raise e


    # check the performance of linux server
    def perform_statistic_linux(self,uuid):
        try:
            server = self.manager.get_server(uuid).to_dict()
            ip_addr = server['ip_addresses']
            perform_info = []
            for ip in ip_addr:
                if ip['access'] =='public' and ip['family'] == 'IPv4':
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip['address'],port=22,username='root',key_filename='private_key.pem')
                    command = 'export TERM=xterm && top -n 1 -b'
                    # command = 'export TERM=xterm && mpstat'
                    stdin, stdout, stderr = ssh.exec_command(command)
                    lines = stdout.readlines()
                    err_lines = stderr.readlines()
                    break
            if err_lines:
                return err_lines
            else:
                return lines
        except Exception as e:
            raise e


    #delete a vm based on the uuid
    def rm_server(self,uuid):
        server = self.manager.get_server(uuid)
        server.shutdown(hard=True)
        while self.manager.get_server(uuid).to_dict()["state"] != "stopped":
            pass
        self.manager.delete_server(uuid)
        return "Selected server deleted."


if __name__ == '__main__':
    ins = Upcloud_API()
    # login_user = ins.key_pair_login()
    # print(ins.server_list())
    # print(ins.get_zones())
    # print(ins.get_templates())
    # print(ins.single_server('00effc4b-47f5-4394-a357-0750c810b096'))
    # print(ins.access_console('00effc4b-47f5-4394-a357-0750c810b096'))
    # print(ins.server_list())
    print(ins.server_status('00e3d773-a32e-4cea-9653-1df3543710fa'))
    # print(ins.perform_statistic_linux('00e3d773-a32e-4cea-9653-1df3543710fa'))
    # print(ins.create_server("2xCPU-4GB","uk-lon1","maggie.win.com", "01000000-0000-4000-8000-000030200200", "10",login_user))
    # ins.rm_server("0021e1da-be14-4440-8de6-f04b0650926b")