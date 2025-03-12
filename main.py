# pypi libs

# local libs
import logging
logging.basicConfig(filename='logs.txt', filemode="w", encoding='utf-8', level=logging.DEBUG)
logging.debug("Starting")


# project libs
from libs.common import _get_valid_input, print_errors, globals_
from libs.opener import get_worksheet
from libs.menu import menu


# project scripts
import scripts.price_updater as price_updater
import scripts.alert_updater as alert_updater
SCRIPTS = {
    price_updater.NAME: price_updater.run,
    alert_updater.NAME: alert_updater.run
}

def save(wb):
    fp = globals_.workbook_fp # file path to save to as imported from common
    while 1:
        try:
            _get_valid_input(
                ask_txt="Would you like to save these changes? (Y/n): ",
                err_msg="If you don't want to save, use 'ctrl + c' or close this window.",
                is_valid_condition=lambda x: x == "Y"
            )
            wb.save(fp)
            break
        except PermissionError:
            print("\n\nPermissionError:\n    unable to write to the workbook.")
            print("\n    Do you have the workbook open? Please close the workbook before trying to save again.")

def main():
    # Open the workbook
    ws, wb = get_worksheet()
    print("What action would you like to preform?")
    SCRIPTS[menu(list(SCRIPTS.keys()))](ws)
    print_errors()
    save(wb)
    input("Finished. Press enter to continue...")



if __name__ == "__main__":
    main()
    logging.debug("Done")