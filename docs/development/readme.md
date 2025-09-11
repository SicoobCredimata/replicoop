# 👨‍💻 Guia de Desenvolvimento - ReplicOOP

## 🎯 Visão Geral

Este guia fornece todas as informações necessárias para desenvolvedores que desejam contribuir, manter ou estender o sistema **ReplicOOP**.

## 📋 Índice

- [🚀 Configuração do Ambiente](#-configuração-do-ambiente)
- [📐 Padrões de Código](#-padrões-de-código)
- [🧪 Testes](#-testes)
- [🔧 Ferramentas de Desenvolvimento](#-ferramentas-de-desenvolvimento)
- [📦 Contribuindo](#-contribuindo)

## 🚀 Configuração do Ambiente

### Pré-requisitos

```yaml
Python: "3.13+"
MySQL: "8.0+"
Sistema: Windows 10/11
Shell: PowerShell 5.1+
```

### Instalação para Desenvolvimento

1. **Clone do Repositório**
```powershell
git clone <repository-url>
cd replicoop
```

2. **Configuração do Ambiente Virtual**
```powershell
# Criação do venv
python -m venv venv

# Ativação (PowerShell)
.\venv\Scripts\Activate.ps1

# Instalação das dependências
pip install -r requirements.txt
```

3. **Configuração de Desenvolvimento**
```powershell
# Instalar dependências de desenvolvimento
pip install pytest black flake8 mypy pre-commit

# Configurar pre-commit hooks
pre-commit install
```

4. **Configuração do Banco de Dados**
```json
// config.json para desenvolvimento
{
  "databases": {
    "production": {
      "host": "localhost",
      "user": "dev_user",
      "password": "dev_pass",
      "database": "dev_production"
    },
    "sandbox": {
      "host": "localhost", 
      "user": "dev_user",
      "password": "dev_pass",
      "database": "dev_sandbox"
    }
  },
  "maintain": [
    "test_table1",
    "test_table2"
  ],
  "backup": {
    "enabled": true,
    "compression": true,
    "retention_days": 3
  },
  "logging": {
    "level": "DEBUG",
    "max_file_size": "10MB",
    "backup_count": 3
  }
}
```

## 📐 Padrões de Código

### Estrutura de Arquivos

```
replicoop/
├── main.py                 # Interface principal
├── manager.bat            # Script de gerenciamento
├── config.json           # Configurações
├── requirements.txt      # Dependências
├── core/                 # Módulos principais
│   ├── __init__.py
│   ├── replication.py    # Motor de replicação
│   ├── database.py       # Interface MySQL
│   ├── backup.py         # Sistema de backup
│   ├── config.py         # Configurações
│   ├── logger.py         # Sistema de logs
│   └── utils.py          # Utilitários
├── tests/                # Testes automatizados
│   ├── __init__.py
│   ├── test_replication.py
│   ├── test_database.py
│   ├── test_backup.py
│   ├── test_config.py
│   ├── test_logger.py
│   └── test_utils.py
├── docs/                 # Documentação
└── backups/              # Backups (ignorado no git)
```

### Convenções de Nomenclatura

#### Classes
```python
# ✅ Correto - PascalCase para classes
class ReplicationManager:
    pass

class DatabaseConnection:
    pass

# ❌ Incorreto
class replicationManager:
    pass
```

#### Métodos e Funções
```python
# ✅ Correto - snake_case para métodos/funções
def replicate_database(self, source, target):
    pass

def get_table_structure(self, table_name):
    pass

# ❌ Incorreto
def replicateDatabase(self, source, target):
    pass
```

#### Constantes
```python
# ✅ Correto - UPPER_CASE para constantes
DEFAULT_BATCH_SIZE = 1000
MAX_RETRY_ATTEMPTS = 3
CONNECTION_TIMEOUT = 30

# ❌ Incorreto
default_batch_size = 1000
```

#### Variáveis
```python
# ✅ Correto - snake_case para variáveis
table_name = "users"
connection_config = {...}
backup_file_path = "backup.sql.gz"

# ❌ Incorreto
tableName = "users"
```

### Documentação de Código

#### Docstrings
```python
def replicate_table_data(self, table_name: str, batch_size: int = 1000) -> dict:
    """
    Replica dados de uma tabela específica.
    
    Args:
        table_name: Nome da tabela a ser replicada
        batch_size: Tamanho do lote para processamento
        
    Returns:
        dict: Estatísticas da replicação contendo:
            - records_replicated: Número de registros replicados
            - execution_time: Tempo de execução em segundos
            - success: Booleano indicando sucesso
            
    Raises:
        ConnectionError: Quando não consegue conectar ao banco
        ReplicationError: Quando falha durante a replicação
        
    Example:
        >>> manager = ReplicationManager()
        >>> result = manager.replicate_table_data("users", 500)
        >>> print(f"Replicados {result['records_replicated']} registros")
    """
    try:
        # Implementação...
        pass
    except Exception as e:
        self.logger.error(f"Erro replicando tabela {table_name}: {e}")
        raise
```

#### Comentários
```python
def complex_operation(self):
    # Etapa 1: Preparação do ambiente
    self._setup_environment()
    
    # Etapa 2: Validação das configurações
    if not self._validate_config():
        raise ConfigurationError("Configuração inválida")
    
    # Etapa 3: Execução da operação principal
    # NOTA: Foreign keys são removidas temporariamente para evitar conflitos
    foreign_keys = self._remove_foreign_keys()
    try:
        result = self._execute_main_operation()
    finally:
        # Sempre restaura as foreign keys, mesmo em caso de erro
        self._restore_foreign_keys(foreign_keys)
    
    return result
```

### Type Hints

```python
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

class DatabaseManager:
    def get_table_data(
        self, 
        table_name: str, 
        batch_size: int = 1000,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Tuple]:
        """
        Retorna dados de tabela com type hints completos.
        """
        pass
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> Union[List[Tuple], int]:
        """
        Executa query e retorna resultados ou número de linhas afetadas.
        """
        pass
```

### Tratamento de Erros

#### Hierarquia de Exceções
```python
class ReplicOOPError(Exception):
    """Exceção base do sistema ReplicOOP"""
    pass

class ConnectionError(ReplicOOPError):
    """Erro de conexão com banco de dados"""
    pass

class ConfigurationError(ReplicOOPError):
    """Erro de configuração"""
    pass

class ReplicationError(ReplicOOPError):
    """Erro durante processo de replicação"""
    pass

class BackupError(ReplicOOPError):
    """Erro no sistema de backup"""
    pass

class ValidationError(ReplicOOPError):
    """Erro de validação"""
    pass
```

#### Tratamento Adequado
```python
def safe_operation(self):
    """Exemplo de tratamento adequado de erros"""
    try:
        # Operação que pode falhar
        result = self._risky_operation()
        
    except ConnectionError as e:
        self.logger.error(f"Falha na conexão: {e}")
        # Tenta reconectar
        self._reconnect()
        raise
        
    except ReplicationError as e:
        self.logger.error(f"Erro na replicação: {e}")
        # Faz rollback se necessário
        self._rollback()
        raise
        
    except Exception as e:
        # Log do erro inesperado
        self.logger.error(f"Erro inesperado: {e}", exc_info=True)
        raise ReplicOOPError(f"Operação falhou: {e}") from e
        
    else:
        # Sucesso
        self.logger.info("Operação concluída com sucesso")
        return result
        
    finally:
        # Limpeza sempre executada
        self._cleanup()
```

## 🧪 Testes

### Estrutura de Testes

```python
# tests/test_replication.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.replication import ReplicationManager
from core.exceptions import ReplicationError

class TestReplicationManager:
    """Testes para ReplicationManager"""
    
    @pytest.fixture
    def mock_managers(self):
        """Fixture que cria mocks dos managers dependentes"""
        return {
            'config_manager': Mock(),
            'database_manager': Mock(),
            'backup_manager': Mock(),
            'logger_manager': Mock()
        }
    
    @pytest.fixture
    def replication_manager(self, mock_managers):
        """Fixture que cria ReplicationManager com dependências mockadas"""
        with patch('core.replication.ConfigManager') as mock_config, \
             patch('core.replication.DatabaseManager') as mock_db, \
             patch('core.replication.BackupManager') as mock_backup, \
             patch('core.replication.LoggerManager') as mock_logger:
            
            mock_config.return_value = mock_managers['config_manager']
            mock_db.return_value = mock_managers['database_manager']
            mock_backup.return_value = mock_managers['backup_manager']
            mock_logger.return_value = mock_managers['logger_manager']
            
            return ReplicationManager()
    
    def test_replicate_database_success(self, replication_manager, mock_managers):
        """Testa replicação bem-sucedida"""
        # Arrange
        mock_managers['backup_manager'].create_backup.return_value = 'backup.sql.gz'
        mock_managers['config_manager'].get_maintain_tables.return_value = ['users']
        
        # Act
        result = replication_manager.replicate_database('production', 'sandbox')
        
        # Assert
        assert result['success'] is True
        assert 'backup_created' in result
        mock_managers['backup_manager'].create_backup.assert_called_once()
    
    def test_replicate_database_connection_error(self, replication_manager, mock_managers):
        """Testa falha de conexão durante replicação"""
        # Arrange
        mock_managers['database_manager'].get_connection.side_effect = ConnectionError("Falha na conexão")
        
        # Act & Assert
        with pytest.raises(ConnectionError):
            replication_manager.replicate_database('production', 'sandbox')
    
    @pytest.mark.parametrize("source_env,target_env,expected_calls", [
        ("production", "sandbox", 1),
        ("sandbox", "production", 1),
    ])
    def test_replicate_different_environments(
        self, replication_manager, mock_managers, 
        source_env, target_env, expected_calls
    ):
        """Testa replicação entre diferentes ambientes"""
        # Act
        replication_manager.replicate_database(source_env, target_env)
        
        # Assert
        assert mock_managers['backup_manager'].create_backup.call_count == expected_calls
```

### Testes de Integração

```python
# tests/integration/test_full_replication.py
import pytest
import mysql.connector
from core.replication import ReplicationManager

class TestFullReplication:
    """Testes de integração para replicação completa"""
    
    @pytest.fixture(scope="class")
    def test_databases(self):
        """Cria bancos de teste para integração"""
        # Setup dos bancos de teste
        source_conn = mysql.connector.connect(**TEST_DB_CONFIG['source'])
        target_conn = mysql.connector.connect(**TEST_DB_CONFIG['target'])
        
        # Criação de dados de teste
        self._setup_test_data(source_conn)
        
        yield source_conn, target_conn
        
        # Limpeza após testes
        self._cleanup_test_data(source_conn, target_conn)
        source_conn.close()
        target_conn.close()
    
    def test_full_replication_cycle(self, test_databases):
        """Testa ciclo completo de replicação"""
        source_conn, target_conn = test_databases
        
        # Act
        replication_manager = ReplicationManager()
        result = replication_manager.replicate_database('test_source', 'test_target')
        
        # Assert
        assert result['success'] is True
        
        # Verifica se dados foram replicados corretamente
        source_count = self._get_record_count(source_conn, 'test_table')
        target_count = self._get_record_count(target_conn, 'test_table')
        
        assert source_count == target_count
```

### Execução de Testes

```powershell
# Executa todos os testes
pytest

# Executa testes com cobertura
pytest --cov=core --cov-report=html

# Executa apenas testes unitários
pytest tests/unit/

# Executa apenas testes de integração
pytest tests/integration/

# Executa testes específicos
pytest tests/test_replication.py::TestReplicationManager::test_replicate_database_success

# Executa testes em paralelo
pytest -n auto
```

## 🔧 Ferramentas de Desenvolvimento

### Formatação de Código

#### Black (Formatador)
```powershell
# Formatar todo o código
black .

# Verificar formatação sem alterar
black --check .

# Formatar apenas arquivos específicos
black core/replication.py
```

#### Configuração (.pyproject.toml)
```toml
[tool.black]
line-length = 88
target-version = ['py313']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### Linting

#### Flake8
```powershell
# Verificar todo o código
flake8

# Verificar arquivos específicos
flake8 core/
```

#### Configuração (.flake8)
```ini
[flake8]
max-line-length = 88
max-complexity = 10
ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist
```

### Type Checking

#### MyPy
```powershell
# Verificar types em todo projeto
mypy .

# Verificar módulo específico
mypy core/replication.py
```

#### Configuração (mypy.ini)
```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
```

### Pre-commit Hooks

#### Configuração (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
      
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
      
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## 📦 Contribuindo

### Fluxo de Contribuição

1. **Fork do repositório**
2. **Criar branch para feature/fix**
```powershell
git checkout -b feature/nova-funcionalidade
```

3. **Implementar mudanças seguindo padrões**
4. **Executar testes**
```powershell
pytest
black --check .
flake8
mypy .
```

5. **Commit com mensagem descritiva**
```powershell
git commit -m "feat: adiciona suporte para PostgreSQL

- Implementa DatabaseAdapter para PostgreSQL
- Adiciona configurações específicas do PostgreSQL  
- Atualiza testes de integração
- Documenta nova funcionalidade

Closes #123"
```

6. **Push e Pull Request**

### Padrões de Commit

```
tipo(escopo): descrição curta

Descrição mais detalhada explicando o que foi alterado
e por que essas mudanças foram feitas.

- Lista de mudanças principais
- Outras alterações relevantes

Closes #numero-da-issue
```

#### Tipos de Commit
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Mudanças na documentação
- `style`: Mudanças de formatação (não afetam código)
- `refactor`: Refatoração de código
- `test`: Adição ou correção de testes
- `chore`: Mudanças em build, dependências, etc.

### Checklist de Contribuição

- [ ] Código segue padrões estabelecidos
- [ ] Testes passam (`pytest`)
- [ ] Código formatado (`black`)
- [ ] Linting sem erros (`flake8`)
- [ ] Type checking sem erros (`mypy`)
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Testes adicionados para nova funcionalidade
- [ ] Commit messages seguem padrão

---

**Próximo**: [Deployment Guide](../deployment/README.md)