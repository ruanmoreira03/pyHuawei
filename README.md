# pyHuawei
Api de integração com roteadores Huawei (Ne20)

Requirements:

paramiko, easysnmp

Exemplos:

Inicializando:

#router = Pyhuawei('IP', 'SSH_PORT', 'SSH_USER','SSH_PASS', 'SNMPv2c_COMMUNITY')

router = Pyhuawei('172.16.1.1', '22', 'user','password', 'public')


Dos metodos relacionados ao Usuario:

A maior parte dos metodos dessa classe recebe o nome de usuario pppoe como parametro.
Estes são os metodos de consulta a clientes pppoe:

router.online(pppoeUser)

Abre uma sessão SSH com o router e retorna o ID do usuario. Caso o username solicitado estiver offline, retorna False

router.user_online(pppoeUser)

Verifica se o username está online retornando True or False

router.user_session(pppoeUser)

Retorna o tempo de sessão pppoe do usuario

router.user_mac(pppoeUser)

Retorna o MAC do usuario pppoe

router.user_ip(pppoeUser)

Retorna o IP de sessão pppoe

router.user_plano(pppoeUser)

Retorna a banda disponivel para o usuario

router.user_qos(pppoeUser)

Retorna o QOS profile atribuido ao usuario

router.user_realtimetraff(pppoeUser)

Retorna a banda consumida em tempo real pelo usuario. 

router.user_wanipv6(pppoeUser)

retorna o IPv6 da sessão PPPoE

router.user_lanipv6(pppoeUser)

retorna a rede prefix delegation do usuario.


Uma vez que foi feita uma consulta, o nome de usuario e ID ficam armazenados até que uma nova consulta para outro usuario com username ou ID diferentes seja executada, logo, vc pode usar o metodo 

router.user_id

para acessar o ID sem precisar abrir nova sessão SSH para buscar o ID.

-------------------------------------------------------------------------------------------

Dos metodos relacionados ao equipamento.

router.export_config()

Exporta a saida do comando "display current-configuration" para arquivo

router.total_ipv4

Retorna o total de clientes conectados utilizando IPv4

router.total_ipv6

Retorna o total de clientes conectados em Dual-stack


router.local_users

Retorna lista de usuarios PPP criados localmente no equipamento

router.ip

Retorna o IP do equipamento



