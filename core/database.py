"""
Módulo de conexão e operações com banco de dados MySQL
"""
import mysql.connector
from mysql.connector import Error as MySQLError
import pymysql
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import time

from .config import DatabaseConfig
from .logger import LoggerManager


class DatabaseConnectionError(Exception):
    """Exceção personalizada para erros de conexão com banco de dados"""
    pass


class DatabaseOperationError(Exception):
    """Exceção personalizada para erros em operações de banco de dados"""
    pass


class DatabaseManager:
    """Gerenciador de conexões e operações com banco de dados MySQL"""
    
    def __init__(self, config: DatabaseConfig, logger: LoggerManager):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            config (DatabaseConfig): Configuração de conexão
            logger (LoggerManager): Gerenciador de logs
        """
        self.config = config
        self.logger = logger
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para gerenciar conexões com banco de dados
        
        Yields:
            mysql.connector.connection: Conexão com o banco de dados
        """
        connection = None
        try:
            connection = self._create_connection()
            yield connection
        except MySQLError as e:
            self.logger.error(f"Erro na conexão com banco de dados: {e}")
            raise DatabaseConnectionError(f"Erro na conexão: {e}")
        finally:
            if connection and connection.is_connected():
                connection.close()
                self.logger.debug("Conexão com banco de dados fechada")
    
    def _create_connection(self) -> mysql.connector.connection:
        """
        Cria uma nova conexão com o banco de dados
        
        Returns:
            mysql.connector.connection: Nova conexão
        """
        try:
            connection = mysql.connector.connect(**self.config.to_dict())
            self.logger.debug(f"Conexão estabelecida com {self.config.host}:{self.config.port}")
            return connection
        except MySQLError as e:
            self.logger.error(f"Falha ao conectar com banco de dados: {e}")
            raise DatabaseConnectionError(f"Falha na conexão: {e}")
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o banco de dados
        
        Returns:
            bool: True se a conexão for bem-sucedida, False caso contrário
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                self.logger.info("Teste de conexão bem-sucedido")
                return True
        except Exception as e:
            self.logger.error(f"Teste de conexão falhou: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_results: bool = True) -> Optional[List[Tuple]]:
        """
        Executa uma query no banco de dados
        
        Args:
            query (str): Query SQL a ser executada
            params (Tuple, optional): Parâmetros para a query
            fetch_results (bool): Se deve retornar os resultados da query
            
        Returns:
            Optional[List[Tuple]]: Resultados da query se fetch_results=True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_results:
                    results = cursor.fetchall()
                    self.logger.debug(f"Query executada com {len(results)} resultados")
                    return results
                else:
                    conn.commit()
                    self.logger.debug(f"Query executada, {cursor.rowcount} linhas afetadas")
                    return None
                    
        except MySQLError as e:
            self.logger.error(f"Erro ao executar query: {e}")
            raise DatabaseOperationError(f"Erro na execução: {e}")
    
    def execute_many_query(self, query: str, params_list: List[Tuple]) -> None:
        """
        Executa uma query com múltiplos conjuntos de parâmetros (batch insert)
        
        Args:
            query (str): Query SQL a ser executada
            params_list (List[Tuple]): Lista de parâmetros para cada execução
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                self.logger.debug(f"Batch query executada: {cursor.rowcount} linhas afetadas")
                    
        except MySQLError as e:
            self.logger.error(f"Erro ao executar batch query: {e}")
            raise DatabaseOperationError(f"Erro na execução em batch: {e}")
    
    def set_zero_preserve_mode(self, enable: bool = True) -> None:
        """
        Configura o modo SQL para preservar valores 0 em colunas AUTO_INCREMENT
        
        Args:
            enable (bool): Se True, permite inserção de valor 0. Se False, restaura comportamento padrão.
        """
        try:
            if enable:
                # Configurações específicas para preservar IDs com valor 0
                self.execute_query("SET SESSION sql_mode = ''", fetch_results=False)  # Remove todas as restrições
                self.execute_query("SET SESSION SQL_MODE = 'ALLOW_INVALID_DATES,NO_ENGINE_SUBSTITUTION'", fetch_results=False)
                self.execute_query("SET @@SESSION.sql_mode = 'NO_ENGINE_SUBSTITUTION'", fetch_results=False)
                # Força o comportamento desejado em AUTO_INCREMENT
                self.execute_query("SET @@auto_increment_offset = 1", fetch_results=False)
                self.execute_query("SET @@auto_increment_increment = 1", fetch_results=False)
                self.logger.debug("Modo SQL configurado para preservar valores 0 em AUTO_INCREMENT")
            else:
                # Restaura modo padrão do MySQL/MariaDB
                self.execute_query("SET SESSION sql_mode = DEFAULT", fetch_results=False)
                self.logger.debug("Modo SQL restaurado para comportamento padrão")
        except Exception as e:
            self.logger.warning(f"Erro ao configurar modo SQL: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_results: bool = True) -> Optional[List[Dict]]:
        """
        Executa uma query no banco de dados e retorna resultados como dicionários
        
        Args:
            query (str): Query SQL a ser executada
            params (Tuple, optional): Parâmetros para a query
            fetch_results (bool): Se deve retornar os resultados da query
            
        Returns:
            Optional[List[Dict]]: Resultados da query como dicionários se fetch_results=True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)  # Retorna dicionários
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_results:
                    results = cursor.fetchall()
                    self.logger.debug(f"Query executada com {len(results)} resultados")
                    return results
                else:
                    conn.commit()
                    self.logger.debug(f"Query executada, {cursor.rowcount} linhas afetadas")
                    return None
                    
        except MySQLError as e:
            self.logger.error(f"Erro ao executar query: {e}")
            raise DatabaseOperationError(f"Erro na execução: {e}")
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """
        Obtém informações das colunas de uma tabela
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            List[Dict[str, str]]: Lista com informações das colunas
        """
        query = f"DESCRIBE `{table_name}`"
        results = self.execute_query(query)
        
        if not results:
            return []
        
        columns = []
        for row in results:
            columns.append({
                'name': row['Field'],
                'type': row['Type'],
                'null': row['Null'],
                'key': row['Key'],
                'default': row['Default'],
                'extra': row['Extra']
            })
        
        return columns
    
    def get_tables(self) -> List[str]:
        """
        Obtém lista de todas as tabelas do banco de dados
        
        Returns:
            List[str]: Lista com nomes das tabelas
        """
        try:
            query = "SHOW TABLES"
            results = self.execute_query(query)
            
            if not results:
                return []
            
            # Trata diferentes formatos de resultado
            tables = []
            for row in results:
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    # Formato tupla/lista: ('table_name',)
                    tables.append(row[0])
                elif isinstance(row, dict):
                    # Formato dicionário: {'Tables_in_dbname': 'table_name'}
                    # Pega o primeiro (e geralmente único) valor do dict
                    table_name = list(row.values())[0]
                    tables.append(table_name)
                elif isinstance(row, str):
                    # Formato string direta
                    tables.append(row)
                else:
                    self.logger.warning(f"Formato inesperado na resposta SHOW TABLES: {type(row)} - {row}")
            
            self.logger.debug(f"Encontradas {len(tables)} tabelas: {tables}")
            return tables
            
        except Exception as e:
            self.logger.error(f"Erro ao obter lista de tabelas: {e}")
            # Tenta método alternativo
            try:
                query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                """
                results = self.execute_query(query, (self.config.dbname,))
                return [table[0] for table in results] if results else []
            except Exception as e2:
                self.logger.error(f"Erro no método alternativo: {e2}")
                return []
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica se uma tabela existe no banco de dados
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            bool: True se a tabela existe, False caso contrário
        """
        try:
            query = """
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
            """
            results = self.execute_query(query, (self.config.dbname, table_name))
            
            if results and len(results) > 0:
                count = results[0]
                # Trata diferentes formatos de resultado
                if isinstance(count, (list, tuple)):
                    exists = count[0] > 0
                elif isinstance(count, dict):
                    exists = list(count.values())[0] > 0
                else:
                    exists = count > 0
                
                self.logger.debug(f"Tabela '{table_name}' {'existe' if exists else 'não existe'}")
                return exists
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar existência da tabela {table_name}: {e}")
            # Método alternativo: tenta listar tabelas
            try:
                tables = self.get_tables()
                exists = table_name in tables
                self.logger.debug(f"Verificação alternativa: tabela '{table_name}' {'existe' if exists else 'não existe'}")
                return exists
            except Exception as e2:
                self.logger.error(f"Erro no método alternativo de verificação: {e2}")
                return False
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Obtém estrutura de uma tabela específica
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            List[Dict[str, Any]]: Estrutura da tabela
        """
        query = f"DESCRIBE `{table_name}`"
        results = self.execute_query(query)
        
        if not results:
            return []
        
        columns = []
        for row in results:
            if isinstance(row, (list, tuple)) and len(row) >= 6:
                # Formato tupla: (field, type, null, key, default, extra)
                columns.append({
                    'Field': row[0],
                    'Type': row[1],
                    'Null': row[2],
                    'Key': row[3],
                    'Default': row[4],
                    'Extra': row[5]
                })
            elif isinstance(row, dict):
                # Formato dict: {'Field': 'id', 'Type': 'int', ...}
                columns.append(row)
        
        return columns
    
    def get_create_table_statement(self, table_name: str) -> str:
        """
        Obtém o statement CREATE TABLE para uma tabela
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            str: Statement CREATE TABLE
        """
        query = f"SHOW CREATE TABLE `{table_name}`"
        results = self.execute_query(query)
        
        if results and len(results) > 0:
            row = results[0]
            # Trata diferentes formatos de retorno
            if isinstance(row, (list, tuple)) and len(row) > 1:
                # Formato tupla: ('table_name', 'CREATE TABLE ...')
                return row[1]
            elif isinstance(row, dict):
                # Formato dicionário: {'Table': 'table_name', 'Create Table': 'CREATE TABLE ...'}
                create_key = None
                for key in row.keys():
                    if 'create' in key.lower() and 'table' in key.lower():
                        create_key = key
                        break
                if create_key:
                    return row[create_key]
                else:
                    # Se não encontrar, pega o segundo valor
                    values = list(row.values())
                    if len(values) > 1:
                        return values[1]
            
        raise DatabaseOperationError(f"Não foi possível obter CREATE TABLE para {table_name}")
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """
        Obtém as chaves estrangeiras de uma tabela
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            List[Dict[str, str]]: Lista de chaves estrangeiras
        """
        query = """
        SELECT 
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        
        results = self.execute_query(query, (self.config.dbname, table_name))
        
        foreign_keys = []
        for row in results:
            foreign_keys.append({
                'constraint_name': row[0],
                'column_name': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            })
        
        return foreign_keys
    
    def disable_foreign_key_checks(self) -> None:
        """Desabilita verificação de chaves estrangeiras"""
        self.execute_query("SET FOREIGN_KEY_CHECKS = 0", fetch_results=False)
        self.logger.debug("Verificação de chaves estrangeiras desabilitada")
    
    def enable_foreign_key_checks(self) -> None:
        """Habilita verificação de chaves estrangeiras"""
        self.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch_results=False)
        self.logger.debug("Verificação de chaves estrangeiras habilitada")
    
    def get_table_data(self, table_name: str, limit: Optional[int] = None) -> List[Tuple]:
        """
        Obtém dados de uma tabela
        
        Args:
            table_name (str): Nome da tabela
            limit (int, optional): Limite de registros
            
        Returns:
            List[Tuple]: Dados da tabela
        """
        query = f"SELECT * FROM `{table_name}`"
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query) or []
    
    def drop_table_if_exists(self, table_name: str) -> None:
        """
        Remove uma tabela se ela existir, desabilitando temporariamente as FKs na mesma conexão
        
        Args:
            table_name (str): Nome da tabela
        """
        try:
            # Executa comandos na mesma conexão
            commands = [
                "SET FOREIGN_KEY_CHECKS = 0",
                f"DROP TABLE IF EXISTS `{table_name}`",
                "SET FOREIGN_KEY_CHECKS = 1"
            ]
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for command in commands:
                    try:
                        cursor.execute(command)
                        self.logger.debug(f"Executado: {command}")
                    except Exception as cmd_error:
                        self.logger.debug(f"Erro no comando '{command}': {cmd_error}")
                        if "DROP TABLE" in command:
                            # Se o DROP falhou, relança o erro
                            raise
                conn.commit()
            
            self.logger.debug(f"Tabela {table_name} removida (se existia)")
            
        except Exception as e:
            self.logger.error(f"Erro ao remover tabela {table_name}: {e}")
            raise
    
    def disable_foreign_key_checks(self) -> None:
        """
        Desabilita as verificações de foreign key para a sessão atual
        """
        try:
            self.execute_query("SET FOREIGN_KEY_CHECKS = 0", fetch_results=False)
            self.logger.debug("Foreign key checks desabilitados")
        except Exception as e:
            self.logger.warning(f"Erro ao desabilitar foreign key checks: {e}")
    
    def enable_foreign_key_checks(self) -> None:
        """
        Habilita as verificações de foreign key para a sessão atual
        """
        try:
            self.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch_results=False)
            self.logger.debug("Foreign key checks habilitados")
        except Exception as e:
            self.logger.warning(f"Erro ao habilitar foreign key checks: {e}")
    
    def create_table_from_statement(self, create_statement: str) -> None:
        """
        Cria uma tabela a partir de um statement CREATE TABLE
        
        Args:
            create_statement (str): Statement CREATE TABLE
        """
        self.execute_query(create_statement, fetch_results=False)
        self.logger.debug("Tabela criada a partir do statement fornecido")