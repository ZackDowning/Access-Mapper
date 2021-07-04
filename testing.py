from general import Connection
from discovery_r import IPAddress, Connectivity
from getpass import getpass
from pprint import pp

username = 'zack.downing'
password = getpass('Password: ')


def ip_addr_query(device):
    ip = device['ip']
    device_type = device['device_type']
    con_type = device['con_type']
    session = Connection(ip, username, password, device_type, con_type).connection()
    return IPAddress('b4de.3160.dbf0', session.session).ip_address


x = Connectivity(['10.187.175.1'], username, password).successful_devices
pp(x)

pp(ip_addr_query(x[0]))
