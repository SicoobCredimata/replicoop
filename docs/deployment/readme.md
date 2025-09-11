# 🚀 Guia de Deployment - ReplicOOP

## 🎯 Visão Geral

Este guia cobre todos os aspectos necessários para realizar deployment do **ReplicOOP** em ambiente de produção, incluindo configuração, monitoramento e manutenção.

## 📋 Índice

- [🏗️ Preparação do Ambiente](#-preparação-do-ambiente)
- [⚙️ Configuração de Produção](#-configuração-de-produção)
- [📊 Monitoramento](#-monitoramento)
- [🔧 Manutenção](#-manutenção)
- [🆘 Troubleshooting](#-troubleshooting)

## 🏗️ Preparação do Ambiente

### Requisitos do Sistema

#### Hardware Mínimo
```yaml
CPU: 2 cores
RAM: 4GB
Disco: 50GB livres
Rede: 100Mbps
```

#### Hardware Recomendado
```yaml
CPU: 4+ cores
RAM: 8GB+
Disco: 100GB+ SSD
Rede: 1Gbps
```

#### Software Necessário
```yaml
SO: Windows Server 2019+
Python: 3.13+
MySQL: 8.0+
PowerShell: 5.1+
```

### Instalação do Ambiente

#### 1. Preparação do Sistema
```powershell
# Atualizar sistema
Get-Module -ListAvailable PowerShellGet
Update-Module PowerShellGet

# Instalar Python (se necessário)
winget install Python.Python.3.13

# Verificar instalação
python --version
pip --version
```

#### 2. Configuração do Usuário de Serviço
```powershell
# Criar usuário específico para o serviço
net user replicoop P@ssw0rd123! /add
net localgroup "Users" replicoop /add

# Configurar privilégios necessários
# - Logon as service
# - Access MySQL databases
```

#### 3. Estrutura de Diretórios
```powershell
# Criar estrutura de diretórios
New-Item -Path "C:\Apps\ReplicOOP" -ItemType Directory
New-Item -Path "C:\Apps\ReplicOOP\logs" -ItemType Directory
New-Item -Path "C:\Apps\ReplicOOP\backups" -ItemType Directory
New-Item -Path "C:\Apps\ReplicOOP\config" -ItemType Directory

# Definir permissões
icacls "C:\Apps\ReplicOOP" /grant replicoop:(OI)(CI)F
```

### Deployment da Aplicação

#### 1. Cópia dos Arquivos
```powershell
# Copiar arquivos da aplicação
Copy-Item -Path ".\*" -Destination "C:\Apps\ReplicOOP\" -Recurse -Exclude @("venv", ".git", "tests", "__pycache__")

# Estrutura final
C:\Apps\ReplicOOP\
├── main.py
├── manager.bat
├── requirements.txt
├── core\
├── config\
├── logs\
└── backups\
```

#### 2. Configuração do Ambiente Python
```powershell
# Navegar para diretório da aplicação
Set-Location "C:\Apps\ReplicOOP"

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Configuração de Produção

### Arquivo de Configuração

#### config.json (Produção)
```json
{
  "databases": {
    "production": {
      "host": "mysql-prod.company.com",
      "port": 3306,
      "user": "replicoop_user",
      "password": "${MYSQL_PROD_PASSWORD}",
      "database": "production_db",
      "charset": "utf8mb4",
      "autocommit": false,
      "connect_timeout": 30,
      "read_timeout": 300,
      "write_timeout": 300
    },
    "sandbox": {
      "host": "mysql-sandbox.company.com", 
      "port": 3306,
      "user": "replicoop_user",
      "password": "${MYSQL_SAND_PASSWORD}",
      "database": "sandbox_db",
      "charset": "utf8mb4",
      "autocommit": false,
      "connect_timeout": 30,
      "read_timeout": 300,
      "write_timeout": 300
    }
  },
  "maintain": [
    "usuarios",
    "produtos",
    "configuracoes",
    "parametros_sistema",
    "perfis_acesso"
  ],
  "backup": {
    "enabled": true,
    "compression": true,
    "retention_days": 30,
    "backup_directory": "C:\\Apps\\ReplicOOP\\backups",
    "verify_backup": true,
    "max_backup_size_gb": 10
  },
  "logging": {
    "level": "INFO",
    "log_directory": "C:\\Apps\\ReplicOOP\\logs",
    "max_file_size": "100MB",
    "backup_count": 10,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S"
  },
  "performance": {
    "batch_size": 5000,
    "max_connections": 10,
    "connection_pool_size": 5,
    "query_timeout": 300,
    "max_table_size_gb": 5
  },
  "notifications": {
    "email_enabled": true,
    "smtp_server": "smtp.company.com",
    "smtp_port": 587,
    "smtp_user": "replicoop@company.com",
    "smtp_password": "${SMTP_PASSWORD}",
    "recipients": [
      "admin@company.com",
      "dba@company.com"
    ]
  },
  "security": {
    "encrypt_passwords": true,
    "ssl_enabled": true,
    "ssl_ca": "ca-cert.pem",
    "ssl_cert": "client-cert.pem", 
    "ssl_key": "client-key.pem"
  }
}
```

### Gerenciamento de Senhas

#### Variáveis de Ambiente
```powershell
# Definir variáveis de ambiente do sistema
[Environment]::SetEnvironmentVariable("MYSQL_PROD_PASSWORD", "prod_password_here", "Machine")
[Environment]::SetEnvironmentVariable("MYSQL_SAND_PASSWORD", "sand_password_here", "Machine")
[Environment]::SetEnvironmentVariable("SMTP_PASSWORD", "smtp_password_here", "Machine")

# Verificar variáveis
Get-ChildItem Env:MYSQL_*
```

#### Criptografia de Senhas
```python
# core/security.py
from cryptography.fernet import Fernet
import os

class PasswordManager:
    def __init__(self, key_file="encryption.key"):
        self.key_file = key_file
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_password(self, password: str) -> str:
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        return self.cipher.decrypt(encrypted_password.encode()).decode()
```

### Configuração de Rede

#### Firewall Windows
```powershell
# Permitir conexões MySQL
New-NetFirewallRule -DisplayName "MySQL Client" -Direction Outbound -Protocol TCP -RemotePort 3306 -Action Allow

# Permitir SMTP (se notificações habilitadas)
New-NetFirewallRule -DisplayName "SMTP Client" -Direction Outbound -Protocol TCP -RemotePort 587 -Action Allow
```

#### Configuração MySQL
```sql
-- Criar usuário específico para replicação
CREATE USER 'replicoop_user'@'%' IDENTIFIED BY 'strong_password_here';

-- Conceder privilégios necessários
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON production_db.* TO 'replicoop_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON sandbox_db.* TO 'replicoop_user'@'%';

-- Para backups via mysqldump
GRANT LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'replicoop_user'@'%';

-- Aplicar alterações
FLUSH PRIVILEGES;
```

## 📊 Monitoramento

### Configuração de Logs

#### Configuração Avançada de Logging
```python
# core/monitoring.py
import logging
import logging.handlers
from datetime import datetime
import json

class ProductionLogger:
    def __init__(self, config):
        self.config = config
        self.setup_loggers()
    
    def setup_loggers(self):
        # Logger principal
        self.main_logger = logging.getLogger('replicoop.main')
        self.main_logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        # Logger de performance
        self.perf_logger = logging.getLogger('replicoop.performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # Logger de auditoria
        self.audit_logger = logging.getLogger('replicoop.audit')
        self.audit_logger.setLevel(logging.INFO)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        log_dir = self.config['logging']['log_directory']
        
        # Handler principal com rotação
        main_handler = logging.handlers.RotatingFileHandler(
            filename=f"{log_dir}/replicoop.log",
            maxBytes=self._parse_size(self.config['logging']['max_file_size']),
            backupCount=self.config['logging']['backup_count']
        )
        
        # Handler de performance
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            filename=f"{log_dir}/performance.log",
            when='midnight',
            interval=1,
            backupCount=30
        )
        
        # Handler de auditoria
        audit_handler = logging.handlers.TimedRotatingFileHandler(
            filename=f"{log_dir}/audit.log",
            when='midnight', 
            interval=1,
            backupCount=365  # Manter auditoria por 1 ano
        )
        
        # Formatadores
        formatter = logging.Formatter(self.config['logging']['format'])
        main_handler.setFormatter(formatter)
        perf_handler.setFormatter(formatter)
        audit_handler.setFormatter(formatter)
        
        # Adicionar handlers
        self.main_logger.addHandler(main_handler)
        self.perf_logger.addHandler(perf_handler)
        self.audit_logger.addHandler(audit_handler)
```

### Métricas de Performance

#### Coleta de Métricas
```python
# core/metrics.py
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
        self.start_time = None
    
    def start_operation(self, operation_name: str):
        self.start_time = time.time()
        self.metrics = {
            'operation': operation_name,
            'start_time': datetime.now(),
            'cpu_percent_start': psutil.cpu_percent(),
            'memory_start': psutil.virtual_memory().percent,
            'disk_start': psutil.disk_usage('C:').percent
        }
    
    def end_operation(self, records_processed: int = 0) -> Dict[str, Any]:
        end_time = time.time()
        execution_time = end_time - self.start_time if self.start_time else 0
        
        self.metrics.update({
            'end_time': datetime.now(),
            'execution_time_seconds': execution_time,
            'cpu_percent_end': psutil.cpu_percent(),
            'memory_end': psutil.virtual_memory().percent,
            'disk_end': psutil.disk_usage('C:').percent,
            'records_processed': records_processed,
            'records_per_second': records_processed / execution_time if execution_time > 0 else 0
        })
        
        return self.metrics
    
    def get_system_health(self) -> Dict[str, Any]:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('C:').percent,
            'disk_free_gb': psutil.disk_usage('C:').free / (1024**3),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
```

### Sistema de Alertas

#### Configuração de Alertas por Email
```python
# core/alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class AlertManager:
    def __init__(self, config):
        self.config = config['notifications']
        self.enabled = self.config['email_enabled']
    
    def send_alert(self, subject: str, message: str, level: str = 'INFO'):
        if not self.enabled:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['smtp_user']
            msg['To'] = ', '.join(self.config['recipients'])
            msg['Subject'] = f"[ReplicOOP {level}] {subject}"
            
            body = f"""
            <html>
            <body>
                <h2>ReplicOOP Alert</h2>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Level:</strong> {level}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['smtp_user'], self.config['smtp_password'])
                server.send_message(msg)
                
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to send alert: {e}")
    
    def alert_replication_success(self, stats: dict):
        subject = "Replication Completed Successfully"
        message = f"""
        Replication completed successfully:
        
        - Tables replicated: {stats.get('tables_replicated', 0)}
        - Records processed: {stats.get('records_replicated', 0)}
        - Execution time: {stats.get('execution_time', 'Unknown')}
        - Backup created: {stats.get('backup_created', 'None')}
        """
        self.send_alert(subject, message, 'SUCCESS')
    
    def alert_replication_failure(self, error: str, details: dict = None):
        subject = "Replication Failed"
        message = f"""
        Replication failed with error:
        
        Error: {error}
        
        Details: {details if details else 'No additional details'}
        
        Please check the logs for more information.
        """
        self.send_alert(subject, message, 'ERROR')
```

## 🔧 Manutenção

### Tarefas Agendadas

#### Script de Backup Automático
```powershell
# backup_automation.ps1
param(
    [string]$ConfigFile = "C:\Apps\ReplicOOP\config\config.json",
    [string]$LogFile = "C:\Apps\ReplicOOP\logs\backup_automation.log"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

try {
    Write-Log "Starting automated backup process"
    
    # Ativar ambiente virtual
    Set-Location "C:\Apps\ReplicOOP"
    .\venv\Scripts\Activate.ps1
    
    # Executar backup
    $result = python -c "
from core.backup import BackupManager
from core.config import ConfigManager

config_mgr = ConfigManager('$ConfigFile')
backup_mgr = BackupManager(config_mgr)

try:
    backup_file = backup_mgr.create_backup('sandbox')
    print(f'SUCCESS:{backup_file}')
except Exception as e:
    print(f'ERROR:{str(e)}')
"
    
    if ($result -match "^SUCCESS:(.+)") {
        $backupFile = $Matches[1]
        Write-Log "Backup created successfully: $backupFile" "SUCCESS"
        
        # Limpeza de backups antigos
        python -c "
from core.backup import BackupManager
from core.config import ConfigManager

config_mgr = ConfigManager('$ConfigFile')
backup_mgr = BackupManager(config_mgr)
removed = backup_mgr.cleanup_old_backups()
print(f'Removed {removed} old backups')
"
        
    } elseif ($result -match "^ERROR:(.+)") {
        $errorMsg = $Matches[1]
        Write-Log "Backup failed: $errorMsg" "ERROR"
        exit 1
    }
    
} catch {
    Write-Log "Script execution failed: $($_.Exception.Message)" "ERROR"
    exit 1
}
```

#### Configuração do Agendador de Tarefas
```powershell
# Criar tarefa agendada para backup diário
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Apps\ReplicOOP\scripts\backup_automation.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"

$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) -RestartCount 3

$principal = New-ScheduledTaskPrincipal -UserId "replicoop" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "ReplicOOP Daily Backup" -Action $action -Trigger $trigger -Settings $settings -Principal $principal
```

### Monitoramento de Saúde

#### Health Check Script
```python
# health_check.py
import json
import sys
from datetime import datetime, timedelta
from core.config import ConfigManager
from core.database import DatabaseManager
from core.metrics import MetricsCollector

def check_database_connectivity():
    """Verifica conectividade com bancos de dados"""
    try:
        config_mgr = ConfigManager()
        db_mgr = DatabaseManager(config_mgr)
        
        results = {}
        for env in ['production', 'sandbox']:
            try:
                connection = db_mgr.get_connection(env)
                if connection:
                    results[env] = {'status': 'OK', 'connected': True}
                    connection.close()
                else:
                    results[env] = {'status': 'FAIL', 'connected': False}
            except Exception as e:
                results[env] = {'status': 'ERROR', 'error': str(e), 'connected': False}
        
        return results
    except Exception as e:
        return {'error': f"Configuration error: {e}"}

def check_disk_space():
    """Verifica espaço em disco"""
    import psutil
    
    disk_usage = psutil.disk_usage('C:')
    free_gb = disk_usage.free / (1024**3)
    used_percent = (disk_usage.used / disk_usage.total) * 100
    
    status = 'OK'
    if used_percent > 90:
        status = 'CRITICAL'
    elif used_percent > 80:
        status = 'WARNING'
    
    return {
        'status': status,
        'free_gb': round(free_gb, 2),
        'used_percent': round(used_percent, 2)
    }

def check_recent_backups():
    """Verifica se há backups recentes"""
    import os
    import glob
    
    backup_dir = "C:/Apps/ReplicOOP/backups"
    if not os.path.exists(backup_dir):
        return {'status': 'ERROR', 'message': 'Backup directory not found'}
    
    backup_files = glob.glob(f"{backup_dir}/*.gz")
    if not backup_files:
        return {'status': 'WARNING', 'message': 'No backup files found'}
    
    # Verifica o backup mais recente
    latest_backup = max(backup_files, key=os.path.getctime)
    backup_time = datetime.fromtimestamp(os.path.getctime(latest_backup))
    
    # Se o backup mais recente tem mais de 25 horas, é um warning
    if datetime.now() - backup_time > timedelta(hours=25):
        return {
            'status': 'WARNING',
            'message': f'Latest backup is old: {backup_time}',
            'latest_backup': latest_backup
        }
    
    return {
        'status': 'OK',
        'latest_backup': latest_backup,
        'backup_time': backup_time.isoformat()
    }

def main():
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'checks': {
            'database_connectivity': check_database_connectivity(),
            'disk_space': check_disk_space(),
            'recent_backups': check_recent_backups()
        }
    }
    
    # Determina status geral
    overall_status = 'OK'
    for check_name, check_result in health_report['checks'].items():
        if isinstance(check_result, dict):
            check_status = check_result.get('status', 'UNKNOWN')
            if check_status == 'CRITICAL':
                overall_status = 'CRITICAL'
                break
            elif check_status in ['ERROR', 'WARNING'] and overall_status == 'OK':
                overall_status = check_status
    
    health_report['overall_status'] = overall_status
    
    # Output JSON para integração com monitoramento
    print(json.dumps(health_report, indent=2))
    
    # Exit code baseado no status
    exit_codes = {'OK': 0, 'WARNING': 1, 'ERROR': 2, 'CRITICAL': 3}
    sys.exit(exit_codes.get(overall_status, 4))

if __name__ == '__main__':
    main()
```

## 🆘 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco
```
Sintoma: "Connection refused" ou "Access denied"
Diagnóstico:
- Verificar conectividade de rede
- Validar credenciais
- Verificar configuração de firewall
- Verificar status do serviço MySQL

Soluções:
1. Testar conexão manual:
   mysql -h hostname -u username -p database_name

2. Verificar logs do MySQL:
   tail -f /var/log/mysql/error.log

3. Verificar configuração de rede do MySQL:
   SHOW VARIABLES LIKE 'bind_address';
```

#### 2. Falha no Backup
```
Sintoma: "Backup creation failed" ou "Permission denied"
Diagnóstico:
- Verificar espaço em disco
- Verificar permissões de diretório
- Verificar se mysqldump está disponível

Soluções:
1. Verificar espaço disponível:
   Get-WmiObject -Class Win32_LogicalDisk

2. Verificar permissões:
   icacls C:\Apps\ReplicOOP\backups

3. Testar mysqldump manualmente:
   mysqldump -h host -u user -p database > test_backup.sql
```

#### 3. Performance Lenta
```
Sintoma: Replicação demora muito tempo
Diagnóstico:
- Verificar tamanho das tabelas
- Verificar latência de rede
- Verificar carga do servidor

Soluções:
1. Ajustar batch_size no config.json
2. Verificar índices nas tabelas
3. Executar durante horário de menor carga
4. Considerar replicação incremental
```

### Scripts de Diagnóstico

#### Diagnóstico Completo
```powershell
# diagnostic.ps1
Write-Host "=== ReplicOOP System Diagnostic ===" -ForegroundColor Green

# Verificar versão Python
Write-Host "`n1. Python Version:" -ForegroundColor Yellow
python --version

# Verificar dependências
Write-Host "`n2. Installed Packages:" -ForegroundColor Yellow
pip list | Select-String "mysql|colorama|tabulate|tqdm"

# Verificar conectividade
Write-Host "`n3. Network Connectivity:" -ForegroundColor Yellow
Test-NetConnection mysql-prod.company.com -Port 3306
Test-NetConnection mysql-sandbox.company.com -Port 3306

# Verificar espaço em disco
Write-Host "`n4. Disk Space:" -ForegroundColor Yellow
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Free(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, @{Name="Total(GB)";Expression={[math]::Round($_.Size/1GB,2)}}

# Verificar logs recentes
Write-Host "`n5. Recent Logs:" -ForegroundColor Yellow
if (Test-Path "C:\Apps\ReplicOOP\logs\replicoop.log") {
    Get-Content "C:\Apps\ReplicOOP\logs\replicoop.log" -Tail 10
} else {
    Write-Host "No log file found"
}

# Health check
Write-Host "`n6. Health Check:" -ForegroundColor Yellow
Set-Location "C:\Apps\ReplicOOP"
.\venv\Scripts\Activate.ps1
python health_check.py
```

### Recovery Procedures

#### Recuperação de Falhas

1. **Falha na Replicação**
```powershell
# recovery_replication.ps1

# 1. Verificar último backup
$latestBackup = Get-ChildItem "C:\Apps\ReplicOOP\backups\*.gz" | Sort-Object CreationTime -Descending | Select-Object -First 1

if ($latestBackup) {
    Write-Host "Latest backup found: $($latestBackup.Name)"
    
    # 2. Confirmar restauração
    $confirm = Read-Host "Restore from backup? (y/n)"
    if ($confirm -eq 'y') {
        # 3. Executar restauração
        Set-Location "C:\Apps\ReplicOOP"
        .\venv\Scripts\Activate.ps1
        
        python -c "
from core.backup import BackupManager
from core.config import ConfigManager

config_mgr = ConfigManager()
backup_mgr = BackupManager(config_mgr)
backup_mgr.restore_backup('$($latestBackup.FullName)', 'sandbox')
print('Restore completed')
"
    }
} else {
    Write-Host "No backups found!" -ForegroundColor Red
}
```

2. **Recuperação de Configuração**
```json
// config_backup.json (template mínimo)
{
  "databases": {
    "production": {
      "host": "CONFIGURE_HOST",
      "user": "CONFIGURE_USER", 
      "password": "CONFIGURE_PASSWORD",
      "database": "CONFIGURE_DATABASE"
    },
    "sandbox": {
      "host": "CONFIGURE_HOST",
      "user": "CONFIGURE_USER",
      "password": "CONFIGURE_PASSWORD", 
      "database": "CONFIGURE_DATABASE"
    }
  },
  "maintain": [],
  "backup": {
    "enabled": true,
    "compression": true,
    "retention_days": 7
  },
  "logging": {
    "level": "INFO"
  }
}
```

### Contatos de Suporte

```yaml
Administrador Sistema: admin@company.com
DBA: dba@company.com
Suporte TI: suporte@company.com
Emergência: +55 (XX) XXXX-XXXX
```

---

**🎉 Documentação Completa! Sistema ReplicOOP pronto para manutenção e evolução.**