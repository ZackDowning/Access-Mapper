import re
from ipaddress import IPv4Network, IPv4Interface
from general import Connection, MultiThread
import time

# TODO: Add menu to just find specific info about device


class Interface:
    """Parses device to find vlan and interface of provided MAC Address"""
    def __init__(self, mac_address, session):
        self.vlan = None
        self.intf = None
        intfs = []
        try:
            show_int_sw = session.send_command('show interface switchport', use_textfsm=True)
            if show_int_sw[0].__contains__('switchport'):

                def int_sw(s_intf):
                    if s_intf['mode'].__contains__('access'):
                        intfs.append(s_intf['interface'])

                MultiThread(int_sw, show_int_sw).mt()
            cdp_nei = session.send_command('show cdp neighbor detail', use_textfsm=True)

            def ap_intf(neighbor):
                if neighbor['capabilities'].__contains__('Trans-Bridge'):
                    full_ap_l_intf = neighbor['local_port']
                    ap_l_intf = str(
                        re.findall(r'\S{2}', full_ap_l_intf)[0]) + str(re.findall(r'\d+\S+', full_ap_l_intf)[0])
                    if all(intf != ap_l_intf for intf in intfs):
                        intfs.append(ap_l_intf)

            MultiThread(ap_intf, cdp_nei).mt()
            show_mac = session.send_command(f'show mac address-table', use_textfsm=True)

            def vlan_intf(mac):
                if type(show_mac) is list:
                    intf = mac['destination_port']
                    mac_intf = str(re.findall(r'\S{2}', intf)[0]) + str(re.findall(r'\d+\S+', intf)[0])
                    if mac['destination_address'] == mac_address and any(x == mac_intf for x in intfs):
                        self.vlan = mac['vlan']
                        self.intf = mac_intf

            MultiThread(vlan_intf, show_mac).mt()
        except IndexError:
            pass


class MACAddress:
    """Parses device to see if it is routing provided IP Addresses to find MAC Address and L3 Interface"""
    def __init__(self, ip_address, session):
        self.gateway_ip = None
        self.mac_address = None
        show_ip_int = session.send_command('show ip interface', use_textfsm=True)

        def gateway(intf):
            for ip_addr, prefix in zip(intf['ipaddr'], intf['mask']):
                intf_ip = f'{ip_addr}/{prefix}'
                intf_network = str(IPv4Interface(intf_ip).network)
                if any(str(host) == ip_address for host in IPv4Network(intf_network).hosts()):
                    self.gateway_ip = ip_addr

        MultiThread(gateway, show_ip_int).mt()
        if self.gateway_ip is not None:
            try:
                self.mac_address = session.send_command(
                    f'show ip arp {ip_address}', use_textfsm=True)[0]['mac']
            except IndexError:
                pass


class IPAddress:
    """Parses device ARP table to find IP address for provided MAC address"""
    def __init__(self, mac_address, session):
        raw_arp_output = session.send_command(f'show ip arp {mac_address}', use_textfsm=True)
        try:
            self.ip_address = raw_arp_output[0]['address']
        except (IndexError, TypeError):
            if raw_arp_output.__contains__(mac_address):
                self.ip_address = raw_arp_output.split('\n')[1].split('  ')[1]
            else:
                self.ip_address = None


class Connectivity:
    def __init__(self, mgmt_ip_list, username, password):
        def check(ip):
            conn = Connection(ip, username, password).check()
            if conn.authorization:
                self.successful_devices.append(
                    {
                        'ip': ip,
                        'hostname': conn.hostname,
                        'con_type': conn.con_type,
                        'device_type': conn.devicetype
                    }
                )
            else:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'exception': conn.exception,
                        'connectivity': conn.connectivity,
                        'authentication': conn.authentication,
                        'authorization': conn.authorization
                    }
                )

        while True:
            self.successful_devices = []
            self.failed_devices = []
            d = MultiThread(check, mgmt_ip_list).mt()
            bug = MultiThread(
                iterable=d.iterable,
                successful_devices=self.successful_devices,
                failed_devices=self.failed_devices
            ).bug()
            if not bug:
                break


class Discovery:
    def __init__(self, query_value, input_type, mgmt_ip_list, username, password):
        self.host_vlan = None
        self.host_mac_address = None
        self.host_ip_address = None
        self.gateway_ip_address = None
        self.connected_device_interface = None
        self.connected_device_mgmt_ip_address = None
        self.connected_device_hostname = None
        self.gateway_mgmt_ip_address = None
        self.gateway_hostname = None
        self.bug = False
        self.discovery_finished = False
        self.successful_cycle_devices = []

        def gateway_query(device):
            ip = device['ip']
            device_type = device['device_type']
            con_type = device['con_type']
            session = Connection(ip, username, password, device_type, con_type).connection()
            if session.session is None:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype,
                        'exception': session.exception
                    }
                )
                self.successful_devices.remove(device)
            else:
                self.successful_cycle_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype
                    }
                )
                mac_addr = MACAddress(self.host_ip_address, session.session)
                if mac_addr.gateway_ip is not None:
                    self.gateway_ip_address = mac_addr.gateway_ip
                    self.host_mac_address = mac_addr.mac_address
                    self.gateway_hostname = device['hostname']
                    self.gateway_mgmt_ip_address = ip
                session.session.disconnect()

        def intf_vlan_query(device):
            ip = device['ip']
            device_type = device['device_type']
            con_type = device['con_type']
            session = Connection(ip, username, password, device_type, con_type).connection()
            if session.session is None:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype,
                        'exception': session.exception
                    }
                )
                self.successful_devices.remove(device)
            else:
                self.successful_cycle_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype
                    }
                )
                intf = Interface(self.host_mac_address, session.session)
                if intf.vlan is not None:
                    self.host_vlan = intf.vlan
                    self.connected_device_interface = intf.intf
                    self.connected_device_hostname = device['hostname']
                    self.connected_device_mgmt_ip_address = ip
                session.session.disconnect()

        def ip_addr_query(device):
            ip = device['ip']
            device_type = device['device_type']
            con_type = device['con_type']
            session = Connection(ip, username, password, device_type, con_type).connection()
            if session.session is None:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype,
                        'exception': session.exception
                    }
                )
                self.successful_devices.remove(device)
            else:
                self.successful_cycle_devices.append(
                    {
                        'ip': ip,
                        'hostname': device['hostname'],
                        'con_type': session.con_type,
                        'device_type': session.devicetype
                    }
                )
                ip_addr = IPAddress(query_value, session.session).ip_address
                if ip_addr is not None:
                    self.host_ip_address = ip_addr
                session.session.disconnect()

        def mt(function):
            while True:
                self.successful_cycle_devices = []
                MultiThread(function, self.successful_devices).mt()
                self.bug = MultiThread(
                    iterable=mgmt_ip_list,
                    successful_devices=self.successful_cycle_devices,
                    failed_devices=self.failed_devices
                ).bug()
                if not self.bug:
                    break

        con_check = Connectivity(mgmt_ip_list, username, password)
        self.successful_devices = con_check.successful_devices
        self.failed_devices = con_check.failed_devices
        while not self.discovery_finished:
            if input_type == 'IP_Address':
                self.host_ip_address = query_value
                if self.host_mac_address is None:
                    time.sleep(5)
                    mt(gateway_query)
                    if self.host_mac_address is None:
                        self.host_mac_address = 'Not Found. Required for VLAN and connected device info.'
                        self.discovery_finished = True
                else:
                    time.sleep(5)
                    mt(intf_vlan_query)
                    self.discovery_finished = True
            if input_type == 'MAC_Address':
                if self.host_ip_address is None:
                    time.sleep(5)
                    mt(ip_addr_query)
                    if self.host_ip_address is None:
                        self.host_ip_address = 'Not Found. Required for discovery.'
                        self.discovery_finished = True
                else:
                    if self.host_mac_address is None:
                        time.sleep(5)
                        mt(gateway_query)
                        # TODO: Update to just use MAC Address from entry
                        if self.host_mac_address is None:
                            self.host_mac_address = 'Not Found. Required for VLAN and connected device info.'
                            self.discovery_finished = True
                    else:
                        time.sleep(5)
                        mt(intf_vlan_query)
                        self.discovery_finished = True
