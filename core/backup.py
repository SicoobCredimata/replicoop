"""
Módulo de backup do sistema ReplicOOP
"""
import os
import subprocess
import gzip
from datetime import datetime
from typing import Optional, List, Dict
import json

from .config import DatabaseConfig
from .logger import LoggerManager
from .database import DatabaseManager


class BackupError(Exception):
    """Exceção personalizada para erros de backup"""
    pass


class BackupManager:
    """Gerenciador de backups do sistema"""
    
    def __init__(self, db_manager: DatabaseManager, logger: LoggerManager, 
                 backup_path: str):
        """
        Inicializa o gerenciador de backup
        
        Args:
            db_manager (DatabaseManager): Gerenciador de banco de dados
            logger (LoggerManager): Gerenciador de logs
            backup_path (str): Caminho para armazenar backups
        """
        self.db_manager = db_manager
        self.logger = logger
        self.backup_path = backup_path
        os.makedirs(backup_path, exist_ok=True)
    
    def create_full_backup(self, environment: str = "production") -> str:
        """
        Cria um backup completo do banco de dados
        
        Args:
            environment (str): Ambiente do banco de dados
            
        Returns:
            str: Caminho do arquivo de backup criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.db_manager.config.dbname}_{environment}_{timestamp}.sql.gz"
        backup_filepath = os.path.join(self.backup_path, backup_filename)
        
        try:
            self.logger.info(f"Iniciando backup completo do banco {self.db_manager.config.dbname}")
            
            # Comando mysqldump
            mysqldump_cmd = [
                "mysqldump",
                f"--host={self.db_manager.config.host}",
                f"--port={self.db_manager.config.port}",
                f"--user={self.db_manager.config.username}",
                f"--password={self.db_manager.config.password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                "--events",
                "--add-drop-table",
                "--create-options",
                "--disable-keys",
                "--extended-insert",
                "--quick",
                "--lock-tables=false",
                self.db_manager.config.dbname
            ]
            
            # Executa mysqldump e comprime o resultado
            self.logger.debug(f"Executando comando: {' '.join(mysqldump_cmd[:-1])} [senha omitida]")
            
            process = subprocess.Popen(
                mysqldump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Comprime e salva o backup
            with gzip.open(backup_filepath, 'wt', encoding='utf-8') as f:
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise BackupError(f"Erro no mysqldump: {stderr}")
                
                f.write(stdout)
            
            # Cria arquivo de metadados do backup
            self._create_backup_metadata(backup_filepath, environment)
            
            backup_size = os.path.getsize(backup_filepath)
            self.logger.info(f"Backup criado com sucesso: {backup_filename} ({backup_size} bytes)")
            
            return backup_filepath
            
        except subprocess.SubprocessError as e:
            self.logger.error(f"Erro ao executar mysqldump: {e}")
            raise BackupError(f"Falha no comando mysqldump: {e}")
        except Exception as e:
            self.logger.error(f"Erro durante backup: {e}")
            raise BackupError(f"Falha no backup: {e}")
    
    def create_structure_backup(self, tables: Optional[List[str]] = None, 
                              environment: str = "production") -> str:
        """
        Cria um backup apenas da estrutura das tabelas
        
        Args:
            tables (List[str], optional): Lista de tabelas específicas
            environment (str): Ambiente do banco de dados
            
        Returns:
            str: Caminho do arquivo de backup criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.db_manager.config.dbname}_structure_{environment}_{timestamp}.sql"
        backup_filepath = os.path.join(self.backup_path, backup_filename)
        
        try:
            self.logger.info(f"Criando backup de estrutura para {len(tables) if tables else 'todas as'} tabelas")
            
            with open(backup_filepath, 'w', encoding='utf-8') as f:
                # Cabeçalho do backup
                f.write(f"-- Backup de Estrutura - {datetime.now().isoformat()}\n")
                f.write(f"-- Banco: {self.db_manager.config.dbname}\n")
                f.write(f"-- Ambiente: {environment}\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
                
                # Se tabelas não foram especificadas, obtém todas
                if not tables:
                    tables = self.db_manager.get_tables()
                
                for table in tables:
                    try:
                        # Obtém statement CREATE TABLE
                        create_statement = self.db_manager.get_create_table_statement(table)
                        
                        f.write(f"-- Estrutura da tabela {table}\n")
                        f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                        f.write(f"{create_statement};\n\n")
                        
                    except Exception as e:
                        self.logger.warning(f"Erro ao obter estrutura da tabela {table}: {e}")
                        continue
                
                f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            
            # Cria arquivo de metadados
            self._create_backup_metadata(backup_filepath, environment, backup_type="structure")
            
            self.logger.info(f"Backup de estrutura criado: {backup_filename}")
            return backup_filepath
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup de estrutura: {e}")
            raise BackupError(f"Falha no backup de estrutura: {e}")
    
    def _create_backup_metadata(self, backup_filepath: str, environment: str, 
                              backup_type: str = "full") -> None:
        """
        Cria arquivo de metadados para o backup
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            environment (str): Ambiente do backup
            backup_type (str): Tipo do backup (full, structure, etc.)
        """
        metadata = {
            "backup_file": os.path.basename(backup_filepath),
            "backup_path": backup_filepath,
            "database": self.db_manager.config.dbname,
            "environment": environment,
            "backup_type": backup_type,
            "timestamp": datetime.now().isoformat(),
            "size_bytes": os.path.getsize(backup_filepath) if os.path.exists(backup_filepath) else 0,
            "host": self.db_manager.config.host,
            "port": self.db_manager.config.port
        }
        
        metadata_filepath = backup_filepath + ".meta"
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def list_backups(self) -> List[Dict]:
        """
        Lista todos os backups disponíveis
        
        Returns:
            List[Dict]: Lista de informações dos backups
        """
        backups = []
        
        try:
            for filename in os.listdir(self.backup_path):
                if filename.endswith('.meta'):
                    metadata_path = os.path.join(self.backup_path, filename)
                    
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backups.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"Erro ao ler metadados de {filename}: {e}")
            
            # Ordena por timestamp (mais recente primeiro)
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao listar backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, keep_last: int = 10) -> None:
        """
        Remove backups antigos, mantendo apenas os mais recentes
        
        Args:
            keep_last (int): Número de backups mais recentes para manter
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_last:
                self.logger.info(f"Mantendo todos os {len(backups)} backups disponíveis")
                return
            
            backups_to_remove = backups[keep_last:]
            
            for backup in backups_to_remove:
                backup_path = backup.get('backup_path')
                metadata_path = backup_path + '.meta' if backup_path else None
                
                try:
                    if backup_path and os.path.exists(backup_path):
                        os.remove(backup_path)
                        self.logger.debug(f"Backup removido: {backup.get('backup_file')}")
                    
                    if metadata_path and os.path.exists(metadata_path):
                        os.remove(metadata_path)
                        self.logger.debug(f"Metadados removidos: {os.path.basename(metadata_path)}")
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao remover backup {backup.get('backup_file')}: {e}")
            
            self.logger.info(f"Limpeza de backups concluída: {len(backups_to_remove)} backups removidos")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de backups: {e}")
    
    def restore_backup(self, backup_filepath: str) -> None:
        """
        Restaura um backup do banco de dados
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
        """
        if not os.path.exists(backup_filepath):
            raise BackupError(f"Arquivo de backup não encontrado: {backup_filepath}")
        
        try:
            self.logger.info(f"Iniciando restauração do backup: {os.path.basename(backup_filepath)}")
            
            # Comando mysql para restaurar
            mysql_cmd = [
                "mysql",
                f"--host={self.db_manager.config.host}",
                f"--port={self.db_manager.config.port}",
                f"--user={self.db_manager.config.username}",
                f"--password={self.db_manager.config.password}",
                self.db_manager.config.dbname
            ]
            
            # Se o arquivo estiver comprimido
            if backup_filepath.endswith('.gz'):
                with gzip.open(backup_filepath, 'rt', encoding='utf-8') as f:
                    process = subprocess.Popen(
                        mysql_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    stdout, stderr = process.communicate(input=f.read())
            else:
                with open(backup_filepath, 'r', encoding='utf-8') as f:
                    process = subprocess.Popen(
                        mysql_cmd,
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise BackupError(f"Erro na restauração: {stderr}")
            
            self.logger.info("Backup restaurado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            raise BackupError(f"Falha na restauração: {e}")