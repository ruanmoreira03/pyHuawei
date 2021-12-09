""" Classe destinada a facilitar a implementação de consultas a informações
    em Roteadores Huawei (Ne20/Ne40)
    Requesito: Paramiko, easysnmp"""

import paramiko, time, datetime, re
from easysnmp import Session


class Pyhuawei:
    def __init__(self, ip, ssh, sshuser, sshpass, community):
        self._ip = ip
        self._ssh = ssh
        self._sshuser = sshuser
        self._sshpass = sshpass
        self._community = community
        self._user = None
        self._user_id = None

    def open_ssh(self, command):
        cliente = paramiko.SSHClient()
        cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente.connect(self._ip,self._ssh,self._sshuser,self._sshpass)
        stdin,stdout,stderr =  cliente.exec_command(command, get_pty=True, timeout=None, bufsize=1024)

        return stdout, cliente


    def get_snmp(self, oid):
        snmp = Session(hostname=self._ip, community=self._community, version=2)
        return snmp.get(oid).value


    def walk_snmp(self, oid):
        snmp = Session(hostname=self._ip, community=self._community, version=2)
        return snmp.walk(oid)


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
        except Exception as E:
            self._user = None
            self._user_id = None
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
        except Exception as E:
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
        except Exception as E:
                return f'{E} Erro: usuario pode estar offline'


    def user_ip(self, user):
        self._update_(user)
        try:
            user_ip = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.15.1.15.'+self._user_id)
            return user_ip
        except Exception as E:
                return f'{E} Erro: usuario pode estar offline'


    def user_wanipv6(self, user):
        self._update_(user)
        try:
            snmp = Session(hostname=self._ip, community=self._community, version=2)
            ipv6 = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.60.'+self._user_id).value
            ipv6 = self._convert_ipv6_(ipv6)
            return ipv6
        except Exception as E:
                return f'{E} Erro: usuario pode estar offline'


    def user_lanipv6(self, user):
        self._update_(user)
        try:
            snmp = Session(hostname=self._ip, community=self._community, version=2)
            ipv6 = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.61.'+self._user_id).value
            ipv6 = self._convert_ipv6_(ipv6)
            prefix = snmp.get('1.3.6.1.4.1.2011.5.2.1.15.1.62.'+self._user_id).value
            return ipv6 +'/'+str(prefix)
        except Exception as E:
                return f'{E} Erro: usuario pode estar offline'


    def user_plano(self, user):
        self._update_(user)
        try:
            plano = self.get_snmp('iso.3.6.1.4.1.2011.5.2.1.15.1.45.'+self._user_id)
            plano = round(int(plano)/1024)
            return plano
        except Exception as E:
                return f'{E} Erro: usuario pode estar offline'


    def user_qos(self, user):
        self._update_(user)
        plano = self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.56.'+self._user_id)
        if plano == 'NOSUCHINSTANCE':
            raise ValueError
        return plano


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


    def cpu_usage(self, time_avg):
        try:
            if time_avg == 1:
                return self.get_snmp('1.3.6.1.4.1.2011.6.3.4.1.3.1.3.0')
            if time_avg == 5:
                return self.get_snmp('1.3.6.1.4.1.2011.6.3.4.1.4.1.3.0')
            else:
                return self.get_snmp('1.3.6.1.4.1.2011.6.3.4.1.2.1.3.0')
        except Exception as e:
            return f'Error. \n {e}'


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
        return result


    @property
    def ppp_interfaces(self):
        tmp = self.interfaces
        int = []
        for item in tmp:
            try:
                qtd = self.get_snmp('1.3.6.1.4.1.2011.5.2.1.42.1.2.1.'+item['id'])
                if qtd != 'NOSUCHINSTANCE':
                    int.append((item['description'], qtd))
            except:
                pass
        return int


    @property
    def interfaces(self):
        int = []
        tmp_desc  = self.walk_snmp('1.3.6.1.2.1.2.2.1.2')
        for item in tmp_desc:
            int.append({"id":           re.search(r'[0-9]*$', item.oid).group(),                 ##int ID
                        "name":         item.value,                                              ##int name
                        "description":  self._snmp_get_index_(item, '1.3.6.1.2.1.31.1.1.1.18.'), ##int desc
                        "admin-status": self._snmp_get_index_(item, '1.3.6.1.2.1.2.2.1.7.'),     ## AdminStatus
                        "oper-status":  self._snmp_get_index_(item, '1.3.6.1.2.1.2.2.1.8.')})    ## Oper Status
        return int


    @property
    def ip (self):
        return self._ip


    @property
    def sysname(self):
        return self.get_snmp('1.3.6.1.2.1.1.5.0')


    @property
    def uptime(self):
        time = self.get_snmp('1.3.6.1.2.1.1.3.0')
        uptime = str(datetime.timedelta(seconds=int(time)/100))
        return uptime


    @property
    def system_time(self):
        return self.get_snmp('1.3.6.1.4.1.2011.5.25.31.6.6.0')


    @property
    def model(self):
        return self.get_snmp('1.3.6.1.4.1.2011.5.25.31.6.5.0')


    @property
    def sys_mac(self):
        return self.get_snmp('1.3.6.1.4.1.2011.5.25.31.6.7.0')


    @property
    def sysinfo(self):
        return self.get_snmp('iso.3.6.1.2.1.1.1.0')


    @property
    def local_asn(self):
        return self.get_snmp('1.3.6.1.2.1.15.2.0')


    @property
    def bgp_router_id(self):
        return self.get_snmp('1.3.6.1.2.1.15.4.0')

    @property
    def bgp_peers(self):
        peers = self.walk_snmp('1.3.6.1.2.1.15.3.1.7')
        return [item.value for item in peers]


    @property
    def bgp_peers_info(self):
        asn = []
        for item in self.bgp_peers:
            asn.append({"peer":          item,                                         #IP Remoto (index)
                        "ip":            self.get_snmp('1.3.6.1.2.1.15.3.1.5.'+item),  #IP da nossa ponta
                        "peer-as":       self.get_snmp('1.3.6.1.2.1.15.3.1.9.'+item),  #Remote AS Number
                        "session-state": self.get_snmp('1.3.6.1.2.1.15.3.1.2.'+item),  #Estado da sessao
                        "router-id":     self.get_snmp('1.3.6.1.2.1.15.3.1.1.'+item),  #Router ID remoto
                        "session-time":  str(datetime.timedelta(seconds=int(self.get_snmp('1.3.6.1.2.1.15.3.1.16.'+item)))), #Tempo de sessao
                        "total-routes":  self.get_snmp('1.3.6.1.4.1.2011.5.25.177.1.1.3.1.1.0.1.1.1.4.'+item), #numero de rotas
                        "active-routes": self.get_snmp('1.3.6.1.4.1.2011.5.25.177.1.1.3.1.2.0.1.1.1.4.'+item)}) #numero de rotas ativas
        return asn


    def _convert_ipv6_(self, ipv6):
        mystr = ""
        for b in ipv6:
          mystr += ("%0.2X" % ord(b)) + " "
        mystr = mystr.strip()
        mystr = mystr.replace(" ", "")

        return mystr


    def _update_(self, user):
        if self._user_id == None or self._user != user:
            self.user(user)


    def _user_traff_(self, user):
        self._update_(user)
        try:
            down = int(self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.36.'+self._user_id))
            up = int(self.get_snmp('1.3.6.1.4.1.2011.5.2.1.15.1.37.'+self._user_id))
            return down, up
        except:
            return 'Erro: usuario pode estar offline'


    def _snmp_get_index_(self, item, oid):
        return self.get_snmp(oid+re.search(r'[0-9]*$', item.oid).group())


    def __str__(self):
        return f'{self.sysinfo}Sysname: {self.sysname}\nUptime: {self.uptime}\nMNGMT IP: {self.ip}\nSystem MAC: {self.sys_mac}'


    def __eq__(self, obj):
        return self.sys_mac == obj.sys_mac
