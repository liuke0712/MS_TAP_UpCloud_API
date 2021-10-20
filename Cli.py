from __future__ import print_function, unicode_literals

import re
import time

import requests
from PyInquirer import style_from_dict, Token, prompt, Separator
import json
from PyInquirer import prompt, Separator
from Upcloud_API import Upcloud_API
from shell import Shell

# from requests import requests
style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

baseURL = 'http://127.0.0.1:5000'


class Cli:
    def __init__(self):
        self.manager = Upcloud_API()

    def ask_action(self):
        directions_prompt = {
            'type': 'list',
            'name': 'action',
            'message': 'Which action would you like to perform?',
            'choices': ['CreateVM', 'CheckVmStatus', 'DeleteVm', 'VmConsole', 'PerformanceStat', 'VmEvents']
        }
        answers = prompt(directions_prompt)
        return answers['action']

    def ask_zone(self):
        response = requests.get(baseURL+'/zone')
        zones = response.json()
        directions_prompt = {
            'type': 'list',
            'name': 'zone',
            'message': 'Which zone would you like to choose?',
            'choices': zones
        }
        answers = prompt(directions_prompt)
        return answers['zone']

    def ask_plan(self):
        response = requests.get(baseURL + '/plan')
        plans = response.json()
        directions_prompt = {
            'type': 'list',
            'name': 'plan',
            'message': 'Which plan would you like to choose?',
            'choices': plans
        }
        answers = prompt(directions_prompt)
        return answers['plan']

    def ask_os(self):
        directions_prompt = {
            'type': 'list',
            'name': 'os',
            'message': 'Which os would you like to choose?',
            'choices': self.get_os_dict().keys()
        }
        answers = prompt(directions_prompt)
        return answers['os']

    def get_os_storage(self):
        while True:
            try:
                os_st = int(input("enter your disk storage (need to be between 10 GB AND 4096 GB) "))
                if (os_st >= 10) and (os_st <= 4096):
                    break
            except ValueError:
                print("This is an unaccepted response, enter a valid value")
                continue
            else:
                continue
        return os_st

    # TODO better to use while loop than recursion!

    def request_progress(self):
        directions_prompt = {
            'type': 'list',
            'name': 'request_prog',
            'message': '  would you like to monitor the progress of your request?',
            'choices': ['YES', 'NO']
        }
        answers = prompt(directions_prompt)
        return answers['request_prog']

  def get_vm_details(self):
        vmDetails=[]
        zone = self.ask_zone()
        plan = self.ask_plan()
        os_name=self.ask_os()
        os = self.get_os_dict()[os_name]
        os_size = self.get_os_storage()
        VmNumber = int(self.get_input('how many VMs you would like to create with these options:\n' +'zone :' +zone +'\n'+'plan: '+plan +'\n'+'os: '+os_name +'\n' ))

        count=1
        for i in range(0, VmNumber):
            vmName = self.get_input('Please pick a name for VM '+ str(count) +'/' +str(VmNumber))
            vmDetails.append([vmName, zone, os, plan,os_size])
            count=count+1
        return vmDetails

    def get_os_dict(self):
        response = requests.get(baseURL+'/template')
        mylist = response.json()
        all_keys = list(set().union(*(d.keys() for d in mylist)))
        all_values = list(set().union(*(d.values() for d in mylist)))
        d = dict(zip(all_keys, all_values))
        return d

    def get_all_servers_list(self):
        hostname_list = []
        response = requests.get(baseURL+'/server')
        for i in response.json():
            hostname_list.append(i['hostname'] + ":" + i['uuid'])

        return hostname_list

    #  def get_delete_choice(self):
    #      question = {
    #          'type': 'list',
    #          'name': 'delete_choice',
    #          'message': '  please pick a choice for the next step?',
    #          'choices': ['choice from existing VMs list','enter a hostname','enter VM UUID ']
    #      }
    #      answers = prompt(question)
    #      return answers['delete_choice']
    #
    #
    # def pick_vm(self):
    #     question1 = {
    #         'type': 'list',
    #         'name': 'vm_choice',
    #         'message': ' please pick one of the bellow VM list ',
    #         'choices': self.get_all_servers_list()
    #     }
    #     answer1 = prompt(question1)
    #     return answer1['vm_choice']

    def pick_vm(self):

        directions_prompt = {
            'type': 'list',
            'name': 'vm',
            'message': '  please pick one of the bellow VM list',
            'choices': self.get_all_servers_list()
        }
        answers = prompt(directions_prompt)
        return answers['vm']

    def get_delete_choice(self):
        directions_prompt = {
            'type': 'list',
            'name': 'delete_option',
            'message': 'please pick a choice for the next step?',
            'choices': ['choice from existing VMs list', 'enter VM UUID']
        }
        answers = prompt(directions_prompt)
        if answers['delete_option'] == "choice from existing VMs list":
            return self.pick_vm().split(':')[1]

        elif answers['delete_option'] == "enter VM UUID":
            return self.get_input('What\'s your VM uuid')

    def get_checkStatus_choice(self):
        directions_prompt = {
            'type': 'list',
            'name': 'status_option',
            'message': 'please pick a choice for the next step?',
            'choices': ['check all VMs status', 'get more details about a specific VM']
        }
        answers = prompt(directions_prompt)
        if answers['status_option'] == "check all VMs status":
            self.check_all_vms_status()

        elif answers['status_option'] == "get more details about a specific VM":
            uuid = self.get_delete_choice()
            response = requests.get(baseURL+'/server/'+uuid)
            json_data = json.dumps(response.json(), indent=4)
            print(json_data)

    def check_all_vms_status(self):
        response = requests.get(baseURL+'/server')
        for server in response.json():
            print(server['hostname'] + ":" + server['uuid'] + ":" + server['state'])

    def after_create_info(self, uuid):
        response = requests.get(baseURL + '/server/' + uuid)
        server_details = response.json()
        for i in server_details['ip_addresses']:
            if i['access'] == 'public' and i['family'] == 'IPv4':
                ip = i['address']
                break
        dict = {
            'hostname': server_details['hostname'],
            'uuid': uuid,
            'ip': ip
        }
        print(json.dumps(dict, indent=4))

    def performe_CreateVM(self):
        vmDetails = self.get_vm_details()
        monitor = self.request_progress()
        vm_list = self.requestSummary(vmDetails, monitor)
        new_uuid_list = []
        for count, vm in enumerate(vm_list):
            print("Start Creating server: " + vm['hostname'] + " order in the queue: " + str(count + 1) + "/" + str(
                len(vm_list)))
            response = requests.post(baseURL + '/server', json=json.dumps(vm))
            new_uuid_list.append(response.json()['uuid'])
        count = 1
        if monitor == 'YES':
            while new_uuid_list:
                for uuid in new_uuid_list:
                    status = self.get_server_status(uuid)
                    if status != 'maintenance':
                        print("Server " + str(count) + "/" + str(len(vm_list)) + ": " + status)
                        self.after_create_info(uuid)
                        count += 1
                        new_uuid_list.remove(uuid)

    def performe_deleteVm(self):
        uuid = self.get_delete_choice()
        monitor = self.request_progress()
        requests.delete(baseURL + '/server/stop/' + uuid)
        if monitor == 'YES':
            while True:
                status = self.get_server_status(uuid)
                if status == 'stopped':
                    break
            print("Server status: stopped")
        response = requests.delete(baseURL + '/server/' + uuid)
        if response.text == 'SUCCESS':
            print("Server status (uuid: " + uuid + "): destroyed.")
        else:
            print("Failed to destroy server (uuid: " + uuid + "): response.text")

    def performe_CheckVmStatus(self):
        self.get_checkStatus_choice()

    def perfome_VmConsole(self):
        uuid = self.get_delete_choice()
        response = requests.get(baseURL+'/server/'+uuid)
        server_details = response.json()
        for i in server_details['ip_addresses']:
            if i['access']=='public' and i['family']== 'IPv4':
                ip = i['address']
        print("Connecting to the VM...")
        sh = Shell(ip, 'root', 'private_key_save.pem')
        # Print initial command line
        while True:
            if sh.channel.recv_ready():
                output = sh.channel.recv(1024)
                new_output = str(output.decode('utf-8'))
                output_list = new_output.split('\n')
                output_list.pop(0)
                for count, line in enumerate(output_list):
                    line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r', '')
                    if count == len(output_list) - 1:
                        print(line, end='')
                    else:
                        print(line)
            else:
                time.sleep(0.5)
                if not (sh.channel.recv_ready()):
                    break
        while True:
            try:
                command = input()
                if command == 'exit':
                    break
                stdout = sh.execute(command)
                for count, line in enumerate(stdout):
                    line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r', '')
                    if count == len(stdout) - 1:
                        print(line, end='')
                    else:
                        print(line)
            except KeyboardInterrupt:
                break

        # add the manager component

    def perfome_checkPerformance(self):
        uuid = self.get_delete_choice()
        response = requests.get(baseURL+'/server/perf/'+uuid)
        perf_details = response.json()
        for line in perf_details:
            print(line.strip())

    def action(self):
        print('#############WELCOME#############')
        action = self.ask_action()
        while True:
            if (action == 'CreateVM'):
                self.performe_CreateVM()
            elif (action == 'CheckVmStatus'):
                self.performe_CheckVmStatus()
            elif (action == 'DeleteVm'):
                self.performe_deleteVm()
                print(self.get_all_servers_list())
            elif (action == 'VmConsole'):
                self.perfome_VmConsole()
            elif (action == 'PerformanceStat'):
                self.perfome_checkPerformance()
            elif (action == 'VmEvents'):
                print('VmEvents')
            elif (action == 'Exit'):
                print('########EXITING PROGRAM THANKS##########')
                break
            action = self.ask_action()

    def requestSummary(self, vmDetails, monitor):
        print("..")
        summary = []
        for i in vmDetails:
            thisdict = {
                "hostname": i[0],
                "zone": i[1],
                "plan": i[3],
                "os": i[2],
                "size": i[4]
            }

            summary.append(thisdict)
        print("=======this is your request choices summary======== \n\n\n")
        print("VMs DETAILS \n\n\n")
        print(summary)
        print("\n\n\n")
        print("MONITORING CHOICE: ", monitor, "\n\n\n")
        return summary

    def get_server_status(self, uuid):
        response = requests.get(baseURL + '/server/status/' + uuid)
        return response.text

    #
    #
    # def vm_name_input(self):
    #     questions = [
    #         {
    #             'type': 'input',
    #             'name': 'vmName',
    #             'message': 'What\'s your VM name',
    #         }
    #     ]
    #     answers = prompt(questions)
    #     return answers['vmName']
    #
    # def vm_uuid_input(self):
    #     questions = [
    #         {
    #             'type': 'input',
    #             'name': 'vmName',
    #             'message': 'What\'s your VM uuid',
    #         }
    #     ]
    #     answers = prompt(questions)
    #     return answers['vmName']
    #
    #
    # def vm_number_input(self):
    #     questions = [
    #         {
    #             'type': 'input',
    #             'name': 'vmNumber',
    #             'message': 'how many VMs you would like to create',
    #         }
    #     ]
    #     answers = prompt(questions)
    #     return int(answers['vmNumber'])

    def get_input(self, msg):
        questions = [
            {
                'type': 'input',
                'name': 'x',
                'message': msg,
            }
        ]
        answers = prompt(questions)
        return answers['x']

    # def encounter2b():
    #     prompt({
    #         'type': 'list',
    #         'name': 'weapon',
    #         'message': 'Pick one',
    #         'choices': [
    #             'Use the stick',
    #             'Grab a large rock',
    #             'Try and make a run for it',
    #             'Attack the wolf unarmed'
    #         ]
    #     },  style=style)
    #     print('The wolf mauls you. You die. The end.')

    # if __name__ == '__main__':
    #     main()


ins = Cli()
ins.perfome_VmConsole()
