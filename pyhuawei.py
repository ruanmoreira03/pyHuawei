""" Classe destinada a facilitar a implementação de consultas a informações
    em Roteadores Huawei (Ne20/Ne40)
    Requesito: Paramiko"""

import paramiko, time, datetime, re
from easysnmp import Session


class Pyhuawei:
    def __init__(self, ip, ssh, sshuser, sshpass, community):
        self._ip = ip
        self._ssh = ssh
        self._sshuser = sshuser
        self._sshpass = sshpass
        self._community = community
        self._user = 'Null'
        self._user_id = 'Null'

    def open_ssh(self, command):
        cliente = paramiko.SSHClient()
        cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente.connect(self._ip,self._ssh,self._sshuser,self._sshpass)
        stdin,stdout,stderr =  cliente.exec_command(command, get_pty=True, timeout=None, bufsize=1024)

        return stdout, cliente

    def get_snmp(self, oid):
        snmp = Session(hostname=self._ip, community=self._community, version=2)
        return snmp.get(oid).value

    def export_config(self):
        temp, cliente = self.open_ssh('screen-length 0 temporary\ndis cu')
        config = open("config.txt", "w")
        for lines in temp:
            config.write(lines)
            time.sleep(0.01)
        cliente.close()
        config.close()

    def user(self, user):
        temp, cliente = self.open_ssh('dis access-user username '+user+' | include (^\s.[0-9])')
        temp = temp.read()
        pattern = re.compile(r'(\\n\s\s)([0-9]*)',re.IGNORECASE)
        id = re.findall(pattern, str(temp))
        cliente.close()
        try:
            id = id[2][1]
            self._user = user
            self._user_id = id
            return id
        except:
            self._user = ''
            self._user_id = ''
            return False

    def user_online(self, user):
        self._update_(user)
        if self.user_session(user):
            return True
        else:
            self._user = ''
            self._user_id = ''
            return False

    def user_session(self, user):
        self._update_(user)
        try:
            user_session = self.get_snmp('1.3.6.1.4.1.2011.5.2.1.16.1.18.'+self._user_id)
            user_session = str(datetime.timedelta(seconds=int(user_session)))
            return user_session
        except:
            return False


    def user_mac(self, user):
        self._update_(user)
        try:
            user_mac = ""
            mac = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.15.1.17.'+self._user_id)
            for b in mac:
                user_mac += ("%0.2X" % ord(b)) + " "
                mac = user_mac.strip()
                mac = mac.replace(" ", ":")
            return mac
        except:
                return 'Erro: usuario pode estar offline'

    def user_ip(self, user):
        self._update_(user)
        try:
            user_ip = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.15.1.15.'+self._user_id)
            return user_ip
        except:
            return 'Erro: usuario pode estar offline'

    def user_wanipv6(self, user):
        self._update_(user)
        try:
            snmp = Session(hostname=self._ip, community=self._community, version=2)
            ipv6 = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.60.'+self._user_id).value
            ipv6 = self._convert_ipv6_(ipv6)
            return ipv6
        except:
            return 'Erro: usuario pode estar offline'

    def user_lanipv6(self, user):
        self._update_(user)
        try:
            snmp = Session(hostname=self._ip, community=self._community, version=2)
            ipv6 = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.61.'+self._user_id).value
            ipv6 = self._convert_ipv6_(ipv6)
            prefix = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.62.'+self._user_id).value
            return ipv6 +'/'+str(prefix)
        except:
            return 'Erro: usuario pode estar offline'

    def user_plano(self, user):
        self._update_(user)
        try:
            plano = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.15.1.45.'+self._user_id)
            plano = round(int(plano)/1024)
            return plano
        except:
            return 'Erro: usuario pode estar offline'

    def user_qos(self, user):
        self._update_(user)
        try:
            plano = self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.56.'+self._user_id)
            return plano
        except:
            return 'Erro: usuario pode estar offline'

    def user_realtimetraff(self, user):
        self._update_(user)
        up1, down1 = self._user_traff_(user)
        time.sleep(10)
        up2, down2 = self._user_traff_(user)

        up = round((up2 - up1)*8/1024, 3)
        up = (up/2)

        down = round((down2 - down1)*8/1024, 3)
        down = (down/2)

        if up > 1024:
            up = round(up/7812, 3)
        else:
            up = round(up/100000, 3)

        if down > 1024:
            down = round(down/7812, 3)

        else:
            down = round(down/100000, 3)

        return down, up

    @property
    def user_id(self):
        return self._user_id

    @property
    def total_ipv4 (self):
        total_ipv4 = self.get_snmp('1.3.6.1.4.1.2011.5.2.1.14.1.2.0')
        return total_ipv4

    @property
    def total_ipv6 (self):
        total_ipv6 = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.14.1.17.0')
        return total_ipv6

    @property
    def local_users (self):
        result = []
        temp, cliente = self.open_ssh('screen-length 0 temporary\n display local-user state active | incl P')
        user = [line for line in iter(temp.readline, "")]
        pattern = re.compile(r'((\s*Active.*))',re.MULTILINE)
        del user[0:7]
        del user[(len(user)-2):len(user)]
        for item in range(len(user)):
            result.append(re.sub(pattern, "", user[item]))
            #print(result)
        return result

    @property
    def ip (self):
        return self._ip

    def _convert_ipv6_(self, ipv6):
        mystr = ""
        for b in ipv6:
          mystr += ("%0.2X" % ord(b)) + " "
        mystr = mystr.strip()
        mystr = mystr.replace(" ", "")

        return mystr

    def _update_(self, user):
        if self._user_id == 'Null' or self._user != user:
            self.user(user)

    def _user_traff_(self, user):
        self._update_(user)
        try:
            down = int(self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.36.'+self._user_id))
            up = int(self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.37.'+self._user_id))
            return down, up
        except:
            return 'Erro: usuario pode estar offline'

