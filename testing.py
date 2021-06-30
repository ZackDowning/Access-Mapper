from getpass import getpass
from discovery import IPAddressDiscovery
from general import Connection

username = input('Username: ')
password = getpass('Password: ')
session = Connection('10.187.165.1', username, password).session
test = IPAddressDiscovery('10.187.161.110', session).l3_intf
