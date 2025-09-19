# Correção: Preservação de IDs com Valor Zero (ID=0)

## 📋 Problema Identificado

Durante a replicação de dados entre bancos MySQL/MariaDB, registros com ID=0 estavam sendo convertidos automaticamente para outros valores (exemplo: id=0 virava id=98 ou id=1), causando **perda de integridade referencial**.

### Situação Anterior ❌
```
Origem:  id=0, agency_id=0, name="Volta Grande"
Destino: id=98, agency_id=1, name="Volta Grande"  // IDs alterados!
```

### Situação Corrigida ✅
```
Origem:  id=0, agency_id=0, name="Volta Grande"
Destino: id=0, agency_id=0, name="Volta Grande"   // IDs preservados exatamente!
```

## 🔧 Causa Raiz do Problema

O MySQL/MariaDB possui comportamento especial para campos AUTO_INCREMENT:
- **ID=0 é automaticamente convertido** para o próximo valor da sequência
- Configurações como `NO_AUTO_VALUE_ON_ZERO` e `REPLACE INTO` não resolvem completamente
- O problema persiste mesmo com mudanças no SQL_MODE

## 💡 Solução Implementada

### Estratégia: Remoção Temporária do AUTO_INCREMENT

1. **Detecção**: Sistema identifica tabelas com registros ID=0 na origem
2. **Preparação**: Remove temporariamente o AUTO_INCREMENT da coluna 
3. **Inserção**: Executa INSERT INTO com IDs exatos (incluindo 0)
4. **Decisão Inteligente**: 
   - Se há registros ID=0: **não restaura** AUTO_INCREMENT (preserva integridade)
   - Se não há registros ID=0: **restaura** AUTO_INCREMENT normalmente

### Código Principal (core/replication.py)

```python
# Detecta registros com ID=0 na origem
check_zero_query = f"SELECT COUNT(*) as count FROM `{table_name}` WHERE `{auto_increment_field}` = 0"
has_zero_id = self.source_db.execute_query(check_zero_query)[0]['count'] > 0

if has_zero_id:
    # Remove AUTO_INCREMENT temporariamente
    alter_remove_query = f"ALTER TABLE `{table_name}` MODIFY COLUMN {column_def}"
    self.target_db.execute_query(alter_remove_query, fetch_results=False)
    
    # Insere dados com IDs exatos
    insert_query = f"INSERT INTO `{table_name}` (...) VALUES (...)"
    
    # DECISÃO CRÍTICA: NÃO restaurar AUTO_INCREMENT se há ID=0
    # pois MySQL converteria ID=0 para próximo valor disponível
    self.logger.warning("AUTO_INCREMENT não será restaurado para preservar IDs=0")
```

## ⚖️ Trade-offs da Solução

### ✅ Vantagens
- **Preservação Total**: IDs=0 mantidos exatamente como na origem
- **Integridade Referencial**: Relacionamentos FK preservados
- **Automático**: Sistema detecta e aplica correção automaticamente
- **Seletivo**: Aplica apenas em tabelas que realmente precisam

### ⚠️ Considerações
- **Tabelas com ID=0**: Ficam sem AUTO_INCREMENT para preservar integridade
- **Novos Registros**: Requerem especificação manual de ID
- **Trade-off Consciente**: Prioriza integridade dos dados existentes

## 🧪 Validação

### Teste Implementado
```bash
python docs/tests/test_zero_id_preservation.py
```

### Resultado do Teste
```
🎉 TESTE PASSOU: IDs com valor 0 foram preservados corretamente!

✅ 1 registro(s) com ID = 0 preservado(s)
   Original:  {'id': 0, 'name': 'Volta Grande', ...}
   Replicado: {'id': 0, 'name': 'Volta Grande', ...}
   ✅ ID = 0 preservado corretamente
```

## 🎯 Impacto

Esta correção garante que o sistema ReplicOOP faça replicação **exata** dos dados:
- ✅ "se ele tem id = 0 ele ficará com id = 0" (requisito do usuário atendido)
- ✅ Preservação de relacionamentos entre tabelas
- ✅ Integridade referencial mantida
- ✅ Dados idênticos entre origem e destino

## 📊 Tabelas Afetadas

O sistema automaticamente identifica e trata todas as tabelas que:
1. Possuem campos AUTO_INCREMENT
2. Contêm registros com ID=0 na origem
3. Necessitam preservação exata de IDs

**Exemplo prático**: Tabela `agencies` tinha registro com ID=0 que estava virando ID=98 → agora permanece ID=0.

---

**Status**: ✅ **RESOLVIDO** - Sistema agora preserva IDs com valor zero corretamente durante replicação.