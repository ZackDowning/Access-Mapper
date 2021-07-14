import os
import sys
import re
from concurrent.futures import ThreadPoolExecutor, wait
from netmiko import ConnectHandler, ssh_exception, SSHDetect
from address_validator import ipv4
from icmplib import ping

# Checks for TextFSM templates within single file bundle if code is frozen
if getattr(sys, 'frozen', False):
    os.environ['NET_TEXTFSM'] = sys._MEIPASS
else:
    os.environ['NET_TEXTFSM'] = './templates'


def mac_address_formatter(mac_address):
    """Formats MAC address into Cisco MAC Address format and returns string"""
    if '.' not in mac_address:
        x = mac_address.replace(':', '').replace('-', '')
        return f'{x[0:4]}.{x[4:8]}.{x[8:12]}'
    else:
        return mac_address


def interface_formatter(interface):
    """Returns formatted Cisco interface string into abbreviated Cisco interface for continuity\n
    Example:\n
    Input: GigabitEthernet1/0/1\n
    Output: Gi1/0/1"""
    return str(re.findall(r'\S{2}', interface)[0]) + str(re.findall(r'\d+\S+', interface)[0])


class MgmtIPAddresses:
    """Input .txt file location containing list of management IP addresses"""
    def __init__(self, mgmt_file_location):
        self.mgmt_file_location = mgmt_file_location
        self.mgmt_ips = []
        """Formatted set of validated IP addresses"""
        self.invalid_line_nums = []
        """Set of invalid line numbers corresponding to line number of management file input"""
        self.invalid_ip_addresses = []
        """Set of invalid IP addresses"""
        self.validate = True
        """Bool of management IP address file input validation"""
        with open(self.mgmt_file_location) as file:
            for idx, address in enumerate(file):
                ip_address = str(address).strip('\n')
                if ipv4(ip_address) is False:
                    self.invalid_line_nums.append(str(idx + 1))
                    self.invalid_ip_addresses.append(str(address))
                    self.validate = False
                    """Bool of management IP address file input validation"""
                else:
                    self.mgmt_ips.append(ip_address)


def reachability(ip_address, count=4):
    """Returns bool if host is reachable with default count of 4 pings"""
    return ping(ip_address, privileged=False, count=count).is_alive


class Connection:
    """SSH or TELNET Connection Initiator"""
    def __init__(self, ip_address, username, password, devicetype='autodetect', con_type=None):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = ''
        self.devicetype = devicetype
        self.con_type = con_type
        self.exception = 'None'
        self.authentication = False
        self.authorization = False
        self.connectivity = False
        self.session = None
        self.device = {
            'device_type': self.devicetype,
            'ip': ip_address,
            'username': username,
            'password': password
        }

    def check(self):
        """Base connectivity check method of device returning updated self attributes:\n
        devicetype\n
        hostname\n
        con_type\n
        exception\n
        authentication\n
        authorization\n
        connectivity"""
        if reachability(self.ip_address):
            try:
                try:
                    autodetect = SSHDetect(**self.device).autodetect()
                    self.device['device_type'] = autodetect
                    self.devicetype = autodetect
                    self.session = ConnectHandler(**self.device)
                except ValueError:
                    try:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        self.session = ConnectHandler(**self.device)
                    except ValueError:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        self.session = ConnectHandler(**self.device)
                showver = self.session.send_command('show version', use_textfsm=True)
                if not showver.__contains__('Failed'):
                    self.hostname = showver[0]['hostname']
                    self.authorization = True
                self.authentication = True
                self.connectivity = True
                self.con_type = 'SSH'
            except (ConnectionRefusedError, ValueError, ssh_exception.NetmikoAuthenticationException,
                    ssh_exception.NetmikoTimeoutException):
                try:
                    try:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        self.session = ConnectHandler(**self.device)
                        showver = self.session.send_command('show version', use_textfsm=True)
                        if not showver.__contains__('Failed'):
                            self.hostname = showver[0]['hostname']
                            self.authorization = True
                        self.authentication = True
                        self.connectivity = True
                        self.con_type = 'TELNET'
                    except ssh_exception.NetmikoAuthenticationException:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        self.session = ConnectHandler(**self.device)
                        showver = self.session.send_command('show version', use_textfsm=True)
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
            except OSError:
                self.exception = 'OSError'
            if self.session is not None:
                self.session.disconnect()
        else:
            self.exception = 'NoPingEcho'
        return self

    def connection(self):
        """Base connection method\n
        Should only use self attributes:\n
        session\n
        exception"""
        if reachability(self.ip_address):
            try:
                if self.con_type == 'TELNET':
                    self.device['secret'] = self.password
                    self.session = ConnectHandler(**self.device)
                else:
                    self.session = ConnectHandler(**self.device)
            except ConnectionRefusedError:
                self.exception = 'ConnectionRefusedError'
            except ssh_exception.NetmikoAuthenticationException:
                self.exception = 'NetmikoAuthenticationException'
            except ssh_exception.NetmikoTimeoutException:
                self.exception = 'NetmikoTimeoutException'
            except ValueError:
                self.exception = 'ValueError'
            except TimeoutError:
                self.exception = 'TimeoutError'
            except OSError:
                self.exception = 'OSError'
        else:
            self.exception = 'NoPingEcho'
        return self


class MultiThread:
    """Multithread Initiator"""
    def __init__(self, function=None, iterable=None, successful_devices=None, failed_devices=None, threads=50):
        self.successful_devices = successful_devices
        self.failed_devices = failed_devices
        self.iterable = iterable
        self.threads = threads
        self.function = function

    def mt(self):
        """Executes multithreading on provided function and iterable"""
        executor = ThreadPoolExecutor(self.threads)
        futures = [executor.submit(self.function, val) for val in self.iterable]
        wait(futures, timeout=None)
        return self

    def bug(self):
        """Returns bool if Windows PyInstaller bug is present with provided lists for successful and failed devices"""
        successful = len(self.successful_devices)
        failed = len(self.failed_devices)
        if (successful + failed) == len(self.iterable):
            return False
        else:
            return True
