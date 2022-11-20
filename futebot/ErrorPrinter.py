import traceback

def print_error(e):
    print("".join(traceback.format_exception(None, e, e.__traceback__)))
