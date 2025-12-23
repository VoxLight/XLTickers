# pypi libs

# project libs
from core.logging_config import setup_logging

# Initialize rotating file logging (logs directory, max 1MB per file, keep 5 backups)
logger = setup_logging(log_dir='./logs', max_bytes=1024*1024, backup_count=5, console_output=False)
logger.debug("Starting XLTickers")


# local libs
from libs.common import _get_valid_input, print_errors, globals_, clear
from libs.opener import get_worksheet
from libs.menu import menu
from libs.cli_adapter import init_config, process_excel_with_callback, print_summary
from core.version import __version__
from core.update_checker import check_and_notify_update


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
                is_valid_condition=lambda x: x in ('Y', 'y')
            )
            wb.save(fp)
            break
        except PermissionError:
            print("\n\nPermissionError:\n    unable to write to the workbook.")
            print("\n    Do you have the workbook open? Please close the workbook before trying to save again.")

def main():
    # Check for updates (non-blocking, silent if no update)
    try:
        check_and_notify_update(__version__, channel='production', interactive=True)
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
    
    # Open the workbook
    ws, wb = get_worksheet()
    print("What action would you like to preform?")
    SCRIPTS[menu(list(SCRIPTS.keys()))](ws)
    save(wb)
    input("Finished. Press enter to continue...")

if __name__ == "__main__":
    main()
    logger.debug("Done")