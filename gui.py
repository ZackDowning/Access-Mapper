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
    return [Sg.InputText(font=font, default_text=str(default_string))]


def gui_password_input(default_string='', font=m_font):
    return [Sg.InputText(password_char='*', font=font, default_text=str(default_string))]


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
        gui_input(),
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
        gui_input(),
        gui_print('Network Password'),
        gui_password_input(''),
        button('Run Discovery')
    ]
    return Sg.Window(window_title, layout, margins=(100, 100))


def w_progress_bar(current_window, length):
    current_window.close()
    layout = [gui_print('Discovery Running'),
              [Sg.ProgressBar(length, orientation='h', size=(20, 20), key='-PROG-')],
              [Sg.Cancel()]
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
        connected_device_mgmt_ip_address):
    current_window.close()
    layout = [
        gui_print(f'Host VLAN: {host_vlan}'),
        gui_print(f'Host MAC Address: {host_mac_address}'),
        gui_print(f'Host IP Address: {host_ip_address}'),
        gui_print(f'Host Gateway IP Address: {gateway_ip_address}'),
        gui_print(f'Upstream Device IP Address: {connected_device_mgmt_ip_address}'),
        gui_print(f'Upstream Device Hostname: {connected_device_hostname}'),
        gui_print(f'Upstream Device Interface: {connected_device_interface}'),
        gui_print(f'Gateway Hostname: {gateway_hostname}'),
        gui_print(f'Gateway Management IP Address: {gateway_mgmt_ip_address}'),
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
