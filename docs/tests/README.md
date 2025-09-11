# 🧪 **Testes do Sistema ReplicOOP**

Este diretório contém todos os testes desenvolvidos durante a implementação e debugging do sistema ReplicOOP.

---

## 📁 **Estrutura dos Testes**

### **🔧 Testes de Desenvolvimento/Debug**
- **`debug_tables.py`** - Debug inicial de listagem de tabelas
- **`debug_plan.py`** - Debug do plano de replicação
- **`test_single_table.py`** - Teste de replicação de tabela única

### **🎯 Testes Funcionais**
- **`test_connection.py`** - Teste de conectividade com bancos de dados
- **`test_full_replication.py`** - Teste de replicação das tabelas maintain
- **`test_all_tables.py`** - Teste completo de todas as tabelas
- **`test_final.py`** - Teste final com validação completa

---

## 🚀 **Como Executar os Testes**

### **Pré-requisitos:**
- Sistema ReplicOOP configurado
- Arquivo `config.json` válido
- Conectividade com os bancos de dados

### **Execução:**
```bash
# Teste de conectividade
python docs/tests/test_connection.py

# Teste de tabela única  
python docs/tests/test_single_table.py

# Teste completo (todas as tabelas)
python docs/tests/test_all_tables.py

# Teste final com validação
python docs/tests/test_final.py
```

---

## 📋 **Descrição dos Testes**

### **1. test_connection.py**
- **Objetivo**: Valida conectividade com os bancos
- **Testa**: Configurações, credenciais, rede
- **Uso**: Diagnóstico de problemas de conexão

### **2. test_single_table.py** 
- **Objetivo**: Testa replicação de uma tabela específica
- **Testa**: Criação de estrutura individual
- **Uso**: Debug de tabelas problemáticas

### **3. test_full_replication.py**
- **Objetivo**: Testa replicação das tabelas maintain
- **Testa**: Estrutura + dados das tabelas configuradas
- **Uso**: Validação das tabelas críticas

### **4. test_all_tables.py**
- **Objetivo**: Testa replicação de TODAS as tabelas
- **Testa**: Sistema completo com diferenciação de tipos
- **Uso**: Teste de aceitação principal

### **5. test_final.py**
- **Objetivo**: Teste completo com validação
- **Testa**: Replicação + validação de resultados
- **Uso**: Certificação final do sistema

---

## 📊 **Resultados Esperados**

### **✅ Teste bem-sucedido:**
```
🎉 TESTE APROVADO: Sistema funcionando perfeitamente!
✅ Todas as funcionalidades testadas com sucesso!
```

### **❌ Teste com falha:**
```
❌ TESTE FALHOU: [Descrição do problema]
Traceback: [Detalhes técnicos]
```

---

## 🔍 **Debugging e Troubleshooting**

### **Problemas Comuns:**

#### **1. Erro de Conectividade**
- **Sintoma**: `Can't connect to MySQL server`
- **Solução**: Verificar config.json e conectividade de rede
- **Teste**: `test_connection.py`

#### **2. Foreign Key Errors**
- **Sintoma**: `Foreign key constraint fails`
- **Solução**: Sistema resolve automaticamente com ordenação
- **Teste**: `test_all_tables.py`

#### **3. Tabelas não Encontradas**
- **Sintoma**: `Table doesn't exist`
- **Solução**: Verificar lista maintain_tables em config.json
- **Teste**: `debug_tables.py`

---

## 📈 **Evolução dos Testes**

### **Fase 1 - Debug Inicial**
- Testes básicos de conectividade
- Listagem de tabelas
- Problemas de encoding no terminal

### **Fase 2 - Replicação Básica**  
- Replicação de tabelas maintain
- Resolução de Foreign Keys
- Sistema de backup

### **Fase 3 - Sistema Completo**
- Todas as tabelas (maintain + não-maintain)
- Ordenação por dependências
- Diferenciação de tipos de replicação

### **Fase 4 - Validação Final**
- Testes de aceitação
- Validação de integridade
- Performance e robustez

---

## 🎯 **Casos de Teste Cobertos**

- ✅ **Conectividade**: Sandbox e Production
- ✅ **Tabelas Maintain**: Estrutura + dados
- ✅ **Tabelas Não-Maintain**: Apenas estrutura  
- ✅ **Foreign Keys**: Dependências e ordenação
- ✅ **Backup**: Criação automática
- ✅ **Logs**: Sistema de logging
- ✅ **Erro Handling**: Recuperação de falhas
- ✅ **Performance**: 33 tabelas em ~9 segundos
- ✅ **Integridade**: Validação de resultados

---

## 📝 **Notas de Desenvolvimento**

### **Problemas Resolvidos:**
1. **Encoding de terminal** - Limpeza de caracteres especiais
2. **Foreign Key constraints** - Ordenação topológica
3. **Cursor format inconsistency** - Tratamento flexível
4. **Environment configuration** - Configuração dinâmica
5. **Backup system** - Fallback para Python nativo

### **Lições Aprendidas:**
- Testes incrementais são essenciais
- Foreign Keys requerem ordenação cuidadosa  
- Sistema de backup é crítico para segurança
- Logs detalhados facilitam debugging
- Separação de responsabilidades melhora manutenibilidade

---

*Documentação dos testes - Atualizada em: 11 de setembro de 2025*