from libs.common import globals_


def _err (ticker, cell):
    globals_.add_error(ticker, cell.row)
    
def _cols(config_): # used for formatting the columns for the name
    return ", ".join(list(config_.values()))