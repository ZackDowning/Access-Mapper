from getpass import getpass
from discovery import MACAddressDiscovery
from general import Connection

username = input('Username: ')
password = getpass('Password: ')
session = Connection('10.187.165.1', username, password).session
print(MACAddressDiscovery('10.187.161.110', session).mac_address)
