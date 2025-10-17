"""
Módulo principal de replicação do sistema ReplicOOP
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
from tqdm import tqdm

from .config import ConfigManager, DatabaseConfig
from .logger import LoggerManager
from .database import DatabaseManager, DatabaseOperationError
from .backup import BackupManager, BackupError


class ReplicationError(Exception):
    """Exceção personalizada para erros de replicação"""
    pass


class ReplicationManager:
    """Gerenciador principal de replicação de estrutura de banco de dados"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa o gerenciador de replicação
        
        Args:
            config_path (str): Caminho para o arquivo de configuração
        """
        self.config_manager = ConfigManager(config_path)
        self.logger = LoggerManager(
            logs_path=self.config_manager.get_logs_path()
        )
        
        # Inicializa gerenciadores de banco de dados
        self.source_db = None
        self.target_db = None
        self.backup_manager = None
        
        self.logger.info("Sistema ReplicOOP inicializado")
    
    def setup_databases(self, source_env: str = "sandbox", 
                       target_env: str = "production") -> None:
        """
        Configura as conexões com bancos de dados de origem e destino
        
        Args:
            source_env (str): Ambiente de origem (sandbox)
            target_env (str): Ambiente de destino (production)
        """
        try:
            # Configuração do banco de origem
            source_config = self.config_manager.get_database_config(source_env)
            self.source_db = DatabaseManager(source_config, self.logger)
            
            # Configuração do banco de destino
            target_config = self.config_manager.get_database_config(target_env)
            self.target_db = DatabaseManager(target_config, self.logger)
            
            # Configuração do gerenciador de backup
            backup_path = self.config_manager.get_backup_path()
            self.backup_manager = BackupManager(self.target_db, self.logger, backup_path)
            
            self.logger.info(f"Bancos configurados: {source_env} -> {target_env}")
            
            # Testa conexões
            if not self.source_db.test_connection():
                raise ReplicationError(f"Falha na conexão com banco de origem ({source_env})")
            
            if not self.target_db.test_connection():
                raise ReplicationError(f"Falha na conexão com banco de destino ({target_env})")
            
            self.logger.info("Conexões com bancos de dados validadas")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar bancos de dados: {e}")
            raise ReplicationError(f"Falha na configuração: {e}")
    
    def create_backup_before_replication(self, environment: str = "production") -> str:
        """
        Cria backup do banco de destino antes da replicação
        
        Args:
            environment (str): Ambiente do backup (destino)
            
        Returns:
            str: Caminho do arquivo de backup criado
        """
        try:
            self.logger.info("Criando backup de segurança antes da replicação...")
            backup_path = self.backup_manager.create_full_backup(environment)
            
            # Limpa backups antigos (mantém últimos 10)
            self.backup_manager.cleanup_old_backups(keep_last=10)
            
            return backup_path
            
        except BackupError as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            raise ReplicationError(f"Falha no backup: {e}")
    
    def get_replication_plan(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Cria um plano de replicação analisando as diferenças entre os bancos
        
        Args:
            tables (List[str], optional): Lista de tabelas específicas
            
        Returns:
            Dict[str, Any]: Plano de replicação detalhado
        """
        try:
            self.logger.info("Analisando diferenças entre bancos...")
            
            # Obtém tabelas para replicação
            if not tables:
                # Se não especificado, usa apenas tabelas maintain (comportamento anterior)
                tables = self.config_manager.get_maintain_tables()
                self.logger.info(f"Tabelas maintain configuradas: {tables}")
                if not tables:
                    tables = self.source_db.get_tables()
                    self.logger.info(f"Usando todas as tabelas do banco de origem: {len(tables)} tabelas")
            else:
                self.logger.info(f"Usando tabelas especificadas: {len(tables) if isinstance(tables, list) else 'N/A'} tabelas")
            
            source_tables = self.source_db.get_tables()
            target_tables = self.target_db.get_tables()
            
            self.logger.info(f"Tabelas no banco de origem: {len(source_tables)}")
            self.logger.info(f"Tabelas no banco de destino: {len(target_tables)}")
            self.logger.info(f"Tabelas para processar: {len(tables) if tables else 0}")
            
            if not tables:
                self.logger.error("Nenhuma tabela foi encontrada para processar!")
                raise ReplicationError("Nenhuma tabela disponível para replicação")
            
            plan = {
                'timestamp': datetime.now().isoformat(),
                'source_tables': len(source_tables),
                'target_tables': len(target_tables),
                'tables_to_replicate': [],
                'tables_to_drop': [],
                'foreign_key_issues': [],
                'foreign_keys_to_recreate': [],  # NOVO: FKs para recriar após replicação
                'warnings': []
            }
            
            # Analisa cada tabela para replicação
            for table in tables:
                if table not in source_tables:
                    plan['warnings'].append(f"Tabela '{table}' não encontrada no banco de origem")
                    continue
                
                table_plan = {
                    'name': table,
                    'action': 'create',
                    'has_foreign_keys': False,
                    'foreign_keys': [],
                    'create_statement_fks': []  # NOVO: FKs extraídas do CREATE TABLE
                }
                
                # Verifica se tabela existe no destino
                if table in target_tables:
                    table_plan['action'] = 'recreate'
                
                # Analisa chaves estrangeiras
                try:
                    foreign_keys = self.source_db.get_foreign_keys(table)
                    if foreign_keys:
                        table_plan['has_foreign_keys'] = True
                        table_plan['foreign_keys'] = foreign_keys
                        
                        # NOVO: Extrai FKs do CREATE TABLE para recriar depois
                        create_statement = self.source_db.get_create_table_statement(table)
                        create_statement_fks = self._extract_foreign_keys_from_create_statement(create_statement, table)
                        table_plan['create_statement_fks'] = create_statement_fks
                        
                        # Adiciona ao plano global para recriar depois
                        plan['foreign_keys_to_recreate'].extend(create_statement_fks)
                        
                        # Verifica se tabelas referenciadas existem
                        for fk in foreign_keys:
                            ref_table = fk['referenced_table']
                            if ref_table not in source_tables:
                                plan['foreign_key_issues'].append(
                                    f"Tabela referenciada '{ref_table}' não encontrada para FK em '{table}'"
                                )
                
                except Exception as e:
                    self.logger.warning(f"Erro ao analisar FKs da tabela {table}: {e}")
                
                plan['tables_to_replicate'].append(table_plan)
            
            # Identifica tabelas no destino que não estão na lista de replicação
            for table in target_tables:
                if table not in tables and table not in [t['name'] for t in plan['tables_to_replicate']]:
                    plan['tables_to_drop'].append(table)
            
            self.logger.info(f"Plano de replicação criado: {len(plan['tables_to_replicate'])} tabelas")
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Erro ao criar plano de replicação: {e}")
            self.logger.error(f"Tipo do erro: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise ReplicationError(f"Falha no planejamento: {e}")
    
    def execute_replication(self, tables: Optional[List[str]] = None, 
                          create_backup: bool = True,
                          replicate_data: bool = False) -> Dict[str, Any]:
        """
        Executa a replicação de estrutura das tabelas
        
        Args:
            tables (List[str], optional): Lista de tabelas específicas
            create_backup (bool): Se deve criar backup antes da replicação
            replicate_data (bool): Se deve replicar dados das tabelas maintain
            
        Returns:
            Dict[str, Any]: Relatório da replicação
        """
        start_time = time.time()
        backup_path = None
        
        try:
            self.logger.info("=== INICIANDO REPLICAÇÃO DE ESTRUTURA ===")
            
            # Cria backup se solicitado
            if create_backup:
                backup_path = self.create_backup_before_replication()
            
            # Cria plano de replicação
            # Se tables não foi especificado, replica TODAS as tabelas do banco de origem
            if tables is None:
                tables = self.source_db.get_tables()
                self.logger.info(f"Replicando TODAS as tabelas do banco de origem: {len(tables)} tabelas")
                # Ordena tabelas por dependências de Foreign Keys
                tables = self._sort_tables_by_dependencies(tables)
            
            plan = self.get_replication_plan(tables)
            
            if not plan['tables_to_replicate']:
                self.logger.warning("Nenhuma tabela para replicar encontrada")
                return {
                    'success': True,
                    'tables_replicated': 0,
                    'execution_time': time.time() - start_time,
                    'backup_created': backup_path,
                    'warnings': ['Nenhuma tabela para replicar']
                }
            
            # Obtém lista de tabelas maintain para replicação de dados
            maintain_tables = self.config_manager.get_maintain_tables()
            
            # Desabilita verificação de FKs no destino
            self.target_db.disable_foreign_key_checks()
            
            replicated_tables = []
            failed_tables = []
            data_replicated_tables = []
            
            # Barra de progresso
            with tqdm(total=len(plan['tables_to_replicate']), desc="Replicando tabelas") as pbar:
                
                for table_plan in plan['tables_to_replicate']:
                    table_name = table_plan['name']
                    is_maintain_table = table_name in maintain_tables
                    
                    try:
                        pbar.set_description(f"Replicando {table_name}")
                        
                        # Obtém estrutura da tabela de origem
                        create_statement = self.source_db.get_create_table_statement(table_name)
                        
                        if is_maintain_table:
                            # TABELAS MAINTAIN: Remove completamente e recria com dados de origem
                            self.logger.debug(f"Tabela MAINTAIN {table_name}: replicando estrutura + dados")
                            
                            # Remove tabela no destino se existir
                            self.target_db.drop_table_if_exists(table_name)
                            
                            # Cria tabela no destino
                            self.target_db.create_table_from_statement(create_statement)
                            
                            # RESETAR AUTO_INCREMENT para preservar IDs originais
                            try:
                                # Verifica se a tabela tem campo AUTO_INCREMENT
                                table_structure = self.target_db.get_table_structure(table_name)
                                has_auto_increment = any(col.get('Extra', '').lower() == 'auto_increment' for col in table_structure)
                                
                                if has_auto_increment:
                                    self.logger.debug(f"Resetando AUTO_INCREMENT da tabela {table_name} para preservar IDs originais")
                                    self.target_db.execute_query(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1", fetch_results=False)
                            except Exception as e:
                                self.logger.warning(f"Não foi possível resetar AUTO_INCREMENT para {table_name}: {e}")
                            
                            # Replica os dados de origem
                            try:
                                self._replicate_table_data(table_name)
                                data_replicated_tables.append(table_name)
                                replicated_tables.append(f"{table_name} (estrutura + dados)")
                                self.logger.debug(f"Tabela maintain {table_name} replicada com estrutura e dados")
                            except Exception as data_error:
                                # Se falhar na replicação de dados, ainda marca como sucesso estrutural
                                replicated_tables.append(f"{table_name} (apenas estrutura)")
                                self.logger.warning(f"Estrutura de {table_name} criada, mas falhou na replicação dos dados: {data_error}")
                        
                        else:
                            # TABELAS NÃO-MAINTAIN: Preserva dados existentes e atualiza apenas estrutura
                            self.logger.debug(f"Tabela NÃO-MAINTAIN {table_name}: preservando dados, atualizando estrutura")
                            
                            # Verifica se a tabela já existe no destino
                            table_exists = self.target_db.table_exists(table_name)
                            
                            if table_exists:
                                # Preserva os dados existentes durante atualização estrutural
                                self._update_table_structure_preserving_data(table_name, create_statement)
                                replicated_tables.append(f"{table_name} (estrutura atualizada, dados preservados)")
                                self.logger.debug(f"Tabela não-maintain {table_name}: estrutura atualizada, dados preservados")
                            else:
                                # Tabela não existe: cria nova apenas com estrutura (sem dados)
                                self.target_db.create_table_from_statement(create_statement)
                                replicated_tables.append(f"{table_name} (nova estrutura criada)")
                                self.logger.debug(f"Tabela não-maintain {table_name}: nova tabela criada (apenas estrutura)")
                        
                    except DatabaseOperationError as e:
                        # Se for erro relacionado a FK, tenta ignorar
                        if "foreign key" in str(e).lower() or "constraint" in str(e).lower():
                            self.logger.warning(f"Erro de FK ignorado para {table_name}: {e}")
                            
                            # Tenta criar tabela sem FKs
                            try:
                                modified_statement = self._remove_foreign_keys_from_create_statement(
                                    create_statement
                                )
                                
                                self.target_db.drop_table_if_exists(table_name)
                                self.target_db.create_table_from_statement(modified_statement)
                                
                                # Verifica se deve replicar dados mesmo sem FKs
                                if is_maintain_table and replicate_data:
                                    try:
                                        self._replicate_table_data(table_name)
                                        data_replicated_tables.append(table_name)
                                        replicated_tables.append(f"{table_name} (sem FKs, estrutura + dados)")
                                    except Exception as data_error:
                                        replicated_tables.append(f"{table_name} (sem FKs)")
                                        self.logger.warning(f"Dados de {table_name} não replicados: {data_error}")
                                else:
                                    replicated_tables.append(f"{table_name} (sem FKs)")
                                
                                self.logger.info(f"Tabela {table_name} criada sem chaves estrangeiras")
                                
                            except Exception as e2:
                                failed_tables.append({
                                    'table': table_name,
                                    'error': str(e2)
                                })
                                self.logger.error(f"Falha ao criar {table_name} mesmo sem FKs: {e2}")
                        else:
                            failed_tables.append({
                                'table': table_name,
                                'error': str(e)
                            })
                            self.logger.error(f"Erro ao replicar {table_name}: {e}")
                            self.logger.error(f"Tipo do erro: {type(e).__name__}")
                            import traceback
                            self.logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    except Exception as e:
                        failed_tables.append({
                            'table': table_name,
                            'error': str(e)
                        })
                        self.logger.error(f"Erro inesperado ao replicar {table_name}: {e}")
                        self.logger.error(f"Tipo do erro: {type(e).__name__}")
                        import traceback
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    finally:
                        pbar.update(1)
            
            # Reabilita verificação de FKs
            self.target_db.enable_foreign_key_checks()
            
            # NOVA FUNCIONALIDADE: Recria as chaves estrangeiras após replicação
            fk_recreation_report = None
            if plan.get('foreign_keys_to_recreate'):
                self.logger.info("=== RECRIANDO CHAVES ESTRANGEIRAS ===")
                try:
                    fk_recreation_report = self._recreate_foreign_keys(plan['foreign_keys_to_recreate'])
                except Exception as fk_error:
                    self.logger.error(f"Erro ao recriar chaves estrangeiras: {fk_error}")
                    # Não falha a replicação por causa das FKs, apenas registra o erro
                    fk_recreation_report = {
                        'success': False,
                        'total_fks': len(plan.get('foreign_keys_to_recreate', [])),
                        'recreated_fks': 0,
                        'failed_fks': [{'error': str(fk_error)}]
                    }
            
            execution_time = time.time() - start_time
            success_count = len(replicated_tables)
            
            # Log do resultado
            if failed_tables:
                self.logger.warning(f"Replicação concluída com {len(failed_tables)} falhas")
            else:
                self.logger.info("Replicação concluída com sucesso!")
            
            self.logger.info(f"Tabelas replicadas: {success_count}")
            if data_replicated_tables:
                self.logger.info(f"Tabelas com dados replicados: {len(data_replicated_tables)}")
            self.logger.info(f"Tempo de execução: {execution_time:.2f}s")
            
            # Log do resultado das FKs
            if fk_recreation_report:
                if fk_recreation_report['success']:
                    self.logger.info(f"🔗 Chaves estrangeiras: {fk_recreation_report['recreated_fks']} recriadas com sucesso!")
                else:
                    self.logger.warning(f"⚠️ Chaves estrangeiras: {fk_recreation_report['recreated_fks']}/{fk_recreation_report['total_fks']} recriadas")
            
            return {
                'success': len(failed_tables) == 0,
                'tables_replicated': success_count,
                'replicated_tables': replicated_tables,
                'data_replicated_tables': data_replicated_tables,
                'failed_tables': failed_tables,
                'execution_time': execution_time,
                'backup_created': backup_path,
                'plan': plan,
                'foreign_keys_recreation': fk_recreation_report  # NOVO: Relatório das FKs
            }
            
        except Exception as e:
            # Reabilita FKs em caso de erro
            try:
                if self.target_db:
                    self.target_db.enable_foreign_key_checks()
            except:
                pass
            
            self.logger.error(f"Erro crítico durante replicação: {e}")
            raise ReplicationError(f"Falha na replicação: {e}")
    
    def _remove_foreign_keys_from_create_statement(self, create_statement: str) -> str:
        """
        Remove definições de chaves estrangeiras de um statement CREATE TABLE
        
        Args:
            create_statement (str): Statement original
            
        Returns:
            str: Statement modificado sem FKs
        """
        lines = create_statement.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Skip linhas que definem foreign keys
            if (line_lower.startswith('constraint') and 'foreign key' in line_lower) or \
               (line_lower.startswith('foreign key')) or \
               ('references' in line_lower and 'foreign' in line_lower):
                continue
            
            # Remove vírgulas órfãs
            if line.strip() == ',':
                continue
                
            filtered_lines.append(line)
        
        # Remove última vírgula se necessário
        result = '\n'.join(filtered_lines)
        result = result.replace(',\n)', '\n)')
        result = result.replace(', )', ' )')
        
        return result
    
    def _extract_foreign_keys_from_create_statement(self, create_statement: str, table_name: str) -> List[Dict[str, str]]:
        """
        Extrai definições de chaves estrangeiras do statement CREATE TABLE
        
        Args:
            create_statement (str): Statement CREATE TABLE original
            table_name (str): Nome da tabela
            
        Returns:
            List[Dict[str, str]]: Lista de definições de FK para recriar depois
        """
        foreign_keys = []
        lines = create_statement.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Encontra linhas com definições de CONSTRAINT FOREIGN KEY
            if line_lower.startswith('constraint') and 'foreign key' in line_lower:
                try:
                    # Extrai o nome da constraint e a definição completa
                    # Exemplo: CONSTRAINT `processes_ibfk_1` FOREIGN KEY (`procedure_id`) REFERENCES `procedures` (`id`)
                    
                    # Remove vírgula do final se houver
                    clean_line = line_stripped.rstrip(',').strip()
                    
                    # Extrai o nome da constraint para poder remover se já existir
                    constraint_name = None
                    try:
                        # Busca por CONSTRAINT `nome` ou CONSTRAINT nome
                        import re
                        constraint_match = re.search(r'CONSTRAINT\s+[`"]?([^`"\s]+)[`"]?', clean_line, re.IGNORECASE)
                        if constraint_match:
                            constraint_name = constraint_match.group(1)
                    except:
                        pass
                    
                    # Adiciona a definição completa da FK para recriar depois
                    foreign_keys.append({
                        'table_name': table_name,
                        'constraint_name': constraint_name,
                        'constraint_definition': clean_line,
                        'alter_statement': f"ALTER TABLE `{table_name}` ADD {clean_line}"
                    })
                    
                    self.logger.debug(f"FK extraída de {table_name}: {clean_line}")
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair FK da linha '{line_stripped}': {e}")
                    continue
        
        return foreign_keys
    
    def _recreate_foreign_keys(self, foreign_keys_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Recria as chaves estrangeiras após a replicação das tabelas
        
        Args:
            foreign_keys_list (List[Dict[str, str]]): Lista de FKs para recriar
            
        Returns:
            Dict[str, Any]: Relatório da recriação de FKs
        """
        if not foreign_keys_list:
            self.logger.info("Nenhuma chave estrangeira para recriar")
            return {
                'success': True,
                'total_fks': 0,
                'recreated_fks': 0,
                'failed_fks': []
            }
        
        self.logger.info(f"Recriando {len(foreign_keys_list)} chave(s) estrangeira(s)...")
        
        recreated_count = 0
        failed_fks = []
        
        # Desabilita verificação de FKs temporariamente para evitar problemas de ordem
        self.target_db.disable_foreign_key_checks()
        
        try:
            # Agrupa FKs por tabela para otimizar
            fks_by_table = {}
            for fk in foreign_keys_list:
                table_name = fk['table_name']
                if table_name not in fks_by_table:
                    fks_by_table[table_name] = []
                fks_by_table[table_name].append(fk)
            
            # PRIMEIRO: Remove todas as constraints FK existentes das tabelas alvo
            self.logger.debug("Removendo constraints FK existentes...")
            for table_name in fks_by_table.keys():
                try:
                    existing_constraints = self.target_db.get_existing_foreign_key_constraints(table_name)
                    for constraint_name in existing_constraints:
                        self.target_db.drop_foreign_key_constraint(table_name, constraint_name)
                        self.logger.debug(f"Constraint existente removida: {table_name}.{constraint_name}")
                except Exception as e:
                    self.logger.debug(f"Erro ao limpar constraints de {table_name}: {e}")
            
            # SEGUNDO: Processa cada tabela para recriar as FKs
            for table_name, table_fks in fks_by_table.items():
                self.logger.debug(f"Recriando {len(table_fks)} FK(s) para tabela {table_name}")
                
                for fk in table_fks:
                    try:
                        alter_statement = fk['alter_statement']
                        
                        # Executa o ALTER TABLE para adicionar a FK
                        self.target_db.execute_query(alter_statement, fetch_results=False)
                        
                        recreated_count += 1
                        self.logger.debug(f"FK recriada: {fk['constraint_definition']}")
                        
                    except Exception as e:
                        error_msg = f"Erro ao recriar FK {fk['constraint_definition']}: {e}"
                        self.logger.warning(error_msg)
                        failed_fks.append({
                            'table': table_name,
                            'constraint': fk['constraint_definition'],
                            'error': str(e)
                        })
        
        finally:
            # Reabilita verificação de FKs
            self.target_db.enable_foreign_key_checks()
        
        success = len(failed_fks) == 0
        
        if success:
            self.logger.info(f"✅ Todas as {recreated_count} chave(s) estrangeira(s) foram recriadas com sucesso!")
        else:
            self.logger.warning(f"⚠️ {recreated_count} FK(s) recriadas, {len(failed_fks)} falharam")
        
        return {
            'success': success,
            'total_fks': len(foreign_keys_list),
            'recreated_fks': recreated_count,
            'failed_fks': failed_fks
        }
    
    def validate_replication(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Valida se a replicação foi bem-sucedida comparando estruturas
        
        Args:
            tables (List[str], optional): Lista de tabelas para validar
            
        Returns:
            Dict[str, Any]: Relatório de validação
        """
        try:
            self.logger.info("Validando replicação...")
            
            if not tables:
                tables = self.config_manager.get_maintain_tables()
                if not tables:
                    tables = self.source_db.get_tables()
            
            validation_report = {
                'timestamp': datetime.now().isoformat(),
                'tables_validated': 0,
                'structure_matches': [],
                'structure_differences': [],
                'missing_tables': []
            }
            
            target_tables = self.target_db.get_tables()
            
            for table in tables:
                try:
                    if table not in target_tables:
                        validation_report['missing_tables'].append(table)
                        continue
                    
                    # Obtém estruturas
                    source_structure = self.source_db.get_table_structure(table)
                    target_structure = self.target_db.get_table_structure(table)
                    
                    # Compara estruturas (ignora FKs)
                    source_basic = self._normalize_structure_for_comparison(source_structure)
                    target_basic = self._normalize_structure_for_comparison(target_structure)
                    
                    if source_basic == target_basic:
                        validation_report['structure_matches'].append(table)
                    else:
                        validation_report['structure_differences'].append({
                            'table': table,
                            'differences': self._find_structure_differences(
                                source_basic, target_basic
                            )
                        })
                    
                    validation_report['tables_validated'] += 1
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao validar tabela {table}: {e}")
            
            # Log do resultado da validação
            matches = len(validation_report['structure_matches'])
            differences = len(validation_report['structure_differences'])
            missing = len(validation_report['missing_tables'])
            
            self.logger.info(f"Validação concluída: {matches} OK, {differences} diferenças, {missing} ausentes")
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Erro durante validação: {e}")
            raise ReplicationError(f"Falha na validação: {e}")
    
    def _replicate_table_data(self, table_name: str, batch_size: int = 1000) -> None:
        """
        Replica os dados de uma tabela específica do banco origem para o destino
        
        Args:
            table_name (str): Nome da tabela
            batch_size (int): Tamanho do lote para processamento
        """
        try:
            self.logger.debug(f"Iniciando replicação de dados da tabela {table_name}")
            
            # Configurar modo SQL para preservar valores 0 em colunas AUTO_INCREMENT
            self.target_db.set_zero_preserve_mode(True)
            
            # Verificar se a tabela tem campo AUTO_INCREMENT
            table_structure = self.target_db.get_table_structure(table_name)
            auto_increment_field = None
            for col in table_structure:
                if col.get('Extra', '').lower() == 'auto_increment':
                    auto_increment_field = col['Field']
                    break
            
            # NOVA ESTRATÉGIA: Para preservar IDs=0, desabilitar AUTO_INCREMENT temporariamente
            needs_auto_increment_fix = False
            original_auto_increment_value = None
            
            if auto_increment_field:
                # Verifica se há registros com ID=0 na origem
                check_zero_query = f"SELECT COUNT(*) as count FROM `{table_name}` WHERE `{auto_increment_field}` = 0"
                zero_result = self.source_db.execute_query(check_zero_query)
                has_zero_id = zero_result[0]['count'] > 0 if zero_result else False
                
                if has_zero_id:
                    self.logger.info(f"🚨 Tabela {table_name} tem registros com {auto_increment_field}=0, aplicando correção especial...")
                    needs_auto_increment_fix = True
                    
                    # Salva o valor atual do AUTO_INCREMENT
                    show_create_query = f"SHOW CREATE TABLE `{table_name}`"
                    create_result = self.target_db.execute_query(show_create_query)
                    if create_result:
                        create_table_sql = create_result[0]['Create Table']
                        import re
                        match = re.search(r'AUTO_INCREMENT=(\d+)', create_table_sql)
                        if match:
                            original_auto_increment_value = int(match.group(1))
                            self.logger.info(f"💾 Valor original AUTO_INCREMENT: {original_auto_increment_value}")
                    
                    # Remove o AUTO_INCREMENT temporariamente
                    self.logger.info(f"🔧 Removendo AUTO_INCREMENT temporariamente da coluna {auto_increment_field}...")
                    
                    # Obtém definição completa da coluna
                    column_def = None
                    for col in table_structure:
                        if col['Field'] == auto_increment_field:
                            null_part = "NOT NULL" if col['Null'] == 'NO' else "NULL"
                            column_def = f"`{col['Field']}` {col['Type']} {null_part}"
                            break
                    
                    if column_def:
                        alter_remove_query = f"ALTER TABLE `{table_name}` MODIFY COLUMN {column_def}"
                        self.target_db.execute_query(alter_remove_query, fetch_results=False)
                        self.logger.info(f"✅ AUTO_INCREMENT removido temporariamente")
            
            # LIMPA os dados da tabela destino para garantir dados idênticos
            self.logger.debug(f"Limpando dados existentes da tabela {table_name} no destino")
            self.target_db.execute_query(f"DELETE FROM `{table_name}`", fetch_results=False)
            
            # Conta total de registros na origem
            count_query = f"SELECT COUNT(*) as total FROM `{table_name}`"
            total_rows = self.source_db.execute_query(count_query)[0]['total']
            
            if total_rows == 0:
                self.logger.debug(f"Tabela {table_name} está vazia, nenhum dado para replicar")
                return
            
            self.logger.debug(f"Replicando {total_rows} registros da tabela {table_name}")
            
            # Obtém estrutura da tabela para montar INSERT
            columns = self.source_db.get_table_columns(table_name)
            column_names = [col['name'] for col in columns]
            
            # Monta queries - usa REPLACE INTO para garantir que IDs específicos sejam preservados
            select_query = f"SELECT * FROM `{table_name}` LIMIT %s OFFSET %s"
            
            # Para tabelas com AUTO_INCREMENT, usar INSERT INTO simples já que removemos o AUTO_INCREMENT
            if needs_auto_increment_fix:
                insert_query = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in column_names])}) VALUES ({', '.join(['%s'] * len(column_names))})"
                self.logger.info(f"🔧 TABELA {table_name}: Usando INSERT INTO (AUTO_INCREMENT temporariamente removido)")
            elif auto_increment_field:
                insert_query = f"REPLACE INTO `{table_name}` ({', '.join([f'`{col}`' for col in column_names])}) VALUES ({', '.join(['%s'] * len(column_names))})"
                self.logger.info(f"🔧 TABELA {table_name}: Usando REPLACE INTO para preservar IDs")
            else:
                insert_query = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in column_names])}) VALUES ({', '.join(['%s'] * len(column_names))})"
                self.logger.info(f"🔧 TABELA {table_name}: Usando INSERT INTO normal")
            
            # Processa em lotes
            processed = 0
            
            with tqdm(total=total_rows, desc=f"Dados {table_name}", leave=False) as data_pbar:
                while processed < total_rows:
                    # Busca lote de dados
                    batch_data = self.source_db.execute_query(select_query, (batch_size, processed))
                    
                    if not batch_data:
                        break
                    
                    # Prepara dados para inserção
                    batch_values = []
                    for row in batch_data:
                        # Converte row dict para lista ordenada de valores
                        row_values = [row.get(col) for col in column_names]
                        batch_values.append(row_values)
                        
                        # Log detalhado para registros com ID = 0
                        if auto_increment_field and row.get(auto_increment_field) == 0:
                            self.logger.info(f"📝 INSERINDO REGISTRO ID=0: {dict(zip(column_names, row_values))}")
                    
                    # Insere lote no destino
                    self.target_db.execute_many_query(insert_query, batch_values)
                    
                    processed += len(batch_data)
                    data_pbar.update(len(batch_data))
            
            # Restaura AUTO_INCREMENT se foi removido
            if needs_auto_increment_fix and auto_increment_field:
                # PRIMEIRO: Verifica se os IDs=0 foram preservados (antes de restaurar AUTO_INCREMENT)
                check_query = f"SELECT COUNT(*) as count FROM `{table_name}` WHERE `{auto_increment_field}` = 0"
                result = self.target_db.execute_query(check_query)
                zero_count = result[0]['count'] if result else 0
                
                if zero_count > 0:
                    self.logger.info(f"✅ {zero_count} registro(s) com ID=0 preservados com sucesso!")
                    
                    # DECISÃO CRÍTICA: NÃO restaurar AUTO_INCREMENT se há registros com ID=0
                    # pois o MySQL irá converter ID=0 para o próximo valor disponível
                    self.logger.warning(f"⚠️ AUTO_INCREMENT NÃO será restaurado para preservar IDs com valor 0")
                    self.logger.warning(f"⚠️ Tabela {table_name} ficará sem AUTO_INCREMENT para manter integridade dos dados")
                    
                else:
                    self.logger.info(f"🔧 Restaurando AUTO_INCREMENT na coluna {auto_increment_field}...")
                    
                    # Obtém definição completa da coluna com AUTO_INCREMENT
                    column_def = None
                    for col in table_structure:
                        if col['Field'] == auto_increment_field:
                            null_part = "NOT NULL" if col['Null'] == 'NO' else "NULL"
                            column_def = f"`{col['Field']}` {col['Type']} {null_part} AUTO_INCREMENT"
                            break
                    
                    if column_def:
                        alter_restore_query = f"ALTER TABLE `{table_name}` MODIFY COLUMN {column_def}"
                        self.target_db.execute_query(alter_restore_query, fetch_results=False)
                    
                    # Restaura o valor do AUTO_INCREMENT
                    if original_auto_increment_value is not None:
                        # Ajusta para o próximo valor disponível
                        max_id_query = f"SELECT COALESCE(MAX(`{auto_increment_field}`), 0) as max_id FROM `{table_name}`"
                        max_result = self.target_db.execute_query(max_id_query)
                        current_max = max_result[0]['max_id'] if max_result else 0
                        next_auto_increment = max(current_max + 1, original_auto_increment_value)
                        
                        alter_increment_query = f"ALTER TABLE `{table_name}` AUTO_INCREMENT = {next_auto_increment}"
                        self.target_db.execute_query(alter_increment_query, fetch_results=False)
                        self.logger.info(f"✅ AUTO_INCREMENT restaurado para: {next_auto_increment}")
                        
            else:
                # Se não há correção especial, verifica se há registros com ID=0
                if auto_increment_field:
                    check_query = f"SELECT COUNT(*) as count FROM `{table_name}` WHERE `{auto_increment_field}` = 0"
                    result = self.target_db.execute_query(check_query)
                    zero_count = result[0]['count'] if result else 0
                    if zero_count > 0:
                        self.logger.info(f"✅ {zero_count} registro(s) com ID=0 preservados!")
                    else:
                        self.logger.debug(f"ℹ️ Nenhum registro com ID=0 na tabela {table_name}")
            
            self.logger.debug(f"Dados da tabela {table_name} replicados com sucesso: {processed} registros")
            
            # Restaurar modo SQL padrão
            self.target_db.set_zero_preserve_mode(False)
            
        except Exception as e:
            # Restaurar modo SQL padrão em caso de erro
            try:
                self.target_db.set_zero_preserve_mode(False)
            except:
                pass
                
            self.logger.error(f"Erro ao replicar dados da tabela {table_name}: {e}")
            raise DatabaseOperationError(f"Falha na replicação de dados de {table_name}: {e}")
    
    def _normalize_structure_for_comparison(self, structure: List[Dict]) -> List[Dict]:
        """Normaliza estrutura de tabela para comparação (remove informações de FK)"""
        normalized = []
        for column in structure:
            normalized.append({
                'Field': column['Field'],
                'Type': column['Type'],
                'Null': column['Null'],
                'Default': column['Default'],
                'Extra': column['Extra']
            })
        return normalized
    
    def _find_structure_differences(self, source: List[Dict], target: List[Dict]) -> List[str]:
        """Encontra diferenças entre duas estruturas de tabela"""
        differences = []
        
        source_fields = {col['Field']: col for col in source}
        target_fields = {col['Field']: col for col in target}
        
        # Campos apenas no source
        for field in source_fields:
            if field not in target_fields:
                differences.append(f"Campo '{field}' existe no origem mas não no destino")
        
        # Campos apenas no target
        for field in target_fields:
            if field not in source_fields:
                differences.append(f"Campo '{field}' existe no destino mas não no origem")
        
        # Campos com diferenças
        for field in source_fields:
            if field in target_fields:
                if source_fields[field] != target_fields[field]:
                    differences.append(f"Campo '{field}' tem definição diferente")
        
        return differences
    
    def _sort_tables_by_dependencies(self, tables: List[str]) -> List[str]:
        """
        Ordena tabelas por dependências de Foreign Keys para evitar erros de criação
        
        Args:
            tables (List[str]): Lista de tabelas para ordenar
            
        Returns:
            List[str]: Tabelas ordenadas por dependência
        """
        try:
            self.logger.debug("Analisando dependências de Foreign Keys...")
            
            # Mapa de dependências: tabela -> tabelas que ela depende
            dependencies = {}
            
            # Analisa cada tabela para encontrar FKs
            for table in tables:
                dependencies[table] = []
                try:
                    # Obtém informações de FKs da tabela
                    fk_query = """
                        SELECT 
                            REFERENCED_TABLE_NAME
                        FROM 
                            information_schema.KEY_COLUMN_USAGE 
                        WHERE 
                            TABLE_SCHEMA = DATABASE() 
                            AND TABLE_NAME = %s
                            AND REFERENCED_TABLE_NAME IS NOT NULL
                    """
                    fk_results = self.source_db.execute_query(fk_query, (table,))
                    
                    for fk_row in fk_results:
                        referenced_table = fk_row.get('REFERENCED_TABLE_NAME')
                        if referenced_table and referenced_table in tables and referenced_table != table:
                            dependencies[table].append(referenced_table)
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao analisar FKs de {table}: {e}")
            
            # Ordenação topológica
            ordered_tables = []
            visited = set()
            temp_visited = set()
            
            def visit(table):
                if table in temp_visited:
                    # Dependência circular - ignora e continua
                    return
                if table in visited:
                    return
                    
                temp_visited.add(table)
                
                # Visita dependências primeiro
                for dep_table in dependencies.get(table, []):
                    if dep_table in tables:
                        visit(dep_table)
                
                temp_visited.remove(table)
                visited.add(table)
                ordered_tables.append(table)
            
            # Processa todas as tabelas
            for table in tables:
                if table not in visited:
                    visit(table)
            
            self.logger.info(f"Tabelas ordenadas por dependências: {len(ordered_tables)} tabelas")
            return ordered_tables
            
        except Exception as e:
            self.logger.warning(f"Erro ao ordenar tabelas por dependência: {e}")
            # Se falhar, retorna ordem original
            return tables

    def _clean_create_statement_for_temp(self, create_statement: str, temp_table_name: str) -> str:
        """
        Remove restrições de FK do statement CREATE para tabela temporária
        
        Args:
            create_statement (str): Statement CREATE original
            temp_table_name (str): Nome da tabela temporária
            
        Returns:
            str: Statement CREATE limpo para tabela temporária
        """
        try:
            lines = create_statement.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Substituir nome da tabela pelo nome temporário
                if 'CREATE TABLE' in line_stripped:
                    # Encontrar e substituir o nome da tabela
                    import re
                    line = re.sub(r'CREATE TABLE `([^`]+)`', f'CREATE TABLE `{temp_table_name}`', line)
                    cleaned_lines.append(line)
                # Pular linhas que contêm restrições de FK
                elif (line_stripped.startswith('CONSTRAINT') and 'FOREIGN KEY' in line_stripped) or \
                     line_stripped.startswith('FOREIGN KEY') or \
                     (line_stripped.startswith('KEY') and 'FOREIGN' in line_stripped) or \
                     line_stripped.startswith('ADD CONSTRAINT'):
                    continue
                # Linha de fechamento da tabela
                elif line_stripped.startswith(')') and ('ENGINE=' in line_stripped or 'CHARSET=' in line_stripped):
                    # Remover vírgula do final da linha anterior se existir
                    if cleaned_lines and cleaned_lines[-1].strip().endswith(','):
                        cleaned_lines[-1] = cleaned_lines[-1].rstrip().rstrip(',')
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
            
            # Verificar se há vírgula final antes do fechamento e remover se necessário
            result_lines = []
            for i, line in enumerate(cleaned_lines):
                if i == len(cleaned_lines) - 1:  # Última linha
                    result_lines.append(line)
                elif i == len(cleaned_lines) - 2:  # Penúltima linha
                    # Se a próxima linha é fechamento da tabela, remover vírgula final
                    next_line = cleaned_lines[i + 1].strip()
                    if next_line.startswith(')') and line.strip().endswith(','):
                        result_lines.append(line.rstrip().rstrip(','))
                    else:
                        result_lines.append(line)
                else:
                    result_lines.append(line)
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            self.logger.warning(f"Erro ao limpar statement CREATE: {e}")
            # Em caso de erro, apenas substitui o nome da tabela
            import re
            return re.sub(r'CREATE TABLE `([^`]+)`', f'CREATE TABLE `{temp_table_name}`', create_statement)
    
    def _update_table_structure_preserving_data(self, table_name: str, new_create_statement: str) -> None:
        """
        Atualiza a estrutura de uma tabela preservando os dados existentes
        
        Args:
            table_name (str): Nome da tabela
            new_create_statement (str): Novo CREATE TABLE statement
        """
        temp_table = None
        backup_table = None
        
        try:
            self.logger.info(f"Atualizando estrutura da tabela {table_name} preservando dados...")
            
            # Nomes das tabelas temporárias
            import random
            suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
            temp_table = f"temp_repl_{table_name}_{suffix}"
            backup_table = f"backup_repl_{table_name}_{suffix}"
            
            # Desabilitar verificações de FK temporariamente
            self.target_db.execute_query("SET FOREIGN_KEY_CHECKS = 0", fetch_results=False)
            
            try:
                # 1. Criar tabela temporária com nova estrutura (sem FKs)
                temp_create_statement = self._clean_create_statement_for_temp(new_create_statement, temp_table)
                
                self.logger.debug(f"Criando tabela temporária {temp_table}")
                self.target_db.create_table_from_statement(temp_create_statement)
                
                # 2. Obter estrutura da tabela original e nova
                original_columns = [col['name'] for col in self.target_db.get_table_columns(table_name)]
                new_columns = [col['name'] for col in self.target_db.get_table_columns(temp_table)]
                
                # 3. Encontrar colunas em comum
                common_columns = [col for col in original_columns if col in new_columns]
                
                if common_columns:
                    # Configurar modo SQL para preservar valores 0 em colunas AUTO_INCREMENT
                    self.target_db.set_zero_preserve_mode(True)
                    
                    # 4. Copiar dados compatíveis para tabela temporária
                    columns_str = ", ".join([f"`{col}`" for col in common_columns])
                    
                    copy_query = f"""
                    INSERT INTO `{temp_table}` ({columns_str})
                    SELECT {columns_str}
                    FROM `{table_name}`
                    """
                    
                    self.logger.debug(f"Copiando dados de {len(common_columns)} colunas comuns: {common_columns}")
                    self.target_db.execute_query(copy_query, fetch_results=False)
                    
                    # Verifica quantos registros foram copiados
                    count_query = f"SELECT COUNT(*) as count FROM `{temp_table}`"
                    result = self.target_db.execute_query(count_query)
                    copied_records = result[0]['count'] if result else 0
                    
                    self.logger.info(f"Copiados {copied_records} registros preservando dados existentes")
                else:
                    self.logger.warning(f"Nenhuma coluna em comum encontrada entre estruturas antiga e nova de {table_name}")
                
                # 5. Fazer backup da tabela original (para segurança)
                self.logger.debug(f"Renomeando tabela original para backup: {backup_table}")
                rename_to_backup_query = f"RENAME TABLE `{table_name}` TO `{backup_table}`"
                self.target_db.execute_query(rename_to_backup_query, fetch_results=False)
                
                # 6. Renomear tabela temporária para o nome original
                self.logger.debug(f"Renomeando tabela temporária {temp_table} para {table_name}")
                rename_temp_query = f"RENAME TABLE `{temp_table}` TO `{table_name}`"
                self.target_db.execute_query(rename_temp_query, fetch_results=False)
                
                # Marcar temp_table como None já que foi renomeado
                temp_table = None
                
                # 7. Remover tabela de backup (opcional - pode manter para segurança)
                self.logger.debug(f"Removendo tabela de backup {backup_table}")
                self.target_db.drop_table_if_exists(backup_table)
                backup_table = None
                
                self.logger.info(f"Estrutura de {table_name} atualizada com sucesso, dados preservados")
                
            finally:
                # Reabilitar verificações de FK
                self.target_db.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch_results=False)
                # Restaurar modo SQL padrão
                try:
                    self.target_db.set_zero_preserve_mode(False)
                except:
                    pass
                
        except Exception as e:
            # Em caso de erro, tenta fazer cleanup
            self.logger.error(f"Erro durante atualização estrutural de {table_name}: {e}")
            
            try:
                # Desabilitar FK checks para cleanup
                self.target_db.execute_query("SET FOREIGN_KEY_CHECKS = 0", fetch_results=False)
                
                # Remove tabela temporária se existir
                if temp_table and self.target_db.table_exists(temp_table):
                    self.target_db.drop_table_if_exists(temp_table)
                
                # Se tiver renomeado a original, tenta restaurar
                if backup_table and self.target_db.table_exists(backup_table):
                    # Se tabela original não existe, restaura do backup
                    if not self.target_db.table_exists(table_name):
                        restore_query = f"RENAME TABLE `{backup_table}` TO `{table_name}`"
                        self.target_db.execute_query(restore_query, fetch_results=False)
                        self.logger.info(f"Tabela {table_name} restaurada do backup após erro")
                    else:
                        # Remove backup já que tabela original existe
                        self.target_db.drop_table_if_exists(backup_table)
                
            except Exception as cleanup_error:
                self.logger.error(f"Erro durante cleanup de {table_name}: {cleanup_error}")
            finally:
                # Reabilitar FK checks
                try:
                    self.target_db.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch_results=False)
                except:
                    pass
            
            # Re-lança a exceção original
            raise ReplicationError(f"Erro na atualização estrutural de {table_name}: {e}")