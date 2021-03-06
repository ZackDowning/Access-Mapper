import PySimpleGUI as Sg

f = {
    'font': 'Helvetica',
    'size': {
        'small': '12',
        'medium': '14',
        'large': '16'
    }}
s_font = f'{f["font"]} {f["size"]["small"]}'
m_font = f'{f["font"]} {f["size"]["medium"]}'
l_font = f'{f["font"]} {f["size"]["large"]}'
window_title = 'Access Mapper'


def gui_print(string, font=m_font):
    return [Sg.Text(str(string), font=font)]


def gui_print_box(string, font=m_font, size=(20, 100)):
    return [Sg.Multiline(str(string), font=font, size=size)]


def gui_input(default_string='', font=m_font):
    return [Sg.InputText(str(default_string), font=font)]


def gui_user_input(font=m_font):
    return [Sg.Input(Sg.user_settings_get_entry('-username-', ''), key='user', font=font)]


def gui_password_input(default_string='', font=m_font):
    return [Sg.InputText(str(default_string), key='pass', password_char='*', font=font)]


def button(string, font=m_font):
    return [Sg.Button(str(string), font=font, bind_return_key=True)]


def dropdown(input_list, font=m_font):
    return [Sg.Combo(input_list, font=font, bind_return_key=True)]


def file_browse_botton(string, font=m_font):
    return [
        Sg.Input(Sg.user_settings_get_entry('-filename-', ''), key='file'),
        Sg.FileBrowse(str(string), initial_folder='./', font=font)]


def w_main(current_window=None):
    """Main / Home Window"""
    if current_window is not None:
        current_window.close()
    layout = [
        gui_print('Select file containing switch management IP addresses'),
        file_browse_botton('Browse'),
        button('Check File')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_file_not_found(current_window):
    """File Not Found Window and Retry"""
    current_window.close()
    layout = [
        gui_print('File or directory not found.'),
        gui_print('Select file containing switch management IP addresses'),
        file_browse_botton('Browse'),
        button('Retry')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_invalid_file_entry(current_window, mgmt_file):
    """Invalid File Entry Window and Retry"""
    invalid_lines = 'Line    | Value\n'
    line_nums = mgmt_file.invalid_line_nums
    ip_addresses = mgmt_file.invalid_ip_addresses
    for (line_n, ip_addr) in zip(
            line_nums, ip_addresses):
        blank_space = ''
        for num1 in range(0, 10 - len(line_n)):
            blank_space += ' '
        invalid_lines += f'{line_n}{blank_space}  {ip_addr}'
    current_window.close()
    layout = [
        gui_print('Invalid File Entries'),
        gui_print_box(invalid_lines, size=(30, 15)),
        gui_print('Select file containing switch management IP addresses'),
        file_browse_botton('Browse'),
        button('Retry')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_function_selection(current_window):
    current_window.close()
    layout = [
        gui_print('Tool Selection'),
        button('Endpoint Discovery'),
        button('Endpoint Provisioning')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_discovery_query(current_window):
    """Discovery Query Window"""
    current_window.close()
    layout = [
        gui_print('Enter IP Address or MAC Address of device to find details'),
        gui_input(),
        gui_print('Network Username'),
        gui_user_input(),
        gui_print('Network Password'),
        gui_password_input(''),
        button('Run Discovery')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_invalid_discovery_query(current_window):
    """Discovery Query Window"""
    current_window.close()
    layout = [
        gui_print('Invalid Discovery Query Value. Either invalid MAC Address or invalid IP Address'),
        gui_print('Enter IP Address or MAC Address of device to find details'),
        gui_input(),
        gui_print('Network Username'),
        gui_user_input(),
        gui_print('Network Password'),
        gui_password_input(''),
        button('Run Discovery')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_progress_bar(length):
    layout = [gui_print('Discovery Running'),
              [Sg.ProgressBar(length, orientation='h', size=(20, 20), key='-PROG-')]
              ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_finished_discovery(
        current_window,
        host_mac_address,
        host_ip_address,
        gateway_ip_address,
        gateway_hostname,
        gateway_mgmt_ip_address,
        host_vlan,
        connected_device_interface,
        connected_device_hostname,
        connected_device_mgmt_ip_address,
        subnet_mask,
        network):
    current_window.close()
    layout = [
        gui_print('Host Information', l_font),
        gui_print(f'VLAN: {host_vlan}'),
        gui_print(f'MAC Address: {host_mac_address}'),
        gui_print(f'IP Address: {host_ip_address}'),
        gui_print(f'Subnet Mask: {subnet_mask}'),
        gui_print(f'Gateway IP Address: {gateway_ip_address}'),
        gui_print(f'Network: {network}'),
        gui_print(f'Infrastructure Information', l_font),
        gui_print(f'Switch Management IP Address: {connected_device_mgmt_ip_address}'),
        gui_print(f'Switch Hostname: {connected_device_hostname}'),
        gui_print(f'Switch Interface: {connected_device_interface}'),
        gui_print(f'Router Hostname: {gateway_hostname}'),
        gui_print(f'Router Management IP Address: {gateway_mgmt_ip_address}'),
        button('Main Page'),
        button('Function Selection')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))

# def w_template(current_window, mgmt_file):
#     """Template Window"""
#     current_window.close()
#     layout = [
#         gui_print('Invalid File Entries'),
#         gui_print_box(invalid_lines, size=(30, 15)),
#         gui_print('Select file containing switch management IP addresses'),
#         file_browse_botton('Browse'),
#         button('Retry')
#     ]
#     return Sg.Window(window_title, layout, margins=(100, 100))
