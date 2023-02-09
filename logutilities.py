import logging


class LogUtilities:

    def __init__(self):
        format = "%(asctime)s: %(message)s"
        '''这里设置打印级别为INFO及以上'''
        logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    @staticmethod
    def debug(msg):
        logging.debug("-DEBUG-" + msg)

    @staticmethod
    def info(msg):
        logging.info("-INFO-" + msg)

    @staticmethod
    def warning(msg):
        logging.warning("-WARNING" + msg)

    @staticmethod
    def critical(msg):
        logging.critical("-CRITICAL-" + msg)

    @staticmethod
    def error(msg):
        logging.error("-ERROR-" + msg)
