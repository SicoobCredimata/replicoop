"""
Módulo de restauração avançada do sistema ReplicOOP
Sistema completo para restaurar backups com validação, análise de diferenças e rollback
"""
import os
import subprocess
import gzip
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple
import json
import tempfile
import time

from .config import DatabaseConfig
from .logger import LoggerManager
from .database import DatabaseManager
from .backup import BackupManager, BackupError


class RestoreError(Exception):
    """Exceção personalizada para erros de restauração"""
    pass


class RestoreManager:
    """Gerenciador avançado de restauração de backups"""
    
    def __init__(self, db_manager: DatabaseManager, backup_manager: BackupManager, 
                 logger: LoggerManager):
        """
        Inicializa o gerenciador de restauração
        
        Args:
            db_manager (DatabaseManager): Gerenciador de banco de dados
            backup_manager (BackupManager): Gerenciador de backups
            logger (LoggerManager): Gerenciador de logs
        """
        self.db_manager = db_manager
        self.backup_manager = backup_manager
        self.logger = logger
        self.temp_dir = tempfile.gettempdir()
    
    def analyze_backup(self, backup_filepath: str) -> Dict:
        """
        Analisa um arquivo de backup e retorna informações detalhadas
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            
        Returns:
            Dict: Informações detalhadas do backup
        """
        if not os.path.exists(backup_filepath):
            raise RestoreError(f"Arquivo de backup não encontrado: {backup_filepath}")
        
        try:
            self.logger.info(f"Analisando backup: {os.path.basename(backup_filepath)}")
            
            analysis = {
                'file_path': backup_filepath,
                'file_name': os.path.basename(backup_filepath),
                'file_size': os.path.getsize(backup_filepath),
                'is_compressed': backup_filepath.endswith('.gz'),
                'tables_found': [],
                'table_count': 0,
                'estimated_records': 0,
                'has_foreign_keys': False,
                'has_triggers': False,
                'mysql_version': None,
                'backup_date': None,
                'database_name': None,
                'analysis_date': datetime.now().isoformat()
            }
            
            # Lê o arquivo de backup
            if analysis['is_compressed']:
                file_handle = gzip.open(backup_filepath, 'rt', encoding='utf-8')
            else:
                file_handle = open(backup_filepath, 'r', encoding='utf-8')
            
            try:
                line_count = 0
                in_create_table = False
                current_table = None
                
                for line in file_handle:
                    line_count += 1
                    line = line.strip()
                    
                    # Limita análise a primeiras 10000 linhas para performance
                    if line_count > 10000:
                        self.logger.debug("Análise limitada às primeiras 10000 linhas")
                        break
                    
                    # Procura informações no cabeçalho
                    if line.startswith('-- Backup') and 'date' in line.lower():
                        try:
                            # Extrai data do backup
                            date_part = line.split('-')[-1].strip()
                            analysis['backup_date'] = date_part
                        except:
                            pass
                    
                    if line.startswith('-- Banco:'):
                        analysis['database_name'] = line.split(':', 1)[1].strip()
                    
                    # Procura por tabelas
                    if line.startswith('CREATE TABLE') or line.startswith('DROP TABLE'):
                        table_match = None
                        if '`' in line:
                            # Extrai nome da tabela entre backticks
                            parts = line.split('`')
                            if len(parts) >= 2:
                                table_match = parts[1]
                        
                        if table_match and table_match not in analysis['tables_found']:
                            analysis['tables_found'].append(table_match)
                            analysis['table_count'] += 1
                    
                    # Verifica foreign keys
                    if 'FOREIGN KEY' in line or 'REFERENCES' in line:
                        analysis['has_foreign_keys'] = True
                    
                    # Verifica triggers
                    if 'TRIGGER' in line:
                        analysis['has_triggers'] = True
                    
                    # Conta INSERTs para estimar registros
                    if line.startswith('INSERT INTO'):
                        analysis['estimated_records'] += 1
                
                # Ordena tabelas por nome
                analysis['tables_found'].sort()
                
                self.logger.info(f"Análise concluída: {analysis['table_count']} tabelas, ~{analysis['estimated_records']} registros")
                
            finally:
                file_handle.close()
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar backup: {e}")
            raise RestoreError(f"Falha na análise do backup: {e}")
    
    def validate_backup_compatibility(self, backup_filepath: str) -> Dict:
        """
        Valida se um backup é compatível com o banco atual
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            
        Returns:
            Dict: Resultado da validação
        """
        try:
            self.logger.info("Validando compatibilidade do backup...")
            
            # Analisa o backup
            backup_info = self.analyze_backup(backup_filepath)
            
            # Obtém informações do banco atual
            current_tables = set(self.db_manager.get_tables())
            backup_tables = set(backup_info['tables_found'])
            
            validation = {
                'compatible': True,
                'warnings': [],
                'errors': [],
                'tables_to_add': backup_tables - current_tables,
                'tables_to_remove': current_tables - backup_tables,
                'tables_common': current_tables & backup_tables,
                'backup_info': backup_info
            }
            
            # Verifica diferenças significativas
            if validation['tables_to_remove']:
                validation['warnings'].append(
                    f"Tabelas que serão removidas: {', '.join(validation['tables_to_remove'])}"
                )
            
            if validation['tables_to_add']:
                validation['warnings'].append(
                    f"Novas tabelas serão criadas: {', '.join(validation['tables_to_add'])}"
                )
            
            # Verifica se o banco de destino está correto
            if backup_info.get('database_name') and backup_info['database_name'] != self.db_manager.config.dbname:
                validation['warnings'].append(
                    f"Backup é de '{backup_info['database_name']}', mas será restaurado em '{self.db_manager.config.dbname}'"
                )
            
            # Log do resultado
            if validation['errors']:
                validation['compatible'] = False
                self.logger.warning(f"Backup incompatível: {len(validation['errors'])} erros encontrados")
            elif validation['warnings']:
                self.logger.warning(f"Backup compatível com ressalvas: {len(validation['warnings'])} avisos")
            else:
                self.logger.info("Backup totalmente compatível")
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Erro na validação: {e}")
            raise RestoreError(f"Falha na validação do backup: {e}")
    
    def create_pre_restore_backup(self, suffix: str = "pre_restore") -> str:
        """
        Cria um backup de segurança antes da restauração
        
        Args:
            suffix (str): Sufixo para o nome do backup
            
        Returns:
            str: Caminho do backup criado
        """
        try:
            self.logger.info("Criando backup de segurança antes da restauração...")
            
            # Usa o backup manager para criar backup completo
            backup_path = self.backup_manager.create_full_backup(environment=suffix)
            
            self.logger.info(f"Backup de segurança criado: {os.path.basename(backup_path)}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup de segurança: {e}")
            raise RestoreError(f"Falha no backup de segurança: {e}")
    
    def restore_backup_advanced(self, backup_filepath: str, 
                               create_safety_backup: bool = True,
                               validate_before_restore: bool = True,
                               force_restore: bool = False,
                               dry_run: bool = False) -> Dict:
        """
        Restaura um backup com opções avançadas de segurança e validação
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            create_safety_backup (bool): Criar backup de segurança antes
            validate_before_restore (bool): Validar compatibilidade antes
            force_restore (bool): Forçar restauração mesmo com avisos
            dry_run (bool): Simular restauração sem executar
            
        Returns:
            Dict: Resultado da operação de restauração
        """
        start_time = time.time()
        safety_backup_path = None
        
        result = {
            'success': False,
            'backup_file': os.path.basename(backup_filepath),
            'start_time': datetime.now().isoformat(),
            'safety_backup_created': None,
            'validation_result': None,
            'restore_duration': 0,
            'tables_restored': 0,
            'records_restored': 0,
            'warnings': [],
            'errors': []
        }
        
        try:
            # 1. Validação inicial
            if not os.path.exists(backup_filepath):
                raise RestoreError(f"Arquivo de backup não encontrado: {backup_filepath}")
            
            self.logger.info(f"Iniciando restauração avançada: {result['backup_file']}")
            
            # 2. Validação de compatibilidade
            if validate_before_restore:
                validation = self.validate_backup_compatibility(backup_filepath)
                result['validation_result'] = validation
                
                if not validation['compatible'] and not force_restore:
                    raise RestoreError("Backup incompatível. Use force_restore=True para forçar")
                
                if validation['warnings'] and not force_restore:
                    self.logger.warning("Avisos encontrados na validação:")
                    for warning in validation['warnings']:
                        self.logger.warning(f"  - {warning}")
                    
                    if not dry_run:
                        self.logger.warning("Use force_restore=True para continuar mesmo com avisos")
                        raise RestoreError("Restauração cancelada devido a avisos")
            
            # 3. Backup de segurança
            if create_safety_backup and not dry_run:
                safety_backup_path = self.create_pre_restore_backup()
                result['safety_backup_created'] = safety_backup_path
            
            # 4. Execução da restauração
            if dry_run:
                self.logger.info("DRY RUN: Simulando restauração...")
                result['success'] = True
                result['tables_restored'] = len(result['validation_result']['backup_info']['tables_found'])
                result['records_restored'] = result['validation_result']['backup_info']['estimated_records']
            else:
                # Restauração real
                self._execute_restore(backup_filepath, result)
            
            result['restore_duration'] = time.time() - start_time
            
            if result['success']:
                self.logger.info(f"Restauração concluída com sucesso em {result['restore_duration']:.2f}s")
            
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            result['restore_duration'] = time.time() - start_time
            
            self.logger.error(f"Erro na restauração: {e}")
            
            # Oferece rollback se tiver backup de segurança
            if safety_backup_path and not dry_run:
                self.logger.info("Backup de segurança disponível para rollback")
                result['rollback_available'] = safety_backup_path
            
            raise RestoreError(f"Falha na restauração: {e}")
    
    def _execute_restore(self, backup_filepath: str, result: Dict) -> None:
        """
        Executa a restauração do backup
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            result (Dict): Dicionário para armazenar resultados
        """
        try:
            self.logger.info("Executando restauração do banco de dados...")
            
            # Verifica se mysql client está disponível
            if not self._is_mysql_client_available():
                # Usa restauração Python nativa
                self._restore_with_python(backup_filepath, result)
            else:
                # Usa mysql client
                self._restore_with_mysql_client(backup_filepath, result)
            
            result['success'] = True
            
        except Exception as e:
            raise RestoreError(f"Erro na execução da restauração: {e}")
    
    def _is_mysql_client_available(self) -> bool:
        """Verifica se o cliente mysql está disponível"""
        try:
            result = subprocess.run(['mysql', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _restore_with_mysql_client(self, backup_filepath: str, result: Dict) -> None:
        """
        Restaura usando o cliente mysql
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            result (Dict): Dicionário para armazenar resultados
        """
        mysql_cmd = [
            "mysql",
            f"--host={self.db_manager.config.host}",
            f"--port={self.db_manager.config.port}",
            f"--user={self.db_manager.config.username}",
            f"--password={self.db_manager.config.password}",
            "--default-character-set=utf8mb4",
            self.db_manager.config.dbname
        ]
        
        self.logger.debug("Usando mysql client para restauração")
        
        if backup_filepath.endswith('.gz'):
            # Arquivo comprimido
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
            # Arquivo não comprimido
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                process = subprocess.Popen(
                    mysql_cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise RestoreError(f"Erro no mysql client: {stderr}")
        
        # Conta tabelas restauradas
        tables_after = self.db_manager.get_tables()
        result['tables_restored'] = len(tables_after)
    
    def _restore_with_python(self, backup_filepath: str, result: Dict) -> None:
        """
        Restaura usando Python nativo (quando mysql client não está disponível)
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            result (Dict): Dicionário para armazenar resultados
        """
        self.logger.debug("Usando restauração Python nativa")
        
        # Abre arquivo de backup
        if backup_filepath.endswith('.gz'):
            file_handle = gzip.open(backup_filepath, 'rt', encoding='utf-8')
        else:
            file_handle = open(backup_filepath, 'r', encoding='utf-8')
        
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                
                # Lê e executa comandos SQL do backup
                sql_buffer = []
                line_count = 0
                
                for line in file_handle:
                    line_count += 1
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('--'):
                        continue
                    
                    sql_buffer.append(line)
                    
                    # Executa quando encontra fim de comando
                    if line.endswith(';'):
                        sql_command = ' '.join(sql_buffer)
                        sql_buffer = []
                        
                        try:
                            cursor.execute(sql_command)
                            
                            # Conta registros inseridos
                            if sql_command.upper().startswith('INSERT'):
                                result['records_restored'] += cursor.rowcount
                                
                        except Exception as e:
                            # Log warning mas continua
                            self.logger.warning(f"Erro em comando SQL linha {line_count}: {e}")
                            result['warnings'].append(f"Linha {line_count}: {e}")
                
                # Executa qualquer comando restante no buffer
                if sql_buffer:
                    try:
                        cursor.execute(' '.join(sql_buffer))
                    except Exception as e:
                        self.logger.warning(f"Erro em comando final: {e}")
                
                connection.commit()
                cursor.close()
                
                # Conta tabelas restauradas
                tables_after = self.db_manager.get_tables()
                result['tables_restored'] = len(tables_after)
        
        finally:
            file_handle.close()
    
    def rollback_to_backup(self, safety_backup_path: str) -> bool:
        """
        Realiza rollback usando um backup de segurança
        
        Args:
            safety_backup_path (str): Caminho do backup de segurança
            
        Returns:
            bool: True se rollback foi bem-sucedido
        """
        try:
            self.logger.info(f"Executando rollback para: {os.path.basename(safety_backup_path)}")
            
            # Usa restauração simples para rollback rápido
            result = self.restore_backup_advanced(
                backup_filepath=safety_backup_path,
                create_safety_backup=False,
                validate_before_restore=False,
                force_restore=True,
                dry_run=False
            )
            
            if result['success']:
                self.logger.info("Rollback executado com sucesso")
                return True
            else:
                self.logger.error("Falha no rollback")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro no rollback: {e}")
            return False
    
    def list_available_backups(self, sort_by: str = "date") -> List[Dict]:
        """
        Lista backups disponíveis com informações para restauração
        
        Args:
            sort_by (str): Critério de ordenação (date, size, name)
            
        Returns:
            List[Dict]: Lista de backups disponíveis
        """
        try:
            backups = self.backup_manager.list_backups()
            
            # Adiciona informações úteis para restauração
            for backup in backups:
                # Calcula idade do backup
                if backup.get('timestamp'):
                    try:
                        backup_date = datetime.fromisoformat(backup['timestamp'].replace('Z', '+00:00'))
                        age_days = (datetime.now() - backup_date.replace(tzinfo=None)).days
                        backup['age_days'] = age_days
                        backup['age_description'] = self._describe_age(age_days)
                    except:
                        backup['age_days'] = None
                        backup['age_description'] = "Desconhecida"
                
                # Formata tamanho
                backup['size_formatted'] = self._format_size(backup.get('size_bytes', 0))
                
                # Adiciona recomendação
                backup['recommended'] = backup.get('backup_type') == 'full' and backup.get('age_days', 999) <= 7
            
            # Ordenação
            if sort_by == "date":
                backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            elif sort_by == "size":
                backups.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
            elif sort_by == "name":
                backups.sort(key=lambda x: x.get('backup_file', ''))
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Erro ao listar backups: {e}")
            return []
    
    def _describe_age(self, age_days: int) -> str:
        """Descreve a idade de um backup em linguagem natural"""
        if age_days == 0:
            return "Hoje"
        elif age_days == 1:
            return "Ontem"
        elif age_days <= 7:
            return f"{age_days} dias atrás"
        elif age_days <= 30:
            weeks = age_days // 7
            return f"{weeks} semana{'s' if weeks > 1 else ''} atrás"
        elif age_days <= 365:
            months = age_days // 30
            return f"{months} me{'ses' if months > 1 else 's'} atrás"
        else:
            years = age_days // 365
            return f"{years} ano{'s' if years > 1 else ''} atrás"
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho do arquivo em formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def compare_backup_with_current(self, backup_filepath: str) -> Dict:
        """
        Compara um backup com o estado atual do banco
        
        Args:
            backup_filepath (str): Caminho do arquivo de backup
            
        Returns:
            Dict: Resultado da comparação
        """
        try:
            self.logger.info("Comparando backup com estado atual do banco...")
            
            # Analisa backup
            backup_info = self.analyze_backup(backup_filepath)
            
            # Obtém informações atuais do banco
            current_tables = set(self.db_manager.get_tables())
            backup_tables = set(backup_info['tables_found'])
            
            comparison = {
                'backup_file': os.path.basename(backup_filepath),
                'backup_tables_count': len(backup_tables),
                'current_tables_count': len(current_tables),
                'tables_only_in_backup': sorted(backup_tables - current_tables),
                'tables_only_in_current': sorted(current_tables - backup_tables),
                'tables_in_both': sorted(current_tables & backup_tables),
                'structural_differences': [],
                'recommendations': []
            }
            
            # Recomendações baseadas na comparação
            if comparison['tables_only_in_backup']:
                comparison['recommendations'].append(
                    f"Backup criará {len(comparison['tables_only_in_backup'])} novas tabelas"
                )
            
            if comparison['tables_only_in_current']:
                comparison['recommendations'].append(
                    f"Restauração removerá {len(comparison['tables_only_in_current'])} tabelas existentes"
                )
            
            if not comparison['tables_only_in_backup'] and not comparison['tables_only_in_current']:
                comparison['recommendations'].append("Estrutura compatível - restauração segura")
            
            self.logger.info("Comparação concluída")
            return comparison
            
        except Exception as e:
            self.logger.error(f"Erro na comparação: {e}")
            raise RestoreError(f"Falha na comparação: {e}")