from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt, Separator
import json
from PyInquirer import prompt, Separator
from Upcloud_API import Upcloud_API
import requests

from requests import request
style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

class Cli:
    def __init__(self):
       self.manager = Upcloud_API()

    def ask_action(self):
        directions_prompt = {
            'type': 'list',
            'name': 'action',
            'message': 'Which action would you like to perform?',
            'choices': ['CreateVM', 'CheckVmStatus', 'DeleteVm', 'VmConsole','PerformanceStat','VmEvents','Exit']
        }
        answers = prompt(directions_prompt)
        return answers['action']

    def ask_zone(self):
        directions_prompt = {
            'type': 'list',
            'name': 'zone',
            'message': 'Which zone would you like to choose?',
            'choices': self.manager.get_zones()
        }
        answers = prompt(directions_prompt)
        return answers['zone']

    def ask_plan(self):
        directions_prompt = {
            'type': 'list',
            'name': 'plan',
            'message': 'Which plan would you like to choose?',
            'choices': self.manager.planList
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
            else :
                continue



    # TODO better to use while loop than recursion!



    def request_progress(self):
        directions_prompt = {
            'type': 'list',
            'name': 'request_prog',
            'message': '  would you like to monitor the progress of your request?',
            'choices': ['YES','NO']
        }
        answers = prompt(directions_prompt)
        return answers['request_prog']

    def choice_confirm(self):
        directions_prompt = {
            'type': 'list',
            'name': 'confirm_option',
            'message': 'please confirm your options?',
            'choices': ['Confirm','Choose again','Return To the Main Menu']
        }
        answers = prompt(directions_prompt)
        if answers['confirm_option'] == "Confirm":
            print("options confirmed\n")
        elif answers['confirm_option'] == "Choose again":
            self.get_vm_details()
        elif answers['confirm_option'] == "Return To the Main Menu":
            self.action()


    def get_vm_details(self):
        vmDetails=[]
        zone = self.ask_zone()
        plan = self.ask_plan()
        os_name=self.ask_os()
        os = self.get_os_dict()[os_name]
        os_size = self.get_os_storage()
        VmNumber = int(self.get_input('how many VMs you would like to create with these options:\n' +'zone :' +zone +'\n'+'plan: '+plan +'\n'+'os: '+os_name +'\n' ))
        self.choice_confirm()
        count=1
        for i in range(0, VmNumber):
            vmName = self.get_input('Please pick a name for VM '+ str(count) +'/' +str(VmNumber))
            vmDetails.append([vmName, zone, os, plan,os_size])
            count=count+1
        return vmDetails
    def get_os_dict(self):
        mylist=self.manager.get_templates()
        all_keys = list(set().union(*(d.keys() for d in mylist)))
        all_values = list(set().union(*(d.values() for d in mylist)))
        d = dict(zip(all_keys, all_values))
        return d

    def creatinn_info(self,uuid):
        dict={
            'VmName':self.manager.server_name(uuid),
            'uuid': uuid,
            'ip': self.manager.server_ip(uuid)

        }
        print(json.dumps(dict,indent=4))

    def get_all_servers_list(self):
        hostname_list=[]
        for i in  self.manager.server_list() :
            hostname_list.append(i['hostname'] +":"+i['uuid'])

        return hostname_list



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
            'choices': ['choice from existing VMs list','enter VM UUID','Return To the Main Menu','EXIT']
        }
        answers = prompt(directions_prompt)
        if  answers['delete_option'] == "choice from existing VMs list":
            return self.pick_vm().split(':')[1]

        elif answers['delete_option'] =="enter VM UUID":
            return self.get_input('What\'s your VM uuid')
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
            'choices': ['check all VMs status','get more details about a specific VM','Return To the Main Menu','EXIT']
        }
        answers = prompt(directions_prompt)
        if  answers['status_option'] == "check all VMs status":
            self.check_all_vms_status()

        elif answers['status_option'] =="get more details about a specific VM":
            out=self.manager.single_server(self.get_delete_choice())
            json_data = json.dumps(out,indent=4)
            print(json_data)



    def check_all_vms_status(self):
        for i in self.get_all_servers_list():
            print (self.manager.server_status(i.split(':')[1]))


    def performe_CreateVM(self):
        vmDetails=self.get_vm_details()
        monitor=self.request_progress()
        vm_list=self.requestSummary( vmDetails, monitor)
        #for vm in vm_list:
            #reponse=requests.post('http://127.0.0.1:5000/server',json=vm)
        #add the manager component

    def performe_deleteVm(self):
        uuid=self.get_delete_choice()
        #print(vm)
        #add the manager component


    def performe_CheckVmStatus(self):
        self.get_checkStatus_choice()
    def perfome_VmConsole(self):
        uuid=self.get_delete_choice()
        ip=self.manager.server_ip(uuid)
        #add the manager component
    def perfome_checkPerformance(self):
        uuid=self.get_delete_choice()
        self.manager.perform_statistic_linux(uuid)


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
                exit()
            action = self.ask_action()

    def requestSummary(self,vmDetails,monitor):
        print("..")
        summary=[]
        for i in vmDetails:
            thisdict = {
                "hostname": i[0],
                "zone": i[1],
                "plan": i[2],
                "os": i[3],
                "os_size":i[4]

            }

            summary.append(thisdict)
        print("=======this is your request choices summary======== \n\n\n")
        print("VMs DETAILS \n\n\n")
        print(summary)
        print("\n\n\n")
        print("MONITORING CHOICE: ",monitor,"\n\n\n")



    def get_input(self,msg):
        questions = [
            {
                'type': 'input',
                'name': 'x',
                'message': msg,
            }
        ]
        answers = prompt(questions)
        return answers['x']




ins=Cli()
ins.action()