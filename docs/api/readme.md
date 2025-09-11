# 📚 API Reference - ReplicOOP

## 🎯 Visão Geral da API

O **ReplicOOP** oferece uma API bem estruturada através de seus 6 módulos principais. Esta documentação fornece referência completa para desenvolvedores que precisam entender, manter ou estender o sistema.

## 📋 Índice dos Módulos

| Módulo | Descrição | Responsabilidade Principal |
|--------|-----------|---------------------------|
| [ReplicationManager](#-replicationmanager) | Motor principal | Orquestra todo o processo de replicação |
| [DatabaseManager](#-databasemanager) | Interface MySQL | Gerencia conexões e execução de queries |
| [BackupManager](#-backupmanager) | Sistema de backup | Cria e gerencia backups de segurança |
| [ConfigManager](#-configmanager) | Configurações | Carrega e valida configurações do sistema |
| [LoggerManager](#-loggermanager) | Sistema de logs | Registra operações e gera relatórios |
| [Utils](#-utils) | Utilitários | Funções auxiliares e helpers |

## 🎯 ReplicationManager

### Descrição
O `ReplicationManager` é o componente principal que orquestra todo o processo de replicação. Ele coordena os outros managers e implementa a lógica de negócio principal.

### Inicialização
```python
class ReplicationManager:
    def __init__(self):
        """Inicializa o ReplicationManager com dependências"""
        self.config_manager = ConfigManager()
        self.database_manager = DatabaseManager()
        self.backup_manager = BackupManager()
        self.logger_manager = LoggerManager()
        self.utils = Utils()
```

### Métodos Principais

#### `replicate_database(source_env, target_env)`
**Descrição**: Executa replicação completa entre ambientes.

**Parâmetros**:
- `source_env` (str): Ambiente de origem ('production', 'sandbox')
- `target_env` (str): Ambiente de destino ('production', 'sandbox')

**Retorna**: `dict` - Resultado da replicação com estatísticas

**Exceções**:
- `ConnectionError`: Falha na conexão com banco
- `ReplicationError`: Erro durante replicação
- `ValidationError`: Falha na validação

**Exemplo**:
```python
replication_manager = ReplicationManager()
result = replication_manager.replicate_database('production', 'sandbox')

# Resultado exemplo:
{
    'success': True,
    'tables_replicated': 15,
    'records_replicated': 1250,
    'execution_time': '00:02:45',
    'backup_created': 'backup_20241201_143022.sql.gz'
}
```

#### `replicate_structure_only(source_env, target_env)`
**Descrição**: Replica apenas as estruturas das tabelas (sem dados).

**Parâmetros**:
- `source_env` (str): Ambiente de origem
- `target_env` (str): Ambiente de destino

**Retorna**: `dict` - Resultado da replicação estrutural

**Exemplo**:
```python
result = replication_manager.replicate_structure_only('production', 'sandbox')
print(f"Estruturas replicadas: {result['tables_replicated']}")
```

#### `replicate_data_and_structure(source_env, target_env, maintain_only=False)`
**Descrição**: Replica estrutura e dados conforme configuração.

**Parâmetros**:
- `source_env` (str): Ambiente de origem
- `target_env` (str): Ambiente de destino
- `maintain_only` (bool): Se True, replica apenas tabelas maintain

**Retorna**: `dict` - Resultado da replicação completa

**Exemplo**:
```python
# Replica tudo conforme config.json
result = replication_manager.replicate_data_and_structure('production', 'sandbox')

# Replica apenas tabelas maintain
result = replication_manager.replicate_data_and_structure(
    'production', 'sandbox', maintain_only=True
)
```

#### `validate_environments()`
**Descrição**: Valida conectividade e configuração dos ambientes.

**Retorna**: `dict` - Status de validação de cada ambiente

**Exemplo**:
```python
validation = replication_manager.validate_environments()
for env, status in validation.items():
    print(f"{env}: {'✅' if status['connected'] else '❌'}")
```

#### `get_replication_status()`
**Descrição**: Retorna status atual do sistema de replicação.

**Retorna**: `dict` - Status detalhado do sistema

**Exemplo**:
```python
status = replication_manager.get_replication_status()
# {
#     'last_replication': '2024-12-01 14:30:22',
#     'tables_in_sync': 12,
#     'tables_out_of_sync': 3,
#     'backup_available': True
# }
```

### Métodos Internos (Privados)

#### `_execute_replication_plan(plan)`
**Descrição**: Executa plano de replicação estruturado.

#### `_handle_foreign_keys(table_name, action)`
**Descrição**: Gerencia foreign keys durante replicação.

#### `_validate_replication_result(result)`
**Descrição**: Valida resultado da replicação.

---

## 💾 DatabaseManager

### Descrição
O `DatabaseManager` gerencia todas as operações de banco de dados, incluindo conexões, execução de queries e transações.

### Inicialização
```python
class DatabaseManager:
    def __init__(self, config_manager=None):
        """Inicializa DatabaseManager"""
        self.config_manager = config_manager or ConfigManager()
        self._connections = {}
        self._connection_pools = {}
```

### Métodos de Conexão

#### `get_connection(environment)`
**Descrição**: Obtém conexão para ambiente específico.

**Parâmetros**:
- `environment` (str): Nome do ambiente ('production', 'sandbox')

**Retorna**: Objeto de conexão MySQL

**Exceções**:
- `ConnectionError`: Falha na conexão

**Exemplo**:
```python
db_manager = DatabaseManager()
conn = db_manager.get_connection('production')
```

#### `test_connection(environment)`
**Descrição**: Testa conectividade com ambiente.

**Parâmetros**:
- `environment` (str): Nome do ambiente

**Retorna**: `bool` - True se conexão bem-sucedida

**Exemplo**:
```python
if db_manager.test_connection('sandbox'):
    print("✅ Conexão sandbox OK")
else:
    print("❌ Falha na conexão sandbox")
```

### Métodos de Consulta

#### `execute_query(connection, query, params=None)`
**Descrição**: Executa query SQL com parâmetros.

**Parâmetros**:
- `connection`: Conexão de banco
- `query` (str): Query SQL
- `params` (tuple, optional): Parâmetros da query

**Retorna**: Lista de resultados

**Exemplo**:
```python
results = db_manager.execute_query(
    conn, 
    "SELECT * FROM users WHERE active = %s", 
    (1,)
)
```

#### `execute_scalar(connection, query, params=None)`
**Descrição**: Executa query que retorna um único valor.

**Parâmetros**:
- `connection`: Conexão de banco
- `query` (str): Query SQL
- `params` (tuple, optional): Parâmetros

**Retorna**: Valor único ou None

**Exemplo**:
```python
count = db_manager.execute_scalar(
    conn, 
    "SELECT COUNT(*) FROM users"
)
```

### Métodos de Estrutura

#### `get_all_tables(connection)`
**Descrição**: Retorna lista de todas as tabelas do banco.

**Parâmetros**:
- `connection`: Conexão de banco

**Retorna**: `list` - Lista de nomes de tabelas

**Exemplo**:
```python
tables = db_manager.get_all_tables(conn)
print(f"Encontradas {len(tables)} tabelas")
```

#### `get_table_structure(connection, table_name)`
**Descrição**: Retorna estrutura completa de uma tabela.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela

**Retorna**: `dict` - Estrutura da tabela

**Exemplo**:
```python
structure = db_manager.get_table_structure(conn, 'users')
# {
#     'columns': [...],
#     'indexes': [...],
#     'foreign_keys': [...],
#     'constraints': [...]
# }
```

#### `get_create_table_statement(connection, table_name)`
**Descrição**: Retorna statement CREATE TABLE.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela

**Retorna**: `str` - Statement SQL completo

### Métodos de Dados

#### `get_table_data(connection, table_name, batch_size=1000, offset=0)`
**Descrição**: Retorna dados de tabela em lotes.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela
- `batch_size` (int): Tamanho do lote
- `offset` (int): Deslocamento inicial

**Retorna**: `list` - Dados do lote

**Exemplo**:
```python
# Primeira página de 1000 registros
data = db_manager.get_table_data(conn, 'users', 1000, 0)
```

#### `insert_batch_data(connection, table_name, data)`
**Descrição**: Insere dados em lote.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela
- `data` (list): Lista de tuplas com dados

**Exemplo**:
```python
data = [
    (1, 'João', 'joao@email.com'),
    (2, 'Maria', 'maria@email.com')
]
db_manager.insert_batch_data(conn, 'users', data)
```

### Métodos de Manutenção

#### `drop_foreign_keys(connection, table_name)`
**Descrição**: Remove todas as foreign keys de uma tabela.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela

**Retorna**: `list` - Foreign keys removidas (para posterior recriação)

#### `create_foreign_keys(connection, table_name, foreign_keys)`
**Descrição**: Recria foreign keys em uma tabela.

**Parâmetros**:
- `connection`: Conexão de banco
- `table_name` (str): Nome da tabela
- `foreign_keys` (list): Lista de foreign keys

---

## 🛡️ BackupManager

### Descrição
O `BackupManager` é responsável por criar, gerenciar e restaurar backups de segurança do sistema.

### Inicialização
```python
class BackupManager:
    def __init__(self, config_manager=None, database_manager=None):
        """Inicializa BackupManager"""
        self.config_manager = config_manager or ConfigManager()
        self.database_manager = database_manager or DatabaseManager()
        self.backup_dir = "backups"
```

### Métodos de Backup

#### `create_backup(environment, compress=True)`
**Descrição**: Cria backup completo do banco de dados.

**Parâmetros**:
- `environment` (str): Ambiente a ser backupeado
- `compress` (bool): Se deve comprimir o backup

**Retorna**: `str` - Caminho do arquivo de backup criado

**Exceções**:
- `BackupError`: Falha na criação do backup

**Exemplo**:
```python
backup_manager = BackupManager()
backup_file = backup_manager.create_backup('sandbox', compress=True)
print(f"Backup criado: {backup_file}")
```

#### `create_table_backup(environment, table_name)`
**Descrição**: Cria backup de uma tabela específica.

**Parâmetros**:
- `environment` (str): Ambiente
- `table_name` (str): Nome da tabela

**Retorna**: `str` - Caminho do backup da tabela

**Exemplo**:
```python
table_backup = backup_manager.create_table_backup('sandbox', 'users')
```

### Métodos de Restauração

#### `restore_backup(backup_file, environment)`
**Descrição**: Restaura backup para ambiente específico.

**Parâmetros**:
- `backup_file` (str): Caminho do arquivo de backup
- `environment` (str): Ambiente de destino

**Exceções**:
- `RestoreError`: Falha na restauração

**Exemplo**:
```python
backup_manager.restore_backup('backup_20241201_143022.sql.gz', 'sandbox')
```

#### `list_available_backups()`
**Descrição**: Lista todos os backups disponíveis.

**Retorna**: `list` - Lista de backups com metadados

**Exemplo**:
```python
backups = backup_manager.list_available_backups()
for backup in backups:
    print(f"{backup['file']} - {backup['date']} - {backup['size']}")
```

### Métodos de Gerenciamento

#### `cleanup_old_backups(retention_days=7)`
**Descrição**: Remove backups antigos baseado na retenção.

**Parâmetros**:
- `retention_days` (int): Dias de retenção

**Retorna**: `int` - Número de backups removidos

**Exemplo**:
```python
removed = backup_manager.cleanup_old_backups(retention_days=7)
print(f"Removidos {removed} backups antigos")
```

#### `verify_backup(backup_file)`
**Descrição**: Verifica integridade de um backup.

**Parâmetros**:
- `backup_file` (str): Caminho do backup

**Retorna**: `dict` - Resultado da verificação

**Exemplo**:
```python
result = backup_manager.verify_backup('backup_20241201_143022.sql.gz')
if result['valid']:
    print("✅ Backup íntegro")
else:
    print(f"❌ Backup corrompido: {result['error']}")
```

---

## ⚙️ ConfigManager

### Descrição
O `ConfigManager` gerencia todas as configurações do sistema, incluindo conexões de banco, tabelas maintain e parâmetros operacionais.

### Inicialização
```python
class ConfigManager:
    def __init__(self, config_file='config.json'):
        """Inicializa ConfigManager (Singleton)"""
        self.config_file = config_file
        self._config = None
```

### Métodos de Configuração

#### `load_config()`
**Descrição**: Carrega configuração do arquivo JSON.

**Retorna**: `dict` - Configuração completa

**Exceções**:
- `FileNotFoundError`: Arquivo de config não encontrado
- `json.JSONDecodeError`: Arquivo JSON inválido

**Exemplo**:
```python
config_manager = ConfigManager()
config = config_manager.load_config()
```

#### `get_database_config(environment)`
**Descrição**: Retorna configuração de banco para ambiente específico.

**Parâmetros**:
- `environment` (str): Nome do ambiente

**Retorna**: `dict` - Configuração do banco

**Exemplo**:
```python
prod_config = config_manager.get_database_config('production')
# {
#     'host': 'prod-server',
#     'user': 'prod-user',
#     'password': 'prod-pass',
#     'database': 'prod-db'
# }
```

#### `get_maintain_tables()`
**Descrição**: Retorna lista de tabelas marcadas como maintain.

**Retorna**: `list` - Lista de nomes de tabelas

**Exemplo**:
```python
maintain_tables = config_manager.get_maintain_tables()
print(f"Tabelas maintain: {', '.join(maintain_tables)}")
```

### Métodos de Validação

#### `validate_config()`
**Descrição**: Valida estrutura e valores da configuração.

**Retorna**: `dict` - Resultado da validação

**Exceções**:
- `ValidationError`: Configuração inválida

**Exemplo**:
```python
validation = config_manager.validate_config()
if validation['valid']:
    print("✅ Configuração válida")
else:
    for error in validation['errors']:
        print(f"❌ {error}")
```

#### `validate_database_config(environment)`
**Descrição**: Valida configuração específica de um ambiente.

**Parâmetros**:
- `environment` (str): Nome do ambiente

**Retorna**: `bool` - True se configuração válida

### Métodos de Utilitários

#### `get_backup_config()`
**Descrição**: Retorna configurações de backup.

**Retorna**: `dict` - Configuração de backup

**Exemplo**:
```python
backup_config = config_manager.get_backup_config()
# {
#     'enabled': True,
#     'compression': True,
#     'retention_days': 7
# }
```

#### `get_logging_config()`
**Descrição**: Retorna configurações de logging.

**Retorna**: `dict` - Configuração de logging

#### `is_table_maintain(table_name)`
**Descrição**: Verifica se tabela está marcada como maintain.

**Parâmetros**:
- `table_name` (str): Nome da tabela

**Retorna**: `bool` - True se é tabela maintain

**Exemplo**:
```python
if config_manager.is_table_maintain('users'):
    print("Tabela users será replicada com dados")
else:
    print("Tabela users será replicada apenas estrutura")
```

---

## 📝 LoggerManager

### Descrição
O `LoggerManager` gerencia todo o sistema de logging, incluindo diferentes níveis de log, rotação de arquivos e formatação.

### Inicialização
```python
class LoggerManager:
    def __init__(self, config_manager=None):
        """Inicializa LoggerManager"""
        self.config_manager = config_manager or ConfigManager()
        self.logger = None
        self.setup_logger()
```

### Métodos de Configuração

#### `setup_logger(log_level='INFO', log_file=None)`
**Descrição**: Configura o sistema de logging.

**Parâmetros**:
- `log_level` (str): Nível de log ('DEBUG', 'INFO', 'WARNING', 'ERROR')
- `log_file` (str, optional): Arquivo de log específico

**Exemplo**:
```python
logger_manager = LoggerManager()
logger_manager.setup_logger('DEBUG', 'custom.log')
```

### Métodos de Logging

#### `log_info(message, extra_data=None)`
**Descrição**: Registra mensagem informativa.

**Parâmetros**:
- `message` (str): Mensagem de log
- `extra_data` (dict, optional): Dados adicionais

**Exemplo**:
```python
logger_manager.log_info("Iniciando replicação", {
    'source': 'production',
    'target': 'sandbox'
})
```

#### `log_error(message, exception=None, extra_data=None)`
**Descrição**: Registra erro com detalhes.

**Parâmetros**:
- `message` (str): Mensagem de erro
- `exception` (Exception, optional): Exceção capturada
- `extra_data` (dict, optional): Dados adicionais

**Exemplo**:
```python
try:
    # operação que pode falhar
    pass
except Exception as e:
    logger_manager.log_error("Falha na replicação", e, {
        'table': 'users',
        'operation': 'insert'
    })
```

#### `log_warning(message, extra_data=None)`
**Descrição**: Registra aviso.

#### `log_debug(message, extra_data=None)`
**Descrição**: Registra mensagem de debug.

### Métodos de Operação

#### `log_operation_start(operation_name, details=None)`
**Descrição**: Marca início de uma operação.

**Parâmetros**:
- `operation_name` (str): Nome da operação
- `details` (dict, optional): Detalhes da operação

**Retorna**: `str` - ID da operação

**Exemplo**:
```python
op_id = logger_manager.log_operation_start('database_replication', {
    'tables_count': 15,
    'source': 'production'
})
```

#### `log_operation_end(operation_id, success=True, details=None)`
**Descrição**: Marca fim de uma operação.

**Parâmetros**:
- `operation_id` (str): ID da operação
- `success` (bool): Se operação foi bem-sucedida
- `details` (dict, optional): Detalhes finais

**Exemplo**:
```python
logger_manager.log_operation_end(op_id, True, {
    'duration': '00:02:45',
    'records_processed': 1250
})
```

### Métodos de Relatório

#### `generate_daily_report(date=None)`
**Descrição**: Gera relatório de atividades do dia.

**Parâmetros**:
- `date` (str, optional): Data no formato 'YYYY-MM-DD'

**Retorna**: `dict` - Relatório estruturado

**Exemplo**:
```python
report = logger_manager.generate_daily_report('2024-12-01')
print(f"Operações realizadas: {report['total_operations']}")
print(f"Sucessos: {report['successful_operations']}")
print(f"Erros: {report['failed_operations']}")
```

#### `get_recent_logs(limit=100, level=None)`
**Descrição**: Retorna logs recentes.

**Parâmetros**:
- `limit` (int): Número máximo de logs
- `level` (str, optional): Filtro por nível

**Retorna**: `list` - Lista de logs

---

## 🔧 Utils

### Descrição
O módulo `Utils` fornece funções utilitárias usadas em todo o sistema.

### Funções de Formatação

#### `format_size(bytes_size)`
**Descrição**: Formata tamanho em bytes para formato legível.

**Parâmetros**:
- `bytes_size` (int): Tamanho em bytes

**Retorna**: `str` - Tamanho formatado

**Exemplo**:
```python
from core.utils import format_size

size = format_size(1073741824)  # "1.00 GB"
print(f"Tamanho do backup: {size}")
```

#### `format_duration(seconds)`
**Descrição**: Formata duração em segundos para formato legível.

**Parâmetros**:
- `seconds` (float): Duração em segundos

**Retorna**: `str` - Duração formatada

**Exemplo**:
```python
from core.utils import format_duration

duration = format_duration(165.5)  # "00:02:45"
print(f"Tempo de execução: {duration}")
```

### Funções de Validação

#### `validate_table_name(table_name)`
**Descrição**: Valida se nome de tabela é válido.

**Parâmetros**:
- `table_name` (str): Nome da tabela

**Retorna**: `bool` - True se válido

**Exemplo**:
```python
from core.utils import validate_table_name

if validate_table_name('users'):
    print("✅ Nome de tabela válido")
```

#### `validate_environment_name(env_name)`
**Descrição**: Valida nome de ambiente.

**Parâmetros**:
- `env_name` (str): Nome do ambiente

**Retorna**: `bool` - True se válido

### Funções de Sistema

#### `safe_filename(filename)`
**Descrição**: Gera nome de arquivo seguro.

**Parâmetros**:
- `filename` (str): Nome original

**Retorna**: `str` - Nome seguro

**Exemplo**:
```python
from core.utils import safe_filename

safe_name = safe_filename("backup file 2024.sql")  # "backup_file_2024.sql"
```

#### `ensure_directory(directory_path)`
**Descrição**: Garante que diretório existe.

**Parâmetros**:
- `directory_path` (str): Caminho do diretório

**Exemplo**:
```python
from core.utils import ensure_directory

ensure_directory('backups/2024/12')
```

### Funções de Progresso

#### `create_progress_callback(description)`
**Descrição**: Cria callback para barra de progresso.

**Parâmetros**:
- `description` (str): Descrição da operação

**Retorna**: `callable` - Função de callback

**Exemplo**:
```python
from core.utils import create_progress_callback

callback = create_progress_callback("Replicando dados")
# Usar com tqdm ou outras barras de progresso
```

---

**Próximo**: [Development Guide](../development/README.md)