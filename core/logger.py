"""
Módulo de logging do sistema ReplicOOP
"""
import logging
import os
from datetime import datetime
from typing import Optional
from colorama import Fore, Style, init

# Inicializa colorama para Windows
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Formatador colorido para logs no console"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


class LoggerManager:
    """Gerenciador de logs do sistema"""
    
    def __init__(self, name: str = "ReplicOOP", logs_path: Optional[str] = None):
        """
        Inicializa o gerenciador de logs
        
        Args:
            name (str): Nome do logger
            logs_path (str, optional): Caminho para salvar arquivos de log
        """
        self.name = name
        self.logs_path = logs_path or os.path.join(os.getcwd(), 'logs')
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura e retorna o logger"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Remove handlers existentes para evitar duplicação
        logger.handlers.clear()
        
        # Handler para console com cores
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Handler para arquivo
        if self.logs_path:
            os.makedirs(self.logs_path, exist_ok=True)
            log_filename = f"replicoop_{datetime.now().strftime('%Y%m%d')}.log"
            log_filepath = os.path.join(self.logs_path, log_filename)
            
            file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, message: str) -> None:
        """Log de debug"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log de informação"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log de aviso"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log de erro"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log crítico"""
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        """Log de exceção com traceback"""
        self.logger.exception(message)