from netmiko import ConnectHandler
from netmiko import ssh_exception
from netmiko import SSHDetect
from address_validator import ipv4
import os

os.environ['NET_TEXTFSM'] = './Inputs/working-files/templates'


class MgmtIPAddresses:
    def __init__(self, mgmt_file_location):
        self.mgmt_file_location = mgmt_file_location
        self.mgmt_ips = []
        self.valid = False
        self.invalid_ips = {
            'line_num': [],
            'ip_address': []
        }

    def validate(self):
        invalid_lines = 0
        line_num = 0
        with open(self.mgmt_file_location) as file:
            for address in file:
                line_num += 1
                ip_address = str(address).strip('\n')
                if ipv4(ip_address) is False:
                    self.invalid_ips['line_num'].append(str(line_num))
                    self.invalid_ips['ip_address'].append(str(address))
                    invalid_lines += 1
                else:
                    self.mgmt_ips.append(ip_address)
            if invalid_lines == 0:
                self.valid = True
        return self.valid


# # Checks and waits for validity of individual IP address in MGMT.txt file and returns list of IP addresses once valid
# def mgmt_ip_addresses(mgmt_file):
#     valid_file = False
#     output = {
#         'mgmt_ips': [],
#         'valid_file': []
#     }
#     mgmt_ips = []
#     while valid_file is False:
#         try:
#             invalid_lines = 0
#             line_num = 0
#             invalid_ips = {
#                 'line_num': [],
#                 'ip_address': []
#             }
#             with open(mgmt_file) as file:
#                 for address in file:
#                     line_num += 1
#                     ip_address = str(address).strip('\n')
#                     if ipv4(ip_address) is False:
#                         invalid_ips['line_num'].append(str(line_num))
#                         invalid_ips['ip_address'].append(str(address))
#                         invalid_lines += 1
#                     else:
#                         mgmt_ips.append(ip_address)
#             if invalid_lines == 0:
#                 valid_file = True
#                 print('"MGMT.txt" file validated.')
#             else:
#                 print('Invalid MGMT.txt file entries:')
#                 for (line_n, ip_addr) in zip(invalid_ips['line_num'], invalid_ips['ip_address']):
#                     print(f'   Line {line_n} - {ip_addr}')
#                 input('\nPress Enter once "MGMT.txt" file is ready.')
#         except FileNotFoundError:
#             input('\n"MGMT.txt" file not found."\n'
#                   'Press Enter once "MGMT.txt" file is ready.')
#     return mgmt_ips


# Returns dictionary with..
# 'con_type': con_type,
# 'connectivity': connectivity,
# 'authentication': authentication,
# 'authorization': authorization,
# 'hostname': hostname,
# 'session': session,
# 'devicetype': devicetype,
# 'exception': exception
def connection(ip_address, username, password):
    device = {
        'device_type': 'autodetect',
        'ip': ip_address,
        'username': username,
        'password': password
    }
    hostname = ''
    con_type = ''
    session = ''
    devicetype = ''
    exception = 'None'
    authentication = False
    authorization = False
    connectivity = False
    try:
        try:
            devicetype = SSHDetect(**device).autodetect()
            device['device_type'] = devicetype
            session = ConnectHandler(**device)
        except ValueError:
            try:
                device['device_type'] = 'cisco_ios'
                devicetype = 'cisco_ios'
                session = ConnectHandler(**device)
            except ValueError:
                device['device_type'] = 'cisco_ios'
                devicetype = 'cisco_ios'
                session = ConnectHandler(**device)
        showver = session.send_command('show version', use_textfsm=True)
        if not showver.__contains__('Failed'):
            hostname = showver[0]['hostname']
            authorization = True
        authentication = True
        connectivity = True
        con_type = 'SSH'
    except (ConnectionRefusedError, ValueError, ssh_exception.NetmikoAuthenticationException,
            ssh_exception.NetmikoTimeoutException):
        try:
            device['device_type'] = 'cisco_ios_telnet'
            devicetype = 'cisco_ios_telnet'
            device['secret'] = password
            session = ConnectHandler(**device)
            showver = session.send_command('show version', use_textfsm=True)
            if not showver.__contains__('Failed'):
                hostname = showver[0]['hostname']
                authorization = True
            authentication = True
            connectivity = True
            con_type = 'TELNET'
        except ssh_exception.NetmikoAuthenticationException:
            try:
                device['device_type'] = 'cisco_ios_telnet'
                devicetype = 'cisco_ios_telnet'
                device['secret'] = password
                session = ConnectHandler(**device)
                showver = session.send_command('show version', use_textfsm=True)
                if not showver.__contains__('Failed'):
                    hostname = showver[0]['hostname']
                    authorization = True
                authentication = True
                connectivity = True
                con_type = 'TELNET'
            except ssh_exception.NetmikoAuthenticationException:
                connectivity = True
                exception = 'NetmikoAuthenticationException'
            except ssh_exception.NetmikoTimeoutException:
                exception = 'NetmikoTimeoutException'
            except ConnectionRefusedError:
                exception = 'ConnectionRefusedError'
            except ValueError:
                exception = 'ValueError'
            except TimeoutError:
                exception = 'TimeoutError'
        except ssh_exception.NetmikoTimeoutException:
            exception = 'NetmikoTimeoutException'
        except ConnectionRefusedError:
            exception = 'ConnectionRefusedError'
        except ValueError:
            exception = 'ValueError'
        except TimeoutError:
            exception = 'TimeoutError'
    except OSError:
        exception = 'OSError'
    return {
        'con_type': con_type,
        'connectivity': connectivity,
        'authentication': authentication,
        'authorization': authorization,
        'hostname': hostname,
        'session': session,
        'devicetype': devicetype,
        'exception': exception
    }
