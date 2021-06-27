# from gui import gui_print, gui_input, gui_password_input, dropdown, button, file_browse_botton
# import PySimpleGUI as Sg
#
# if __name__ == '__main__':
#     layout1 = [
#         gui_print('IP Address'),
#         gui_input(),
#         gui_print('Username'),
#         gui_input(),
#         gui_print('Password'),
#         gui_password_input(),
#         button('Enter'),
#         gui_print('Select File'),
#         file_browse_botton('Browse')
#     ]
#     window1 = Sg.Window('Access Mapper', layout1, margins=(100, 100))
#     current_window = window1
#     while True:
#         event, values = current_window.read()
#         if event == 'Enter':
#             current_window.close()
#             file = open(values[3]).readlines()
#             layout2 = [
#                 [Sg.Multiline(f'{file}', font='Helvetica 14', size=(20, 10))],
#                 [Sg.InputText(font='Helvetica 14')],
#                 [Sg.Button('Reset', font='Helvetica 14', bind_return_key=True)]
#             ]
#             current_window = Sg.Window('Access Mapper', layout2, margins=(100, 100))
#         if event == 'Reset':
#             current_window.close()
#             layout1 = [
#                 gui_print('IP Address'),
#                 gui_input(),
#                 gui_print('Username'),
#                 gui_input(),
#                 gui_print('Password'),
#                 gui_password_input(),
#                 button('Enter'),
#             ]
#             current_window = Sg.Window('Access Mapper', layout1, margins=(100, 100))
#         if event == Sg.WIN_CLOSED:
#             break
#
#     current_window.close()

testing = {
    'test1': ['1', '2', '3'],
    'test2': ['a', 'b', 'c']
}

test = ''
for (test1, test2) in zip(testing['test1'], testing['test2']):
    test += f'{test1} {test2}\n'

print(test)
