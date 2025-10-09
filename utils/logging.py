import logging, os
_LEVEL=os.getenv('LOG_LEVEL','INFO').upper()
def get_logger(name):
    lg=logging.getLogger(name)
    if not lg.handlers:
        h=logging.StreamHandler()
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s :: %(message)s'))
        lg.addHandler(h)
    lg.setLevel(_LEVEL)
    return lg
