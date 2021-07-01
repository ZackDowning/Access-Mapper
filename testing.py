# # from getpass import getpass
# # from gui import (
# #     w_main, w_finished_discovery)
# # from discovery import Discovery
# # from general import MgmtIPAddresses
# #
# # import PySimpleGUI as Sg
# #
# # if __name__ == '__main__':
# #     username = input('Username: ')
# #     password = getpass('Password: ')
# #     current_window = w_main()
# #     discovery_finished = False
# #     d = None
# #     while True:
# #         event, values = current_window.read()
# #         if event == 'Check File':
# #             Sg.user_settings_set_entry('-filename-', values['file'])
# #             mgmt_file_location = values['file']
# #             mgmt_file = MgmtIPAddresses(mgmt_file_location).mgmt_ips
# #             query_value = '10.39.10.145'
# #
# #         if discovery_finished:
# #             current_window = w_finished_discovery(
# #                 current_window, d.host_mac_address, d.host_ip_address, d.gateway_ip_address, d.gateway_hostname,
# #                 d.gateway_mgmt_ip_address, d.host_vlan, d.connected_device_interface, d.connected_device_hostname,
# #                 d.connected_device_mgmt_ip_address
# #             )
# #         if event == Sg.WIN_CLOSED:
# #             break
# #
# #     current_window.close()
from discovery import MACAddress, IPAddress, Interface
from general import Connection, MultiThread, MgmtIPAddresses
from getpass import getpass
input_type = 'IP_Address'
query_value = '10.39.10.145'
username = input('Username')
password = getpass('Password')
host_mac_address = None
gateway_ip_address = None
host_ip_address = None
gateway_hostname = None
gateway_mgmt_ip_address = None
host_vlan = None
connected_device_interface = None
connected_device_hostname = None
connected_device_mgmt_ip_address = None
successful_devices = []
failed_devices = []
mgmt_ip_list = MgmtIPAddresses('/Users/zack.downing/Downloads/NSBB MGMT.txt').mgmt_ips
bug = False


# def mt(ip, index):
def mt(ip):
    global host_mac_address
    global gateway_ip_address
    global gateway_hostname
    global gateway_mgmt_ip_address
    global host_ip_address
    global host_vlan
    global connected_device_mgmt_ip_address
    global connected_device_hostname
    global connected_device_interface
    global successful_devices
    global failed_devices
    # print('testing')
    # if index == 0:
    #     print('1')
    # current_window = w_running_discovery(current_window)
    if bug:
        print('2')
        # current_window = w_windows_bug(current_window)
    print(ip)
    conn = Connection(ip, username, password)
    session = conn.session
    if input_type == 'IP_Address':
        if host_mac_address is None:
            mac_addr = MACAddress(query_value, session)
            if mac_addr.l3_intf is not None:
                gateway_ip_address = mac_addr.l3_intf
                host_mac_address = mac_addr.mac_address
                host_ip_address = query_value
                gateway_hostname = conn.hostname
                gateway_mgmt_ip_address = ip
        else:
            if host_vlan is None:
                intf = Interface(host_mac_address, session)
                if intf.vlan is not None:
                    host_vlan = intf.vlan
                    connected_device_interface = intf.intf
                    connected_device_hostname = conn.hostname
                    connected_device_mgmt_ip_address = ip
    if input_type == 'MAC_Address':
        if host_ip_address is None:
            ip_addr = IPAddress(query_value, session).ip_address
            if ip_addr is not None:
                host_ip_address = ip_addr
        else:
            if host_mac_address is None:
                mac_addr = MACAddress(host_ip_address, session)
                if mac_addr.l3_intf is not None:
                    gateway_ip_address = mac_addr.l3_intf
                    host_mac_address = mac_addr.mac_address
                    gateway_hostname = conn.hostname
                    gateway_mgmt_ip_address = ip
            else:
                intf = Interface(host_mac_address, session)
                if intf.vlan is not None:
                    host_vlan = intf.vlan
                    connected_device_interface = intf.intf
                    connected_device_hostname = conn.hostname
                    connected_device_mgmt_ip_address = ip
    if conn.authorization:
        successful_devices.append(ip)
    else:
        # TODO: Output failed devices to list of dictionaries with more device details
        failed_devices.append(ip)


while True:
    successful_devices = []
    failed_devices = []
    d = MultiThread(mt, mgmt_ip_list).mt()
    print(len(successful_devices))
    print(len(failed_devices))
    print(len(mgmt_ip_list))
    bug = MultiThread(
        iterable=d.iterable,
        successful_devices=successful_devices,
        failed_devices=failed_devices
    ).bug()
    if not bug:
        break
