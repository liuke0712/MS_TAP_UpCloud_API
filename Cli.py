from __future__ import print_function, unicode_literals
import json
import re
import threading
import time
import requests
from PyInquirer import style_from_dict, Token, prompt, Separator
from Upcloud_API import Upcloud_API
from shell import Shell
import logs

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
        self.mylogger = logs.Logs()

    # ask the user to choose an action from the action list
    def ask_action(self):
        directions_prompt = {
            'type': 'list',
            'name': 'action',
            'message': 'Which action would you like to perform?',
            'choices': ['Create VM', 'Check VM Status', 'Delete VM', 'Access VM Console', 'Check VM Performance', 'Check VM Events', 'EXIT']
        }
        answers = prompt(directions_prompt)
        return answers['action']

    # ask the user the choose a zone when creating a vm
    def ask_zone(self):
        response = requests.get(baseURL + '/zone')
        zones = response.json()
        directions_prompt = {
            'type': 'list',
            'name': 'zone',
            'message': 'Which zone would you like to choose?',
            'choices': zones
        }
        answers = prompt(directions_prompt)
        return answers['zone']

    # ask the user the choose a plan when creating a vm
    def ask_plan(self):
        response = requests.get(baseURL + '/plan')
        plans = response.json()
        directions_prompt = {
            'type': 'list',
            'name': 'plan',
            'message': 'Which plan would you like to choose?',
            'choices': plans.keys()
        }
        answers = prompt(directions_prompt)
        return answers['plan'], plans[answers['plan']]

    # ask the user the choose an os when creating a vm
    def ask_os(self):
        directions_prompt = {
            'type': 'list',
            'name': 'os',
            'message': 'Which os would you like to choose?',
            'choices': self.get_os_dict().keys()
        }
        answers = prompt(directions_prompt)
        return answers['os']

    # ask the user the choose  to change the os size when creating a vm
    def ask_os_size(self, default_size):
        directions_prompt = {
            'type': 'list',
            'name': 'os_size',
            'message': 'Would you like to change the default storage size(' + str(default_size) + 'GB)?',
            'choices': ['NO', 'YES']
        }
        answers = prompt(directions_prompt)
        return answers['os_size']

    # get the updated os size
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

    # ask the user if he would like to monitor the request
    def request_progress(self):
        directions_prompt = {
            'type': 'list',
            'name': 'request_prog',
            'message': '  would you like to monitor the progress of your request?',
            'choices': ['YES', 'NO']
        }
        answers = prompt(directions_prompt)
        return answers['request_prog']


    # utility function
    def get_os_dict(self):
        response = requests.get(baseURL + '/template')
        mylist = response.json()
        all_keys = list(set().union(*(d.keys() for d in mylist)))
        all_values = list(set().union(*(d.values() for d in mylist)))
        d = dict(zip(all_keys, all_values))
        return d

    #get the existing server list
    def get_all_servers_list(self):
        hostname_list = []
        response = requests.get(baseURL + '/server')
        for i in response.json():
            hostname_list.append(i['hostname'] + " : " + i['uuid'])

        return hostname_list

    # get details for a specific vm
    def get_vm_details(self):
        vmDetails = []
        zone = self.ask_zone()
        os_name = self.ask_os()
        plan, os_size = self.ask_plan()
        if self.ask_os_size(os_size) == 'YES':
            os_size = self.get_os_storage()
        os = self.get_os_dict()[os_name]
        print('zone: ' + zone + '\n' + 'plan: ' + plan + '\n' + 'os: ' + os_name + '\n' + 'size: ' + str(os_size))
        while True:
            VmNumber = self.get_input('how many VMs you would like to create with the above configurations (1-50):')
            if VmNumber.isnumeric() and 0 < int(VmNumber) <= 50:
                VmNumber = int(VmNumber)
                break
            else:
                print('Please enter a valid value.')
        self.choice_confirm()
        count = 1
        for i in range(0, VmNumber):
            vmName = self.get_input('Please pick a hostname for VM ' + str(count) + '/' + str(VmNumber))
            vmTitle = self.get_input('Please pick a title for VM (' + vmName + ') ' + str(count) + '/' + str(VmNumber))
            if not vmTitle:
                vmTitle = vmName
            vmDetails.append([vmName, zone, os, plan, os_size, vmTitle])
            count = count + 1
        return vmDetails

    #get server status using it uuid
    def get_server_status(self, uuid):
        response = requests.get(baseURL + '/server/status/' + uuid)
        return response.text

    #utility function to get user input
    def get_input(self, msg):
        questions = [
            {
                'type': 'input',
                'name': 'x',
                'message': msg,
            }
        ]
        if 'title' not in msg:
            while True:
                answers = prompt(questions)
                if answers['x']:
                    break
                else:
                    print('Please enter a value.')
        else:
            answers = prompt(questions)
        return answers['x']


    # ask the user to pick a vm from the existing vm list
    def pick_vm(self):

        directions_prompt = {
            'type': 'list',
            'name': 'vm',
            'message': '  please pick one of the below VM list',
            'choices': self.get_all_servers_list()
        }
        answers = prompt(directions_prompt)
        return answers['vm']

    # get the user chice
    def get_choice(self,action='not_multi_choices'):
        directions_prompt = {
            'type': 'list',
            'name': 'delete_option',
            'message': 'please pick a choice for the next step?',
            'choices': ['choice from existing VMs list', 'enter VM UUID', 'Return To the Main Menu', 'EXIT']
        }
        answers = prompt(directions_prompt)
        if answers['delete_option'] == "choice from existing VMs list":
            if action == 'multi_choices':
                return self.multi_choice2()
            else:
                return self.pick_vm().split(':')[1].strip()

        elif answers['delete_option'] == "enter VM UUID":
            count = 0
            while True:
                uuid = self.get_input('What\'s your VM uuid')
                response = requests.get(baseURL + '/server/' + uuid)
                if 'api_error' not in response.json():
                    return uuid
                else:
                    count += 1
                    print('Invalid uuid. Please try again.')
                if count == 3:
                    self.action()
        elif answers['delete_option'] == "Return To the Main Menu":
            self.action()
        elif answers['delete_option'] == "EXIT":
            print('########EXITING PROGRAM THANKS##########')
            exit()

    # get muliti_choice for the user
    def multi_choice2(self):
        vm_list=self.get_all_servers_list()
        vm_dict_list=[]
        for i in vm_list:
            info = {
                "name": i
            }
            vm_dict_list.append(info)
        questions = [
            {
                'type': 'checkbox',
                'message': 'Please choose the VMs you want to delete(you need to to choose at least one)',
                'name': 'vm_list_to_delete',
                'choices': vm_dict_list,
                'validate': lambda answer: 'You must choose at least one VM.' \
                    if len(answer) == 0 else True
            }
        ]
        answers = prompt(questions, style=style)
        return answers['vm_list_to_delete']

    # confirm the user options when creating the vm
    def choice_confirm(self):
        directions_prompt = {
            'type': 'list',
            'name': 'confirm_option',
            'message': 'please confirm your options?',
            'choices': ['Confirm', 'Choose again', 'Return To the Main Menu']
        }
        answers = prompt(directions_prompt)
        if answers['confirm_option'] == "Confirm":
            print("options confirmed\n")
        elif answers['confirm_option'] == "Choose again":
            self.get_vm_details()
        elif answers['confirm_option'] == "Return To the Main Menu":
            self.action()

    #get vm status
    def get_checkStatus_choice(self):
        directions_prompt = {
            'type': 'list',
            'name': 'status_option',
            'message': 'please pick a choice for the next step?',
            'choices': ['check all VMs status', 'get more details about a specific VM', 'Return To the Main Menu',
                        'EXIT']
        }
        answers = prompt(directions_prompt)
        if answers['status_option'] == "check all VMs status":
            self.check_all_vms_status()

        elif answers['status_option'] == "get more details about a specific VM":
            uuid = self.get_choice()
            response = requests.get(baseURL + '/server/' + uuid)
            json_data = json.dumps(response.json(), indent=4)
            print(json_data)
        elif answers['status_option'] == "Return To the Main Menu":
            self.action()
        elif answers['delete_option'] == "EXIT":
            print('########EXITING PROGRAM THANKS##########')
            exit()

    #  check all vms status
    def check_all_vms_status(self):
        response = requests.get(baseURL + '/server')
        for server in response.json():
            print(server['hostname'] + " : " + server['uuid'] + " ===> " + server['state'])

    # return vm details just after creation
    def after_create_info(self, uuid):
        response = requests.get(baseURL + '/server/' + uuid)
        server_details = response.json()
        for i in server_details['ip_addresses']:
            if i['access'] == 'public' and i['family'] == 'IPv4':
                ip = i['address']
                break
        dict = {
            'hostname': server_details['hostname'],
            'title': server_details['title'],
            'uuid': uuid,
            'ip': ip,
            'plan':server_details['plan']

        }
        print(json.dumps(dict, indent=4))

    #start the logging process in the backend
    def logging_thread(self, new_uuid_list):
        while new_uuid_list:
            for uuid in new_uuid_list:
                status = self.get_server_status(uuid)
                if status != 'maintenance':
                    new_uuid_list.remove(uuid)
                    self.mylogger.info_logger('The Server: ' + uuid + ' is in ' + status + ' status.')

    # return creat vm request summary
    def requestSummary(self, vmDetails, monitor):
        print("..")
        summary = []
        for i in vmDetails:
            thisdict = {
                "title": i[5],
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

    # perfrom create vm action
    def performe_CreateVM(self):
        vmDetails = self.get_vm_details()
        monitor = self.request_progress()
        vm_list = self.requestSummary(vmDetails, monitor)
        new_uuid_list = []
        for count, vm in enumerate(vm_list):
            print("Start Creating server: " + vm['hostname'] + " order in the queue: " + str(count + 1) + "/" + str(
                len(vm_list)))
            response = requests.post(baseURL + '/server', json=json.dumps(vm))
            if 'api_error' in response.json():
                print("Failed to create server: " + response.json()['api_error'] + '\n')
                return
            if monitor == 'NO':
                print(json.dumps(response.json(), indent=4))
            new_uuid_list.append(response.json()['uuid'])
            self.mylogger.info_logger(
                'The Server: ' + response.json()['uuid'] + ' is in ' + response.json()['state'] + ' status.')
        if monitor == 'YES':
            count = 1
            while new_uuid_list:
                for uuid in new_uuid_list:
                    status = self.get_server_status(uuid)
                    if status != 'maintenance':
                        print("Server " + str(count) + "/" + str(len(vm_list)) + ": " + status)
                        self.after_create_info(uuid)
                        count += 1
                        new_uuid_list.remove(uuid)
                        self.mylogger.info_logger('The Server: ' + uuid + ' is in ' + status + ' status.')
        else:
            t = threading.Thread(target=self.logging_thread, args=(new_uuid_list,))
            t.start()

    # perfrom modify vm action
    def perform_modify(self):
        uuid_list = []
        out = self.get_choice("multi_choices")
        if type(out) == list:
            for i in out:
                uuid_list.append(i.split(':')[1])
        else:
            uuid_list.append(out)
        for count, uuid in enumerate(uuid_list):
            print("This is the current server configuration "+  str(count + 1) + "/" + str(
                len(uuid_list)))
            self.after_create_info(uuid)
        new_plan, not_used = self.ask_plan()
        for count, uuid in enumerate(uuid_list):
            print('Stopping server '+  str(count + 1) + "/" + str(
                len(uuid_list))+': '+str(uuid)  )
            requests.post(baseURL + '/server/stop/' + uuid)
            while True:
                status = self.get_server_status(uuid)
                if status == 'stopped':
                    break
            print("Server status: stopped")
            print('Modifying server: '+ str(uuid) +  str(count + 1) + "/" + str(
                len(uuid_list)) )
            new_config={
                'plan': new_plan
            }
            response = requests.put(baseURL + '/server/' +uuid, json=json.dumps(new_config))
            json_config=response.json()['server']
            print('This is the new server config:')
            updated_config={
                 'hostname': json_config['hostname'],
                 'title': json_config['title'],
                 'uuid': uuid,
                 'plan': json_config['plan']
             }
            print(json.dumps(updated_config,indent=4))
            print('Starting the server after updating... '+  str(count + 1) + "/" + str(
                len(uuid_list)))

            response_start = requests.post(baseURL + '/server/start/' +uuid)
            print('The server has been started \n')

    # perfrom delete vm action
    def performe_deleteVm(self):
        uuid_list=[]
        out = self.get_choice("multi_choices")
        if type(out)==list:
            for i in out:
                uuid_list.append(i.split(':')[1])
        else:
            uuid_list.append(out)
        for count, uuid in enumerate(uuid_list):
            print('Stopping server... (' + str(count + 1) + "/" + str(len(uuid_list)) + ')')
            requests.post(baseURL + '/server/stop/' + uuid)
            while True:
                status = self.get_server_status(uuid)
                if status == 'stopped':
                    break
            print("Server status: stopped")
            print('Deleting server... (' + str(count + 1) + "/" + str(len(uuid_list)) + ')')
            response = requests.delete(baseURL + '/server/' + uuid)
            if not response.text:
                print("Server status (uuid: " + uuid + "): deleted.")
                self.mylogger.info_logger("Server: " + uuid + " has been deleted.")
            else:
                print("Failed to destroy server (uuid: " + uuid + "): " + json.loads(response.text)['error']['error_message'])

    # perfrom check vm  status  action
    def performe_CheckVmStatus(self):
        self.get_checkStatus_choice()

    # perfrom access vm console action
    def perfome_VmConsole(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/server/' + uuid)
        server_details = response.json()
        for i in server_details['ip_addresses']:
            if i['access'] == 'public' and i['family'] == 'IPv4':
                ip = i['address']
        print("Connecting to the VM...")
        sh = Shell(ip, 'root', 'private_key.pem')
        # Print initial command line
        while True:
            if sh.channel.recv_ready():
                output = sh.channel.recv(1024)
                new_output = str(output.decode('utf-8'))
                output_list = new_output.split('\n')
                output_list.pop(0)
                for count, line in enumerate(output_list):
                    line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r',
                                                                                                                 '')
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
                    line = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r',
                                                                                                                 '')
                    if count == len(stdout) - 1:
                        print(line, end='')
                    else:
                        print(line)
            except KeyboardInterrupt:
                break

    # perfrom check vm performance action
    def perfome_checkPerformance(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/server/perf/' + uuid)
        perf_details = response.json()
        for line in perf_details:
            print(line.strip())

    # perfrom check  vm events  action
    def perform_events(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/logs/' + uuid)
        logs = response.json()
        for line in logs:
            print(line.strip())

    # execution the action chosen by the user
    def action(self):
        print('#############WELCOME#############')
        action = self.ask_action()
        while True:
            if (action == 'Create VM'):
                self.performe_CreateVM()
            elif (action == 'Check VM Status'):
                self.performe_CheckVmStatus()
            elif (action == 'Delete VM'):
                self.performe_deleteVm()
            elif (action == 'Access VM Console'):
                self.perfome_VmConsole()
            elif (action == 'Check VM Performance'):
                self.perfome_checkPerformance()
            elif (action == 'Check VM Events'):
                self.perform_events()
            elif (action == 'EXIT'):
                print('########EXITING PROGRAM THANKS##########')
                exit()
            action = self.ask_action()



if __name__ == '__main__':
    ins = Cli()
    ins.action()
