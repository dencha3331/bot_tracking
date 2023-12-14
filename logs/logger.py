import logging
import logging.handlers
import os


class MyLogger:
    """Class logger"""
    def __init__(self, logger_name, log_dir):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # Создаем обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Создаем катологи для логов
        os.makedirs(f"{log_dir}/debug", exist_ok=True)
        os.makedirs(f"{log_dir}/info", exist_ok=True)
        os.makedirs(f"{log_dir}/warning", exist_ok=True)
        os.makedirs(f"{log_dir}/error", exist_ok=True)

        # Создаем и настраиваем обработчики файловых логов
        debug_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(f"{log_dir}/debug", 'debug.log'), when='midnight', backupCount=0)
        debug_handler.suffix = '%Y-%m-%d'
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)

        info_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(f"{log_dir}/info", 'info.log'), when='midnight', backupCount=0)
        info_handler.suffix = '%Y-%m-%d'
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)

        warning_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(f"{log_dir}/warning", 'warning.log'), when='midnight', backupCount=0)
        warning_handler.suffix = '%Y-%m-%d'
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(formatter)

        error_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(f"{log_dir}/error", 'error.log'), when='midnight', backupCount=0)
        warning_handler.suffix = '%Y-%m-%d'
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(formatter)

        # Добавляем обработчики к логгеру
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(info_handler)
        self.logger.addHandler(warning_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)