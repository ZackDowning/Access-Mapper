from netmiko import ConnectHandler
from netmiko import ssh_exception
from netmiko import SSHDetect
from address_validator import ipv4
import os
import sys

if getattr(sys, 'frozen', False):
    os.environ['NET_TEXTFSM'] = sys._MEIPASS
else:
    os.environ['NET_TEXTFSM'] = './working-files/templates'


class MgmtIPAddresses:
    """
    Input .txt file location containing list of management IP addresses
    """
    def __init__(self, mgmt_file_location):
        self.mgmt_file_location = mgmt_file_location
        self.mgmt_ips = []
        self.invalid_line_nums = []
        self.invalid_ip_addresses = []

    def validate(self):
        """
        Returns bool for file format validity and appends values to attributes
        """
        invalid_lines = 0
        with open(self.mgmt_file_location) as file:
            for idx, address in enumerate(file):
                ip_address = str(address).strip('\n')
                if ipv4(ip_address) is False:
                    self.invalid_line_nums.append(str(idx + 1))
                    self.invalid_ip_addresses.append(str(address))
                    invalid_lines += 1
                else:
                    self.mgmt_ips.append(ip_address)
            if invalid_lines == 0:
                return True
            else:
                return False


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
