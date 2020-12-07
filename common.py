import os

def clear():
    os.system('cls')

def _get_valid_input(err_msg, is_valid_condition, ask_txt, return_type=None):
    while not is_valid_condition(txt := input(ask_txt)):
        print(err_msg)
        
    if return_type:
        return return_type(txt)
    
    return txt
