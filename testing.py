from general import Connection
from getpass import getpass
from pprint import pp
import re

# username = 'zack.downing'
username = 'admin'
password = getpass('Password: ')

ssh = Connection('192.168.3.11', username, password, 'cisco_nxos').connection()
show_mac = []
output = ssh.session.send_command(f'show mac address-table | i */').split('\n')
for idx, line in enumerate(output):
    if idx != 0:
        line_split = re.split(r' +', line)
        if len(line_split) == 8:
            show_mac.append({
                'destination_port': line_split[7],
                'destination_address': line_split[2],
                'vlan': line_split[1]
            })
pp(show_mac, indent=2)
