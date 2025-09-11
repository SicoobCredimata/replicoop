"""
Módulo de configuração do sistema ReplicOOP
"""
import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuração de conexão com banco de dados"""
    host: str
    port: int
    username: str
    password: str
    dbname: str
    charset: str = "utf8"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'host': self.host,
            'port': self.port,
            'user': self.username,
            'password': self.password,
            'database': self.dbname,
            'charset': self.charset
        }


class ConfigManager:
    """Gerenciador de configurações do sistema"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa o gerenciador de configurações
        
        Args:
            config_path (str): Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Carrega as configurações do arquivo JSON"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao decodificar arquivo de configuração: {e}")
        except Exception as e:
            raise Exception(f"Erro ao carregar configurações: {e}")
    
    def get_database_config(self, environment: str) -> DatabaseConfig:
        """
        Obtém configuração do banco de dados para um ambiente específico
        
        Args:
            environment (str): Nome do ambiente (production, sandbox, etc.)
            
        Returns:
            DatabaseConfig: Configuração do banco de dados
        """
        if environment not in self._config:
            raise ValueError(f"Ambiente '{environment}' não encontrado na configuração")
        
        env_config = self._config[environment]
        return DatabaseConfig(
            host=env_config['host'],
            port=env_config['port'],
            username=env_config['username'],
            password=env_config['password'],
            dbname=env_config['dbname'],
            charset=env_config.get('charset', 'utf8')
        )
    
    def get_maintain_tables(self) -> List[str]:
        """
        Obtém lista de tabelas para manter/replicar
        
        Returns:
            List[str]: Lista de nomes das tabelas
        """
        return self._config.get('maintain', [])
    
    def get_backup_path(self) -> str:
        """
        Obtém o caminho para armazenamento de backups
        
        Returns:
            str: Caminho do diretório de backups
        """
        backup_path = os.path.join(os.getcwd(), 'backups')
        os.makedirs(backup_path, exist_ok=True)
        return backup_path
    
    def get_logs_path(self) -> str:
        """
        Obtém o caminho para armazenamento de logs
        
        Returns:
            str: Caminho do diretório de logs
        """
        logs_path = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_path, exist_ok=True)
        return logs_path