# 🚀 ReplicOOP - Sistema de Replicação MySQL

Sistema avançado para replicação de estruturas e dados de banco de dados MySQL desenvolvido em Python.

## 📋 **Documentação Completa**

📁 **[Ver Documentação Completa em docs/README.md](docs/README.md)**  
🧪 **[Ver Testes em docs/tests/README.md](docs/tests/README.md)**

---

## 🎯 Características Principais

- **Replicação Inteligente**: Diferencia tabelas MAINTAIN (estrutura + dados) de não-MAINTAIN (apenas estrutura)
- **Resolução de Dependências**: Análise automática e ordenação de Foreign Keys
- **Backup Automático**: Backup comprimido antes de qualquer operação
- **Sistema Robusto**: Tratamento completo de erros e recuperação
- **Interface Amigável**: Menu interativo com logs coloridos
- **Performance Otimizada**: 33 tabelas replicadas em ~9 segundos
- **Multi-Ambiente**: Suporte completo para diferentes ambientes

## 🏗️ **Regras de Negócio**

### **📊 Tabelas MAINTAIN**
- Listadas em `config.json` → `maintain_tables`
- **Comportamento**: Estrutura + Dados completos
- **Uso**: Configurações, parâmetros, dados de referência

### **🏗️ Tabelas NÃO-MAINTAIN**  
- Todas as outras tabelas do banco
- **Comportamento**: Apenas estrutura (CREATE TABLE)
- **Uso**: Dados transacionais, logs, processamento

## 🚀 Instalação e Configuração

### Passo 1: Preparar Ambiente
```bash
# Executar manager.bat e escolher opção [1]
manager.bat
```

### Passo 2: Configurar Banco de Dados
```json
{
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
}
```

### Passo 3: Executar Sistema
```bash
# Executar manager.bat e escolher opção [2]
manager.bat
```

## 📋 Menu do Sistema

### 🔄 Operações de Replicação
1. **Replicar Estruturas** - Replicação personalizada com opções
2. **Replicar Tudo** - Estrutura completa + dados das tabelas maintain
3. **Validar Replicação** - Verificar integridade pós-replicação

### 💾 Operações de Backup  
4. **Criar Backup Manual** - Backup sob demanda
5. **Listar Backups** - Visualizar histórico de backups

### 🔧 Configurações e Testes
6. **Testar Conexões** - Verificar conectividade com todos os ambientes
7. **Ver Plano de Replicação** - Preview das operações antes da execução
8. **Configurar Sistema** - Gerenciar arquivos de configuração

### 📊 Relatórios e Logs
9. **Ver Logs** - Acessar logs detalhados do sistema  
10. **Estatísticas** - Estatísticas de uso e performance

## 🎛️ Configuração Avançada

### Tabelas Maintain
As tabelas listadas em `"maintain"` no config.json são especiais:
- **Replicação Completa**: Copia estrutura E dados
- **Dados Preservados**: Mantém informações críticas do sistema
- **Configurável**: Facilmente ajustável via JSON

### Outras Tabelas  
Todas as demais tabelas:
- **Apenas Estrutura**: Schema, índices, constraints
- **Performance**: Replicação muito mais rápida
- **Flexibilidade**: Permite desenvolvimento com estrutura limpa

## 🔐 Segurança e Backup

### Sistema de Backup
- **Automático**: Backup antes de cada replicação destrutiva
- **Compressão**: Gzip para economia de espaço
- **Metadados**: Informações completas de cada backup
- **Rotação**: Limpeza automática de backups antigos

### Tratamento de Erros
- **Rollback**: Possibilidade de restaurar backup em caso de problemas
- **Logs Detalhados**: Rastreamento completo de todas as operações
- **Validação**: Verificação de integridade pós-operação

## 📈 Performance

### Otimizações
- **Processamento em Lotes**: Replicação de dados em batches
- **Barras de Progresso**: Feedback visual em tempo real  
- **Conexões Otimizadas**: Pool de conexões inteligente
- **Compressão**: Backups comprimidos economizam espaço

### Métricas
- **Tempo de Execução**: Medição precisa de performance
- **Contadores**: Tabelas processadas, erros, sucessos
- **Estatísticas**: Relatórios detalhados de uso

## 🛠️ Arquitetura Técnica

### Módulos Core
- **config.py**: Gerenciamento de configurações multi-ambiente
- **database.py**: Interface MySQL com pool de conexões
- **backup.py**: Sistema completo de backup e restore
- **replication.py**: Motor principal de replicação
- **logger.py**: Sistema avançado de logging colorido
- **utils.py**: Utilitários e helpers do sistema

### Tecnologias
- **Python 3.13+**: Runtime moderno e performático
- **MySQL Connector**: Driver oficial MySQL
- **tqdm**: Barras de progresso profissionais
- **colorama**: Output colorido no terminal
- **gzip**: Compressão nativa de backups

## 🎯 Casos de Uso

### Desenvolvimento
```
Produção → Development (apenas estruturas)
Staging → Development (estruturas + dados maintain)
```

### Staging/Homologação  
```
Produção → Staging (estruturas + dados maintain)
```

### Testes
```  
Qualquer → Sandbox (configuração flexível)
```

## 📞 Suporte

### Logs do Sistema
- **Localização**: `logs/` directory
- **Níveis**: DEBUG, INFO, WARNING, ERROR
- **Rotação**: Automática por data
- **Cores**: Diferenciação visual por nível

### Solução de Problemas
1. **Verifique Logs**: `logs/replicoop_YYYY-MM-DD.log`
2. **Teste Conexões**: Menu opção [6]
3. **Valide Configuração**: Menu opção [8]
4. **Restaure Backup**: Em caso de problemas críticos

---

**Desenvolvido por Marcus Geraldino**  
*Sistema Profissional de Replicação MySQL v1.0.0*