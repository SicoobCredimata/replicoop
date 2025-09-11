#!/usr/bin/env python3
"""
ReplicOOP - Sistema Profissional de Replicação de Estrutura MySQL
Autor: Marcus Geraldino
Versão: 1.0.0

Sistema para replicação de estruturas de banco de dados MySQL com:
- Backup automático antes de operações
- Tratamento inteligente de chaves estrangeiras
- Logs detalhados
- Validação de replicação
- Menu interativo profissional
"""

import os
import sys
from typing import List, Optional
from datetime import datetime

# Adiciona o diretório core ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.replication import ReplicationManager, ReplicationError
    from core.logger import LoggerManager
    from core.config import ConfigManager
    from core.restore import RestoreManager, RestoreError
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("💡 Verifique se as dependências estão instaladas:")
    print("   pip install -r requirements.txt")
    input("Pressione Enter para sair...")
    sys.exit(1)


#!/usr/bin/env python3
"""
ReplicOOP - Sistema Profissional de Replicação de Estrutura MySQL
Autor: Marcus Geraldino
Versão: 1.0.0

Sistema para replicação de estruturas de banco de dados MySQL com:
- Backup automático antes de operações
- Tratamento inteligente de chaves estrangeiras
- Logs detalhados
- Validação de replicação
- Menu interativo profissional
"""

import os
import sys
from typing import List, Optional
from datetime import datetime

# Adiciona o diretório core ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.replication import ReplicationManager, ReplicationError
    from core.logger import LoggerManager
    from core.config import ConfigManager
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("💡 Verifique se as dependências estão instaladas:")
    print("   pip install -r requirements.txt")
    input("Pressione Enter para sair...")
    sys.exit(1)


class ReplicOOPMenu:
    """Menu interativo principal do ReplicOOP"""
    
    def __init__(self):
        """Inicializa o menu"""
        self.replication_manager = None
        self.restore_manager = None
        self.logger = LoggerManager()
        self.config_path = "config.json"
        
    def clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Imprime cabeçalho do sistema"""
        print("\n" + "="*70)
        print("🚀 ReplicOOP - Sistema de Replicação MySQL v1.0.0")
        print("   Sistema Profissional de Replicação de Estruturas")
        print("="*70)
    
    def print_main_menu(self):
        """Imprime menu principal"""
        print("\n📋 MENU PRINCIPAL")
        print("-" * 50)
        print("🔄 OPERAÇÕES DE REPLICAÇÃO:")
        print("  [1] - Replicar Estruturas (com opções)")
        print("  [2] - Replicar Tudo (estrutura + dados das tabelas maintain)")
        print("  [3] - Validar Replicação")
        print()
        print("💾 OPERAÇÕES DE BACKUP:")
        print("  [4] - Criar Backup Manual")
        print("  [5] - Listar Backups Disponíveis")
        print()
        print("� OPERAÇÕES DE RESTAURAÇÃO:")
        print("  [6] - Restaurar Backup (Avançado)")
        print("  [7] - Analisar Backup")
        print("  [8] - Comparar Backup com Estado Atual")
        print()
        print("�🔧 CONFIGURAÇÕES E TESTES:")
        print("  [9] - Testar Conexões")
        print("  [10] - Ver Plano de Replicação")
        print("  [11] - Configurar Sistema")
        print()
        print("📊 RELATÓRIOS E LOGS:")
        print("  [12] - Ver Logs")
        print("  [13] - Estatísticas do Sistema")
        print()
        print("  [0] - ❌ Sair")
        print("-" * 50)
    
    def wait_for_user(self):
        """Aguarda input do usuário"""
        print("\n" + "="*70)
        input("📌 Pressione Enter para continuar...")
    
    def get_user_choice(self, min_val: int = 0, max_val: int = 13) -> int:
        """Obtém escolha do usuário"""
        while True:
            try:
                choice = input(f"\n🎯 Digite sua escolha ({min_val}-{max_val}): ").strip()
                if choice == "":
                    continue
                
                choice_int = int(choice)
                if min_val <= choice_int <= max_val:
                    return choice_int
                else:
                    print(f"❌ Escolha deve estar entre {min_val} e {max_val}")
            except ValueError:
                print("❌ Digite apenas números")
            except KeyboardInterrupt:
                print("\n\n👋 Sistema encerrado pelo usuário")
                sys.exit(0)
    
    def initialize_manager(self) -> bool:
        """Inicializa os gerenciadores do sistema"""
        try:
            if not os.path.exists(self.config_path):
                print(f"❌ Arquivo de configuração não encontrado: {self.config_path}")
                print("💡 Crie o arquivo config.json com suas configurações de banco")
                return False
            
            self.replication_manager = ReplicationManager(self.config_path)
            
            # Setup básico dos bancos para ter os managers disponíveis
            self.replication_manager.setup_databases("sandbox", "production")
            
            # Inicializa o RestoreManager
            if hasattr(self.replication_manager, 'backup_manager') and self.replication_manager.target_db:
                self.restore_manager = RestoreManager(
                    db_manager=self.replication_manager.target_db,
                    backup_manager=self.replication_manager.backup_manager,
                    logger=self.replication_manager.logger
                )
            
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar sistema: {e}")
            return False
    
    def select_environments(self) -> tuple:
        """Seleciona ambientes de origem e destino"""
        config_manager = ConfigManager(self.config_path)
        environments = config_manager.get_available_environments()
        
        print("\n🔧 SELEÇÃO DE AMBIENTES")
        print("-" * 30)
        
        # Ambiente de origem
        print("\n📤 Selecione o ambiente de ORIGEM:")
        for i, env in enumerate(environments, 1):
            print(f"  [{i}] - {env.capitalize()}")
        
        source_choice = self.get_user_choice(1, len(environments))
        source_env = environments[source_choice - 1]
        
        # Ambiente de destino
        print(f"\n📥 Selecione o ambiente de DESTINO:")
        for i, env in enumerate(environments, 1):
            indicator = " (origem)" if env == source_env else ""
            print(f"  [{i}] - {env.capitalize()}{indicator}")
        
        target_choice = self.get_user_choice(1, len(environments))
        target_env = environments[target_choice - 1]
        
        if source_env == target_env:
            print("⚠️  Origem e destino são iguais! Confirme se está correto.")
            confirm = input("Continuar mesmo assim? (s/N): ").lower().strip()
            if confirm != 's':
                return self.select_environments()
        
        print(f"\n✅ Selecionado: {source_env} → {target_env}")
        return source_env, target_env
    
    def select_tables(self) -> Optional[List[str]]:
        """Seleciona tabelas para operação"""
        print("\n📋 SELEÇÃO DE TABELAS")
        print("-" * 30)
        print("  [1] - Usar configuração (tabelas do config.json)")
        print("  [2] - Especificar tabelas manualmente")
        print("  [3] - Todas as tabelas do banco origem")
        
        choice = self.get_user_choice(1, 3)
        
        if choice == 1:
            return None  # Usa configuração
        elif choice == 2:
            tables_input = input("\n📝 Digite as tabelas separadas por vírgula: ").strip()
            if tables_input:
                tables = [t.strip() for t in tables_input.split(',') if t.strip()]
                print(f"✅ {len(tables)} tabelas selecionadas: {', '.join(tables)}")
                return tables
            return None
        else:
            print("✅ Todas as tabelas do banco origem serão processadas")
            return []  # Lista vazia indica todas as tabelas
    
    def option_replicate_with_options(self):
        """Opção 1: Replicar com opções"""
        print("\n🔄 REPLICAÇÃO PERSONALIZADA")
        print("="*50)
        
        if not self.initialize_manager():
            return
        
        # Selecionar ambientes
        source_env, target_env = self.select_environments()
        
        # Selecionar tabelas  
        tables = self.select_tables()
        
        # Configurar backup
        print("\n💾 CONFIGURAÇÃO DE BACKUP")
        print("-" * 30)
        backup_choice = input("Criar backup antes da replicação? (S/n): ").lower().strip()
        create_backup = backup_choice != 'n'
        
        # Confirmar operação
        print(f"\n📋 RESUMO DA OPERAÇÃO:")
        print(f"   Origem: {source_env}")
        print(f"   Destino: {target_env}")
        if tables is None:
            print(f"   Tabelas: Usando configuração (maintain)")
        elif len(tables) == 0:
            print(f"   Tabelas: Todas do banco origem")
        else:
            print(f"   Tabelas: {', '.join(tables)}")
        print(f"   Backup: {'Sim' if create_backup else 'Não'}")
        
        confirm = input(f"\n❓ Confirma a replicação? (s/N): ").lower().strip()
        if confirm != 's':
            print("❌ Operação cancelada")
            return
        
        # Executar replicação
        try:
            print(f"\n🚀 Iniciando replicação...")
            self.replication_manager.setup_databases(source_env, target_env)
            
            result = self.replication_manager.execute_replication(
                tables=tables,
                create_backup=create_backup,
                replicate_data=False  # Apenas estrutura nesta opção
            )
            
            # Mostrar resultados
            self.show_replication_results(result)
            
        except Exception as e:
            print(f"\n❌ Erro durante replicação: {e}")
    
    def option_replicate_all(self):
        """Opção 2: Replicar tudo (estrutura + dados)"""
        print("\n🔄 REPLICAÇÃO COMPLETA")
        print("="*50)
        print("ℹ️  Esta opção replica:")
        print("   • ESTRUTURA de todas as tabelas")
        print("   • DADOS apenas das tabelas listadas em 'maintain'")
        
        if not self.initialize_manager():
            return
        
        # Selecionar ambientes
        source_env, target_env = self.select_environments()
        
        # Confirmar operação
        print(f"\n⚠️  ATENÇÃO: Esta operação irá:")
        print(f"   1. Fazer backup do ambiente {target_env}")
        print(f"   2. Replicar TODAS as estruturas de {source_env}")
        print(f"   3. Replicar DADOS das tabelas 'maintain'")
        print(f"   4. Pode demorar bastante dependendo do tamanho dos dados")
        
        confirm = input(f"\n❓ Confirma a replicação COMPLETA? (s/N): ").lower().strip()
        if confirm != 's':
            print("❌ Operação cancelada")
            return
        
        # Executar replicação completa
        try:
            print(f"\n🚀 Iniciando replicação completa...")
            self.replication_manager.setup_databases(source_env, target_env)
            
            # Replicação completa: estrutura de todas + dados das maintain
            result = self.replication_manager.execute_replication(
                tables=None,  # Todas as tabelas (usa config)
                create_backup=True,
                replicate_data=True  # Replica dados das tabelas maintain
            )
            
            self.show_replication_results(result)
            
        except Exception as e:
            print(f"\n❌ Erro durante replicação: {e}")
    
    def option_validate(self):
        """Opção 3: Validar replicação"""
        print("\n🔍 VALIDAÇÃO DE REPLICAÇÃO")
        print("="*50)
        
        if not self.initialize_manager():
            return
        
        source_env, target_env = self.select_environments()
        tables = self.select_tables()
        
        try:
            self.replication_manager.setup_databases(source_env, target_env)
            result = self.replication_manager.validate_replication(tables)
            
            self.show_validation_results(result)
            
        except Exception as e:
            print(f"\n❌ Erro durante validação: {e}")
    
    def option_backup(self):
        """Opção 4: Criar backup manual"""
        print("\n💾 BACKUP MANUAL")
        print("="*50)
        
        if not self.initialize_manager():
            return
        
        config_manager = ConfigManager(self.config_path)
        environments = config_manager.get_available_environments()
        print("\n📤 Selecione o ambiente para backup:")
        for i, env in enumerate(environments, 1):
            print(f"  [{i}] - {env.capitalize()}")
        
        env_choice = self.get_user_choice(1, len(environments))
        environment = environments[env_choice - 1]
        
        try:
            self.replication_manager.setup_databases(target_env=environment)
            backup_path = self.replication_manager.create_backup_before_replication(environment)
            
            print(f"\n✅ Backup criado com sucesso!")
            print(f"📁 Arquivo: {os.path.basename(backup_path)}")
            
        except Exception as e:
            print(f"\n❌ Erro ao criar backup: {e}")
    
    def option_list_backups(self):
        """Opção 5: Listar backups"""
        print("\n📦 BACKUPS DISPONÍVEIS")
        print("="*50)
        
        try:
            config_manager = ConfigManager(self.config_path)
            logger = LoggerManager(logs_path=config_manager.get_logs_path())
            
            from core.backup import BackupManager
            backup_manager = BackupManager(None, logger, config_manager.get_backup_path())
            
            backups = backup_manager.list_backups()
            
            if not backups:
                print("📭 Nenhum backup encontrado")
                return
            
            print(f"\n📋 {len(backups)} backups encontrados:\n")
            
            for i, backup in enumerate(backups, 1):
                timestamp = datetime.fromisoformat(backup.get('timestamp', ''))
                size_mb = backup.get('size_bytes', 0) / 1024 / 1024
                
                print(f"[{i:2d}] 📁 {backup.get('backup_file', 'N/A')}")
                print(f"     🗄️  Banco: {backup.get('database', 'N/A')}")
                print(f"     🏷️  Ambiente: {backup.get('environment', 'N/A')}")
                print(f"     📅 Data: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"     📏 Tamanho: {size_mb:.1f} MB")
                print()
            
        except Exception as e:
            print(f"\n❌ Erro ao listar backups: {e}")
    
    def option_test_connections(self):
        """Opção 6: Testar conexões"""
        print("\n🔌 TESTE DE CONEXÕES")
        print("="*50)
        
        try:
            config_manager = ConfigManager(self.config_path)
            logger = LoggerManager()
            
            from core.database import DatabaseManager
            
            config_manager = ConfigManager(self.config_path)
            environments = config_manager.get_available_environments()
            results = {}
            
            print("\n🧪 Testando conexões com todos os ambientes...\n")
            
            for env in environments:
                try:
                    print(f"⏳ Testando {env}...", end=" ")
                    config = config_manager.get_database_config(env)
                    db_manager = DatabaseManager(config, logger)
                    
                    if db_manager.test_connection():
                        print("✅ OK")
                        results[env] = True
                    else:
                        print("❌ FALHA")
                        results[env] = False
                        
                except Exception as e:
                    print(f"❌ ERRO: {str(e)[:50]}...")
                    results[env] = False
            
            # Resumo
            success_count = sum(1 for r in results.values() if r)
            total_count = len(results)
            
            print(f"\n📊 RESULTADO: {success_count}/{total_count} conexões bem-sucedidas")
            
            if success_count < total_count:
                print("\n⚠️  Problemas encontrados:")
                for env, success in results.items():
                    if not success:
                        print(f"   • {env}: Verifique configurações e conectividade")
            
        except Exception as e:
            print(f"\n❌ Erro no teste de conexões: {e}")
    
    def option_show_plan(self):
        """Opção 7: Ver plano de replicação"""
        print("\n📋 PLANO DE REPLICAÇÃO")
        print("="*50)
        
        if not self.initialize_manager():
            return
        
        source_env, target_env = self.select_environments()
        tables = self.select_tables()
        
        try:
            self.replication_manager.setup_databases(source_env, target_env)
            plan = self.replication_manager.get_replication_plan(tables)
            
            self.show_replication_plan(plan)
            
        except Exception as e:
            print(f"\n❌ Erro ao gerar plano: {e}")
    
    def option_configure(self):
        """Opção 8: Configurar sistema"""
        print("\n⚙️  CONFIGURAÇÃO DO SISTEMA")
        print("="*50)
        
        if os.path.exists(self.config_path):
            print(f"✅ Arquivo de configuração encontrado: {self.config_path}")
            
            choice = input("\nO que deseja fazer?\n"
                          "  [1] - Ver configurações atuais\n"
                          "  [2] - Abrir arquivo para edição\n"
                          "  [3] - Criar novo arquivo\n"
                          "Escolha: ").strip()
            
            if choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.open_config_file()
            elif choice == "3":
                self.create_new_config()
        else:
            print(f"❌ Arquivo de configuração não encontrado: {self.config_path}")
            choice = input("Deseja criar um novo? (s/N): ").lower().strip()
            if choice == 's':
                self.create_new_config()
    
    def option_view_logs(self):
        """Opção 9: Ver logs"""
        print("\n📊 LOGS DO SISTEMA")
        print("="*50)
        
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            print("📭 Pasta de logs não encontrada")
            return
        
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        
        if not log_files:
            print("📭 Nenhum arquivo de log encontrado")
            return
        
        log_files.sort(reverse=True)
        
        print(f"\n📋 {len(log_files)} arquivos de log encontrados:")
        for i, log_file in enumerate(log_files[:5], 1):  # Mostra últimos 5
            print(f"  [{i}] - {log_file}")
        
        if len(log_files) > 5:
            print(f"  ... e mais {len(log_files) - 5} arquivos")
        
        print(f"\n💡 Para ver logs detalhados, abra a pasta: {os.path.abspath(logs_dir)}")
        
        choice = input("\nAbrir pasta de logs? (s/N): ").lower().strip()
        if choice == 's':
            if os.name == 'nt':  # Windows
                os.system(f'explorer "{os.path.abspath(logs_dir)}"')
            else:  # Unix/Linux/Mac
                os.system(f'xdg-open "{os.path.abspath(logs_dir)}"')
    
    def option_statistics(self):
        """Opção 10: Estatísticas do sistema"""
        print("\n📊 ESTATÍSTICAS DO SISTEMA")
        print("="*50)
        
        try:
            # Estatísticas de backups
            config_manager = ConfigManager(self.config_path)
            from core.backup import BackupManager
            
            backup_manager = BackupManager(None, self.logger, config_manager.get_backup_path())
            backups = backup_manager.list_backups()
            
            print(f"\n💾 BACKUPS:")
            print(f"   Total de backups: {len(backups)}")
            
            if backups:
                total_size = sum(b.get('size_bytes', 0) for b in backups)
                print(f"   Espaço utilizado: {total_size / 1024 / 1024:.1f} MB")
                
                latest = backups[0]
                latest_date = datetime.fromisoformat(latest['timestamp'])
                print(f"   Último backup: {latest_date.strftime('%d/%m/%Y %H:%M')}")
            
            # Estatísticas de logs
            logs_dir = "logs"
            if os.path.exists(logs_dir):
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
                print(f"\n📋 LOGS:")
                print(f"   Arquivos de log: {len(log_files)}")
                
                if log_files:
                    total_log_size = sum(
                        os.path.getsize(os.path.join(logs_dir, f)) 
                        for f in log_files
                    )
                    print(f"   Espaço utilizado: {total_log_size / 1024 / 1024:.1f} MB")
            
            # Estatísticas de configuração
            if os.path.exists(self.config_path):
                config_manager = ConfigManager(self.config_path)
                maintain_tables = config_manager.get_maintain_tables()
                
                print(f"\n⚙️  CONFIGURAÇÃO:")
                print(f"   Tabelas em maintain: {len(maintain_tables)}")
                print(f"   Arquivo config: {self.config_path}")
            
        except Exception as e:
            print(f"\n❌ Erro ao obter estatísticas: {e}")
    
    def show_replication_results(self, result: dict):
        """Mostra resultados da replicação"""
        print(f"\n" + "="*60)
        print("📊 RELATÓRIO DE REPLICAÇÃO")
        print("="*60)
        
        status = "✅ SUCESSO" if result['success'] else "❌ FALHAS ENCONTRADAS"
        print(f"\n🏆 Status: {status}")
        print(f"📊 Tabelas processadas: {result['tables_replicated']}")
        
        if result.get('data_replicated_tables'):
            print(f"🔄 Tabelas com dados replicados: {len(result['data_replicated_tables'])}")
        
        print(f"⏱️  Tempo de execução: {result['execution_time']:.2f}s")
        
        if result.get('backup_created'):
            backup_name = os.path.basename(result['backup_created'])
            print(f"💾 Backup criado: {backup_name}")
        
        if result.get('replicated_tables'):
            print(f"\n✅ Tabelas Replicadas ({len(result['replicated_tables'])}):")
            for i, table in enumerate(result['replicated_tables'], 1):
                print(f"   {i:2d}. {table}")
        
        if result.get('data_replicated_tables'):
            print(f"\n🔄 Tabelas com Dados Replicados ({len(result['data_replicated_tables'])}):")
            for i, table in enumerate(result['data_replicated_tables'], 1):
                print(f"   {i:2d}. {table}")
        
        if result.get('failed_tables'):
            print(f"\n❌ Tabelas com Falha ({len(result['failed_tables'])}):")
            for i, failed in enumerate(result['failed_tables'], 1):
                error_short = failed['error'][:60] + "..." if len(failed['error']) > 60 else failed['error']
                print(f"   {i:2d}. {failed['table']}: {error_short}")
    
    def show_validation_results(self, result: dict):
        """Mostra resultados da validação"""
        print(f"\n" + "="*60)
        print("🔍 RELATÓRIO DE VALIDAÇÃO")
        print("="*60)
        
        matches = len(result['structure_matches'])
        differences = len(result['structure_differences'])
        missing = len(result['missing_tables'])
        
        print(f"\n📊 RESUMO:")
        print(f"   Tabelas validadas: {result['tables_validated']}")
        print(f"   ✅ Estruturas idênticas: {matches}")
        print(f"   ⚠️  Com diferenças: {differences}")
        print(f"   ❌ Tabelas ausentes: {missing}")
        
        if result['structure_differences']:
            print(f"\n⚠️  DIFERENÇAS ENCONTRADAS:")
            for diff in result['structure_differences']:
                print(f"\n🔸 Tabela: {diff['table']}")
                for difference in diff['differences'][:3]:  # Mostra até 3 diferenças
                    print(f"   • {difference}")
                if len(diff['differences']) > 3:
                    print(f"   • ... e mais {len(diff['differences']) - 3} diferenças")
        
        if result['missing_tables']:
            print(f"\n❌ TABELAS AUSENTES NO DESTINO:")
            for table in result['missing_tables']:
                print(f"   • {table}")
    
    def show_replication_plan(self, plan: dict):
        """Mostra plano de replicação"""
        print(f"\n" + "="*60)
        print("📋 PLANO DE REPLICAÇÃO")
        print("="*60)
        
        timestamp = datetime.fromisoformat(plan['timestamp'])
        
        print(f"\n📊 RESUMO:")
        print(f"   Data/Hora: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   Tabelas no origem: {plan['source_tables']}")
        print(f"   Tabelas no destino: {plan['target_tables']}")
        print(f"   Tabelas para replicar: {len(plan['tables_to_replicate'])}")
        print(f"   Problemas com FK: {len(plan['foreign_key_issues'])}")
        
        if plan['tables_to_replicate']:
            print(f"\n📋 TABELAS PARA REPLICAÇÃO:")
            for i, table in enumerate(plan['tables_to_replicate'][:10], 1):  # Mostra até 10
                fk_info = f"(FK: {len(table['foreign_keys'])})" if table['has_foreign_keys'] else ""
                action_emoji = "🆕" if table['action'] == 'create' else "🔄"
                print(f"   {i:2d}. {action_emoji} {table['name']} {fk_info}")
            
            if len(plan['tables_to_replicate']) > 10:
                remaining = len(plan['tables_to_replicate']) - 10
                print(f"   ... e mais {remaining} tabelas")
        
        if plan['foreign_key_issues']:
            print(f"\n⚠️  PROBLEMAS COM CHAVES ESTRANGEIRAS:")
            for issue in plan['foreign_key_issues']:
                print(f"   • {issue}")
        
        if plan['warnings']:
            print(f"\n⚠️  AVISOS:")
            for warning in plan['warnings']:
                print(f"   • {warning}")
    
    def show_current_config(self):
        """Mostra configuração atual"""
        try:
            config_manager = ConfigManager(self.config_path)
            
            print(f"\n⚙️  CONFIGURAÇÃO ATUAL:")
            print(f"   Arquivo: {self.config_path}")
            
            # Mostra ambientes configurados
            environments = config_manager.get_available_environments()
            print(f"\n🗄️  AMBIENTES CONFIGURADOS:")
            
            for env in environments:
                try:
                    config = config_manager.get_database_config(env)
                    print(f"   ✅ {env}: {config.host}:{config.port}/{config.dbname}")
                except:
                    print(f"   ❌ {env}: Não configurado")
            
            # Mostra tabelas maintain
            maintain_tables = config_manager.get_maintain_tables()
            print(f"\n📋 TABELAS MAINTAIN ({len(maintain_tables)}):")
            if maintain_tables:
                for i, table in enumerate(maintain_tables, 1):
                    print(f"   {i:2d}. {table}")
            else:
                print("   📭 Nenhuma tabela configurada (todas serão consideradas)")
                
        except Exception as e:
            print(f"\n❌ Erro ao ler configuração: {e}")
    
    def open_config_file(self):
        """Abre arquivo de configuração para edição"""
        if os.name == 'nt':  # Windows
            os.system(f'notepad "{self.config_path}"')
        else:  # Unix/Linux/Mac
            os.system(f'nano "{self.config_path}"')
        
        print("💡 Arquivo aberto no editor. Salve e feche para continuar.")
    
    def create_new_config(self):
        """Cria novo arquivo de configuração"""
        sample_config = '''{
    "production": {
        "host": "localhost",
        "port": 3306,
        "username": "user_prod",
        "password": "senha_prod", 
        "dbname": "banco_producao",
        "charset": "utf8mb4"
    },
    "sandbox": {
        "host": "localhost",
        "port": 3306,
        "username": "user_test",
        "password": "senha_test",
        "dbname": "banco_teste", 
        "charset": "utf8mb4"
    },
    "maintain": [
        "usuarios",
        "produtos",
        "categorias"
    ]
}'''
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(sample_config)
            
            print(f"✅ Arquivo {self.config_path} criado com configuração de exemplo")
            print("⚠️  IMPORTANTE: Edite o arquivo com suas configurações reais!")
            
            choice = input("\nAbrir arquivo para edição agora? (s/N): ").lower().strip()
            if choice == 's':
                self.open_config_file()
                
        except Exception as e:
            print(f"❌ Erro ao criar arquivo: {e}")
    
    def option_restore_backup(self):
        """Opção para restaurar backup"""
        if not self.initialize_manager():
            return
        
        if not self.restore_manager:
            print("❌ Gerenciador de restauração não inicializado")
            return
        
        try:
            print("\n🔙 RESTAURAÇÃO AVANÇADA DE BACKUP")
            print("="*50)
            
            # Lista backups disponíveis
            backups = self.restore_manager.list_available_backups()
            
            if not backups:
                print("❌ Nenhum backup disponível para restauração")
                return
            
            print(f"\n📋 Backups Disponíveis ({len(backups)}):")
            print("-" * 70)
            
            for i, backup in enumerate(backups, 1):
                recommended = "⭐ " if backup.get('recommended') else "   "
                print(f"{recommended}[{i:2}] {backup['backup_file']}")
                print(f"      📅 {backup.get('age_description', 'N/A')} | 💾 {backup.get('size_formatted', 'N/A')}")
                print(f"      🗂️  {backup.get('backup_type', 'N/A').title()} | 🏷️  {backup.get('environment', 'N/A')}")
                print()
            
            # Seleção do backup
            choice = self.get_user_choice(1, len(backups))
            selected_backup = backups[choice - 1]
            backup_path = selected_backup['backup_path']
            
            print(f"\n✅ Backup selecionado: {selected_backup['backup_file']}")
            
            # Opções de restauração
            print("\n⚙️ OPÇÕES DE RESTAURAÇÃO:")
            print("  [1] - Restauração Rápida (sem validações)")
            print("  [2] - Restauração Segura (com backup de segurança)")
            print("  [3] - Simulação (dry-run)")
            print("  [4] - Análise detalhada primeiro")
            
            restore_choice = self.get_user_choice(1, 4)
            
            if restore_choice == 4:
                # Análise primeiro
                self._show_backup_analysis(backup_path)
                
                confirm = input("\nContinuar com a restauração? (s/N): ").lower().strip()
                if confirm != 's':
                    return
                
                restore_choice = 2  # Mudanças para segura após análise
            
            # Configurações baseadas na escolha
            if restore_choice == 1:
                # Rápida
                safety_backup = False
                validate = False
                force = True
                dry_run = False
            elif restore_choice == 2:
                # Segura
                safety_backup = True
                validate = True
                force = False
                dry_run = False
            else:  # 3 - Simulação
                safety_backup = False
                validate = True
                force = False
                dry_run = True
            
            # Confirmação final
            if not dry_run:
                print(f"\n⚠️  ATENÇÃO: Esta operação irá {'substituir' if restore_choice == 1 else 'restaurar'} o banco de dados atual!")
                print(f"📂 Banco alvo: {self.replication_manager.db_manager_target.config.dbname}")
                
                if restore_choice == 2:
                    print("💾 Backup de segurança será criado antes da restauração")
                
                confirm = input("\nConfirma a restauração? (CONFIRMO/N): ").strip()
                if confirm != "CONFIRMO":
                    print("❌ Restauração cancelada")
                    return
            
            # Executa restauração
            print(f"\n🔄 Iniciando {'simulação de' if dry_run else ''} restauração...")
            
            result = self.restore_manager.restore_backup_advanced(
                backup_filepath=backup_path,
                create_safety_backup=safety_backup,
                validate_before_restore=validate,
                force_restore=force,
                dry_run=dry_run
            )
            
            # Mostra resultados
            print(f"\n{'🎯 SIMULAÇÃO' if dry_run else '✅ RESTAURAÇÃO'} CONCLUÍDA!")
            print("-" * 50)
            print(f"📁 Arquivo: {result['backup_file']}")
            print(f"⏱️  Duração: {result['restore_duration']:.2f} segundos")
            print(f"📊 Tabelas: {result['tables_restored']}")
            
            if not dry_run:
                print(f"📝 Registros: {result.get('records_restored', 'N/A')}")
                
                if result.get('safety_backup_created'):
                    print(f"💾 Backup segurança: {os.path.basename(result['safety_backup_created'])}")
            
            if result.get('warnings'):
                print(f"\n⚠️  Avisos ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    print(f"   • {warning}")
            
            if dry_run:
                print("\n💡 Esta foi apenas uma simulação. Use opção 1 ou 2 para restauração real.")
            
        except RestoreError as e:
            print(f"❌ Erro na restauração: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
    
    def option_analyze_backup(self):
        """Opção para analisar backup"""
        if not self.initialize_manager():
            return
        
        if not self.restore_manager:
            print("❌ Gerenciador de restauração não inicializado")
            return
        
        try:
            print("\n🔍 ANÁLISE DE BACKUP")
            print("="*40)
            
            # Lista backups disponíveis
            backups = self.restore_manager.list_available_backups()
            
            if not backups:
                print("❌ Nenhum backup disponível para análise")
                return
            
            print(f"\n📋 Selecione o backup para análise:")
            for i, backup in enumerate(backups, 1):
                print(f"  [{i}] {backup['backup_file']} ({backup.get('size_formatted', 'N/A')})")
            
            choice = self.get_user_choice(1, len(backups))
            selected_backup = backups[choice - 1]
            
            self._show_backup_analysis(selected_backup['backup_path'])
            
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
    
    def option_compare_backup(self):
        """Opção para comparar backup com estado atual"""
        if not self.initialize_manager():
            return
        
        if not self.restore_manager:
            print("❌ Gerenciador de restauração não inicializado")
            return
        
        try:
            print("\n⚖️  COMPARAÇÃO: BACKUP vs ESTADO ATUAL")
            print("="*50)
            
            # Lista backups disponíveis
            backups = self.restore_manager.list_available_backups()
            
            if not backups:
                print("❌ Nenhum backup disponível para comparação")
                return
            
            print(f"\n📋 Selecione o backup para comparação:")
            for i, backup in enumerate(backups, 1):
                print(f"  [{i}] {backup['backup_file']}")
            
            choice = self.get_user_choice(1, len(backups))
            selected_backup = backups[choice - 1]
            
            print(f"\n🔄 Analisando diferenças...")
            comparison = self.restore_manager.compare_backup_with_current(selected_backup['backup_path'])
            
            print(f"\n📊 RESULTADO DA COMPARAÇÃO")
            print("-" * 40)
            print(f"📁 Backup: {comparison['backup_file']}")
            print(f"📋 Tabelas no backup: {comparison['backup_tables_count']}")
            print(f"📋 Tabelas atuais: {comparison['current_tables_count']}")
            
            if comparison['tables_only_in_backup']:
                print(f"\n➕ Tabelas APENAS no backup ({len(comparison['tables_only_in_backup'])}):")
                for table in comparison['tables_only_in_backup']:
                    print(f"   • {table}")
            
            if comparison['tables_only_in_current']:
                print(f"\n➖ Tabelas APENAS no estado atual ({len(comparison['tables_only_in_current'])}):")
                for table in comparison['tables_only_in_current']:
                    print(f"   • {table}")
            
            if comparison['tables_in_both']:
                print(f"\n✅ Tabelas em AMBOS ({len(comparison['tables_in_both'])}):")
                # Mostra apenas algumas para não poluir a tela
                shown = comparison['tables_in_both'][:10]
                for table in shown:
                    print(f"   • {table}")
                
                if len(comparison['tables_in_both']) > 10:
                    print(f"   ... e mais {len(comparison['tables_in_both']) - 10} tabelas")
            
            print(f"\n💡 RECOMENDAÇÕES:")
            if comparison['recommendations']:
                for rec in comparison['recommendations']:
                    print(f"   • {rec}")
            else:
                print("   • Nenhuma recomendação específica")
            
        except Exception as e:
            print(f"❌ Erro na comparação: {e}")
    
    def _show_backup_analysis(self, backup_path: str):
        """Mostra análise detalhada de um backup"""
        try:
            print(f"\n🔍 Analisando backup...")
            analysis = self.restore_manager.analyze_backup(backup_path)
            
            print(f"\n📊 ANÁLISE DETALHADA")
            print("-" * 40)
            print(f"📁 Arquivo: {analysis['file_name']}")
            print(f"💾 Tamanho: {analysis['file_size']:,} bytes")
            print(f"📦 Comprimido: {'Sim' if analysis['is_compressed'] else 'Não'}")
            print(f"🗂️  Tabelas: {analysis['table_count']}")
            print(f"📝 Registros (estimativa): {analysis['estimated_records']:,}")
            
            if analysis.get('database_name'):
                print(f"🏷️  Banco origem: {analysis['database_name']}")
            
            if analysis.get('backup_date'):
                print(f"📅 Data backup: {analysis['backup_date']}")
            
            print(f"🔗 Foreign Keys: {'Sim' if analysis['has_foreign_keys'] else 'Não'}")
            print(f"⚡ Triggers: {'Sim' if analysis['has_triggers'] else 'Não'}")
            
            if analysis['tables_found']:
                print(f"\n📋 TABELAS ENCONTRADAS ({len(analysis['tables_found'])}):")
                # Mostra primeiras 15 tabelas
                shown_tables = analysis['tables_found'][:15]
                for i, table in enumerate(shown_tables, 1):
                    print(f"  {i:2}. {table}")
                
                if len(analysis['tables_found']) > 15:
                    remaining = len(analysis['tables_found']) - 15
                    print(f"  ... e mais {remaining} tabelas")
            
            # Validação de compatibilidade
            print(f"\n🔍 Validando compatibilidade...")
            validation = self.restore_manager.validate_backup_compatibility(backup_path)
            
            print(f"\n✅ COMPATIBILIDADE")
            print("-" * 20)
            print(f"Status: {'✅ Compatível' if validation['compatible'] else '❌ Incompatível'}")
            
            if validation['warnings']:
                print(f"\n⚠️  AVISOS ({len(validation['warnings'])}):")
                for warning in validation['warnings']:
                    print(f"   • {warning}")
            
            if validation['errors']:
                print(f"\n❌ ERROS ({len(validation['errors'])}):")
                for error in validation['errors']:
                    print(f"   • {error}")
            
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
    
    def run(self):
        """Executa o menu principal"""
        while True:
            try:
                self.clear_screen()
                self.print_header()
                self.print_main_menu()
                
                choice = self.get_user_choice(0, 13)
                
                if choice == 0:
                    print("\n👋 Obrigado por usar o ReplicOOP!")
                    break
                elif choice == 1:
                    self.option_replicate_with_options()
                elif choice == 2:
                    self.option_replicate_all()
                elif choice == 3:
                    self.option_validate()
                elif choice == 4:
                    self.option_backup()
                elif choice == 5:
                    self.option_list_backups()
                elif choice == 6:
                    self.option_restore_backup()
                elif choice == 7:
                    self.option_analyze_backup()
                elif choice == 8:
                    self.option_compare_backup()
                elif choice == 9:
                    self.option_test_connections()
                elif choice == 10:
                    self.option_show_plan()
                elif choice == 11:
                    self.option_configure()
                elif choice == 12:
                    self.option_view_logs()
                elif choice == 13:
                    self.option_statistics()
                
                if choice != 0:
                    self.wait_for_user()
                    
            except KeyboardInterrupt:
                print("\n\n👋 Sistema encerrado pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                self.wait_for_user()


def main():
    """Função principal do sistema"""
    try:
        menu = ReplicOOPMenu()
        menu.run()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)


if __name__ == "__main__":
    main()