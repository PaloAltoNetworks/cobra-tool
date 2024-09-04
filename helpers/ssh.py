import paramiko


class SSHClient(object):

    def __init__(self, host, username, keypath):
        self.host = host
        self.username = username
        self.keypath = keypath
        self.connection = None

    def connect(self):
        pkey = paramiko.RSAKey.from_private_key_file(self.keypath)
        self.connection = paramiko.SSHClient()
        policy = paramiko.AutoAddPolicy()
        # TODO: ^^^ is this the same as `ssh -o 'StrictHostKeyChecking accept-new'` ??
        self.connection.set_missing_host_key_policy(policy)
        self.connection.connect(self.host, username=self.username, pkey=pkey)

    def exec(self, command):
        stdin, stdout, stderr = self.connection.exec_command(command)
        err = stderr.read().decode()
        if err:
            # TODO: consider custom Exception
            raise Exception(
                'Error executing command in SSH session: {}'.format(err))
        else:
            return stdout.read().decode()

    def disconnect(self):
        if self.connection:
            self.connection.close()
