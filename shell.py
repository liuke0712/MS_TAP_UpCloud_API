import time
import paramiko


class Shell:
    def __init__(self, host, user, key_file):
        self.sshClient = paramiko.SSHClient()
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshClient.connect(host, username=user, key_filename=key_file, port=22)
        self.channel = self.sshClient.get_transport().open_session()
        self.channel.get_pty()
        self.channel.invoke_shell()

    def __del__(self):
        self.sshClient.close()

    def execute(self, cmd):
        self.channel.send(cmd + "\n")

        while True:
            if self.channel.recv_ready():
                output = self.channel.recv(1024)
                new_output = str(output.decode('utf-8'))
                output_list = new_output.split('\n')
                output_list.pop(0)
                return output_list
            else:
                time.sleep(0.5)
                if not (self.channel.recv_ready()):
                    break


if __name__ == '__main__':
    sh = Shell('94.237.57.153', 'root', 'private_key_save.pem')
    # Print initial command line
    while True:
        if sh.channel.recv_ready():
            output = sh.channel.recv(1024)
            new_output = str(output.decode('utf-8'))
            output_list = new_output.split('\n')
            output_list.pop(0)
            for count, line in enumerate(output_list):
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
                if count == len(stdout) - 1:
                    print(line, end='')
                else:
                    print(line)
        except KeyboardInterrupt:
            break
