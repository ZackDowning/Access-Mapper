import os
import sys
from netmiko import ConnectHandler, ssh_exception, SSHDetect
from address_validator import ipv4

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


class Connection:
    def __init__(self, ip_address, username, password):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = ''
        self.devicetype = ''
        self.con_type = ''
        self.exception = 'None'
        self.authentication = False
        self.authorization = False
        self.connectivity = False

    def session(self):
        """
        Returns SSH or TELNET Netmiko session and populates Connection attributes
        """
        session = None
        device = {
            'device_type': 'autodetect',
            'ip': self.ip_address,
            'username': self.username,
            'password': self.password
        }
        try:
            try:
                self.devicetype = SSHDetect(**device).autodetect()
                device['device_type'] = self.devicetype
                session = ConnectHandler(**device)
            except ValueError:
                try:
                    device['device_type'] = 'cisco_ios'
                    self.devicetype = 'cisco_ios'
                    session = ConnectHandler(**device)
                except ValueError:
                    device['device_type'] = 'cisco_ios'
                    self.devicetype = 'cisco_ios'
                    session = ConnectHandler(**device)
            showver = session.send_command('show version', use_textfsm=True)
            if not showver.__contains__('Failed'):
                self.hostname = showver[0]['hostname']
                self.authorization = True
            self.authentication = True
            self.connectivity = True
            self.con_type = 'SSH'
        except (ConnectionRefusedError, ValueError, ssh_exception.NetmikoAuthenticationException,
                ssh_exception.NetmikoTimeoutException):
            try:
                device['device_type'] = 'cisco_ios_telnet'
                self.devicetype = 'cisco_ios_telnet'
                device['secret'] = self.password
                session = ConnectHandler(**device)
                showver = session.send_command('show version', use_textfsm=True)
                if not showver.__contains__('Failed'):
                    self.hostname = showver[0]['hostname']
                    self.authorization = True
                self.authentication = True
                self.connectivity = True
                self.con_type = 'TELNET'
            except ssh_exception.NetmikoAuthenticationException:
                try:
                    device['device_type'] = 'cisco_ios_telnet'
                    self.devicetype = 'cisco_ios_telnet'
                    device['secret'] = self.password
                    session = ConnectHandler(**device)
                    showver = session.send_command('show version', use_textfsm=True)
                    if not showver.__contains__('Failed'):
                        self.hostname = showver[0]['hostname']
                        self.authorization = True
                    self.authentication = True
                    self.connectivity = True
                    self.con_type = 'TELNET'
                except ssh_exception.NetmikoAuthenticationException:
                    self.connectivity = True
                    self.exception = 'NetmikoAuthenticationException'
                except ssh_exception.NetmikoTimeoutException:
                    self.exception = 'NetmikoTimeoutException'
                except ConnectionRefusedError:
                    self.exception = 'ConnectionRefusedError'
                except ValueError:
                    self.exception = 'ValueError'
                except TimeoutError:
                    self.exception = 'TimeoutError'
            except ssh_exception.NetmikoTimeoutException:
                self.exception = 'NetmikoTimeoutException'
            except ConnectionRefusedError:
                self.exception = 'ConnectionRefusedError'
            except ValueError:
                self.exception = 'ValueError'
            except TimeoutError:
                self.exception = 'TimeoutError'
        except OSError:
            self.exception = 'OSError'
        return session
