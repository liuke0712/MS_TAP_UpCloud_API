from __future__ import print_function, unicode_literals

import json
import re
import sys
import threading
import time

import requests
from PyInquirer import style_from_dict, Token, prompt

import logs
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
        self.mylogger = logs.Logs()

    def multi_choice2(self):
        vm_list = self.get_all_servers_list()
        vm_dict_list = []
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

    def ask_action(self):
        directions_prompt = {
            'type': 'list',
            'name': 'action',
            'message': 'Which action would you like to perform?',
            'choices': ['CreateVM', 'CheckVmStatus', 'ModifyVm', 'DeleteVm', 'VmConsole', 'PerformanceStat', 'VmEvents',
                        'Exit']
        }
        answers = prompt(directions_prompt)
        return answers['action']

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

    def ask_os(self):
        directions_prompt = {
            'type': 'list',
            'name': 'os',
            'message': 'Which os would you like to choose?',
            'choices': self.get_os_dict().keys()
        }
        answers = prompt(directions_prompt)
        return answers['os']

    def ask_os_size(self, default_size):
        directions_prompt = {
            'type': 'list',
            'name': 'os_size',
            'message': 'Would you like to change the default storage size(' + str(default_size) + 'GB)?',
            'choices': ['NO', 'YES']
        }
        answers = prompt(directions_prompt)
        return answers['os_size']

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
        return answers['confirm_option']

    def get_vm_details(self):
        vmDetails = []
        while True:
            zone = self.ask_zone()
            os_name = self.ask_os()
            os = self.get_os_dict()[os_name]
            plan, os_size = self.ask_plan()
            if self.ask_os_size(os_size) == 'YES':
                os_size = self.get_os_storage()
            print('zone: ' + zone + '\n' + 'plan: ' + plan + '\n' + 'os: ' + os_name + '\n' + 'size: ' + str(os_size))
            while True:
                VmNumber = self.get_input('how many VMs you would like to create with the above configurations (1-50):')
                if VmNumber.isnumeric() and 0 < int(VmNumber) <= 50:
                    VmNumber = int(VmNumber)
                    break
                else:
                    print('Please enter a valid value.')
            option = self.choice_confirm()
            if option == 'Confirm':
                break
            elif option == 'Return To the Main Menu':
                return "exit"
        count = 1
        for i in range(0, VmNumber):
            vmName = self.get_input('Please pick a hostname for VM ' + str(count) + '/' + str(VmNumber))
            vmTitle = self.get_input('Please pick a title for VM (' + vmName + ') ' + str(count) + '/' + str(VmNumber))
            if not vmTitle:
                vmTitle = vmName
            vmDetails.append([vmName, zone, os, plan, os_size, vmTitle])
            count = count + 1
        return vmDetails

    def get_os_dict(self):
        response = requests.get(baseURL + '/template')
        mylist = response.json()
        d = {}
        for os in mylist:
            key = list(os.keys())[0]
            d[key] = os[key]
        return d

    def get_all_servers_list(self):
        hostname_list = []
        response = requests.get(baseURL + '/server')
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
            'message': '  please pick one of the below VM list',
            'choices': self.get_all_servers_list()
        }
        answers = prompt(directions_prompt)
        return answers['vm']

    def get_choice(self, action='not_multi_choices'):
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
                return self.pick_vm().split(':')[1]

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

    def check_all_vms_status(self):
        response = requests.get(baseURL + '/server')
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
            'title': server_details['title'],
            'uuid': uuid,
            'ip': ip,
            'plan': server_details['plan']

        }
        print(json.dumps(dict, indent=4))

    def perform_CreateVM(self):
        vmDetails = self.get_vm_details()
        if isinstance(vmDetails, str):
            return
        monitor = self.request_progress()
        vm_list = self.requestSummary(vmDetails, monitor)
        new_uuid_list = []
        for count, vm in enumerate(vm_list):
            print("Start Creating server: " + vm['hostname'] + " " + str(count + 1) + "/" + str(len(vm_list)))
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
            print('')
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

    def logging_thread(self, new_uuid_list):
        while new_uuid_list:
            for uuid in new_uuid_list:
                status = self.get_server_status(uuid)
                if status != 'maintenance':
                    new_uuid_list.remove(uuid)
                    self.mylogger.info_logger('The Server: ' + uuid + ' is in ' + status + ' status.')

    def perform_modify(self):
        uuid_list = []
        out = self.get_choice("multi_choices")
        if type(out) == list:
            for i in out:
                uuid_list.append(i.split(':')[1])
        else:
            uuid_list.append(out)
        uuid_len = len(uuid_list)
        print("\n=======This is your current server configurations======== \n")
        for count, uuid in enumerate(uuid_list):
            print(f"Server {count+1}/{uuid_len}")
            self.after_create_info(uuid)
        print('')
        new_plan, not_used = self.ask_plan()
        for count, uuid in enumerate(uuid_list):
            print(f'Stopping server ({uuid})... ({count+1}/{uuid_len})')
            requests.post(baseURL + '/server/stop/' + uuid)
        print('')
        count = 1
        while uuid_list:
            for uuid in uuid_list:
                if self.get_server_status(uuid) == 'stopped':
                    print(f'Modifying server... ({count}/{uuid_len})')
                    print(f"Server status ({uuid}): stopped")
                    new_config = {
                        'plan': new_plan
                    }
                    response = requests.put(baseURL + '/server/' + uuid, json=json.dumps(new_config))
                    json_config = response.json()['server']
                    print('New server configuration:')
                    updated_config = {
                        'hostname': json_config['hostname'],
                        'title': json_config['title'],
                        'uuid': uuid,
                        'plan': json_config['plan']
                    }
                    print(json.dumps(updated_config, indent=4))
                    print(f'Starting the server after updating... ({count}/{uuid_len})')
                    requests.post(baseURL + '/server/start/' + uuid)
                    print('The server has been started \n')
                    count += 1
                    uuid_list.remove(uuid)

    def perform_deleteVm(self):
        uuid_list = []
        out = self.get_choice("multi_choices")
        if type(out) == list:
            for i in out:
                uuid_list.append(i.split(':')[1])
        else:
            uuid_list.append(out)
        uuid_len = len(uuid_list)
        for count, uuid in enumerate(uuid_list):
            print(f'Stopping server ({uuid})... ({count+1}/{uuid_len})')
            requests.post(baseURL + '/server/stop/' + uuid)
        print('')
        count = 1
        while uuid_list:
            for uuid in uuid_list:
                if self.get_server_status(uuid) == 'stopped':
                    print(f'Deleting server... ({count}/{uuid_len})')
                    print(f"Server status ({uuid}): stopped")
                    response = requests.delete(baseURL + '/server/' + uuid)
                    if not response.text:
                        print(f"Server successfully deleted\n")
                        self.mylogger.info_logger("Server: " + uuid + " has been deleted.")
                    else:
                        print("Failed to destroy server (uuid: " + uuid + "): " + json.loads(response.text)['error'][
                            'error_message']+'\n')
                    count += 1
                    uuid_list.remove(uuid)

    def perform_CheckVmStatus(self):
        self.get_checkStatus_choice()

    def perform_VmConsole(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/server/' + uuid)
        server_details = response.json()
        for i in server_details['ip_addresses']:
            if i['access'] == 'public' and i['family'] == 'IPv4':
                ip = i['address']
        print("Connecting to the VM...")
        sh = Shell(ip, 'root', 'private_key.pem')
        sys.stdout.write('\n')
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

        # add the manager component

    def perform_checkPerformance(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/server/perf/' + uuid)
        perf_details = response.json()
        print('')
        for line in perf_details:
            print(line.strip())
        print('')

    def perform_events(self):
        uuid = self.get_choice()
        response = requests.get(baseURL + '/logs/' + uuid)
        logs = response.json()
        print('')
        for line in logs:
            print(line.strip())
        print('')

    def action(self):
        print('#############WELCOME#############')
        action = self.ask_action()
        while True:
            if (action == 'CreateVM'):
                self.perform_CreateVM()
            elif (action == 'CheckVmStatus'):
                self.perform_CheckVmStatus()
            elif (action == 'ModifyVm'):
                self.perform_modify()
            elif (action == 'DeleteVm'):
                self.perform_deleteVm()
            elif (action == 'VmConsole'):
                self.perform_VmConsole()
            elif (action == 'PerformanceStat'):
                self.perform_checkPerformance()
            elif (action == 'VmEvents'):
                self.perform_events()
            elif (action == 'Exit'):
                print('########EXITING PROGRAM THANKS##########')
                exit()
            action = self.ask_action()

    def requestSummary(self, vmDetails, monitor):
        print("..")
        summary = []
        print("=======This is your request choices summary======== \n")
        print("VMs DETAILS \n")
        for count, i in enumerate(vmDetails):
            thisdict = {
                "title": i[5],
                "hostname": i[0],
                "zone": i[1],
                "plan": i[3],
                "os": i[2],
                "size": i[4]
            }
            print(f'Server {count + 1}/{len(vmDetails)}')
            print(json.dumps(thisdict, indent=4))
            summary.append(thisdict)
        print("\n\n")
        print("MONITORING CHOICE: ", monitor, "\n")
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


if __name__ == '__main__':
    ins = Cli()
    ins.action()
