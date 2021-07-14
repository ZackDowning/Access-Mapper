from general import Connection
from discovery import (
    IPAddress,
    # Gateway,
    # Interface
)
from getpass import getpass

username = 'zack.downing'
password = getpass('Password: ')

session = Connection('10.187.30.3', username, password, 'cisco_nxos').connection().session
intf = IPAddress('40a6.b709.6a7c', session, 'cisco_nxos')
print(intf.ip_address)
