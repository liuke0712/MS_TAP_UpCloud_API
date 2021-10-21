import logging
import logging


class Logs:
    def __init__(self):
        logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    def info_logger(self, content):
        logging.info(content)

    def warning_logger(self, content):
        logging.warning(content)

    def error_logger(self, content):
        logging.error(content)

    def debug_logger(self, content):
        logging.debug(content)
