from common import _get_valid_input


def _invalid_menu_option(items, input_):
    if not input_.isdigit():
        print("    ERROR: That is not a number.")
        return False
    
    if int(input_) > len(items)-1:
        print("    ERROR: That option is not in the list.")
        return False
    
    return True


def _list_menu_options(items):
    for i in range(len(items)):
        print(f"[{i}] {items[i]}")


def menu(items):
    _list_menu_options(items)
    id_ = _get_valid_input(
        ask_txt="Please enter a number to select an option: ",
        err_msg='',
        is_valid_condition=lambda x: _invalid_menu_option(items, x),
        return_type=int
    )
    return items[id_]


if __name__ == "__main__":
    menu(["Burger", "Fries", "Chicken"])