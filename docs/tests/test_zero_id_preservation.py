#!/usr/bin/env python3
"""
Teste específico para validação de preservação de IDs com valor 0 (zero)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.replication import ReplicationManager
from core.config import ConfigManager
from core.logger import LoggerManager

def test_zero_id_preservation():
    """
    Teste específico para validar que IDs com valor 0 são preservados durante a replicação
    """
    print("\n🧪 TESTE DE PRESERVAÇÃO DE IDs COM VALOR ZERO")
    print("=" * 60)
    
    try:
        # 1. Inicializar sistema
        print("\n1️⃣ Inicializando sistema...")
        
        replication_manager = ReplicationManager("config.json")
        print("✅ Sistema inicializado")
        
        # 2. Configurar bancos (usando configuração padrão)
        print("\n2️⃣ Configurando conexões com bancos...")
        replication_manager.setup_databases("sandbox", "production")
        print("✅ Bancos configurados")
        
        # 3. Verificar se há registros com ID = 0 no banco origem
        print("\n3️⃣ Verificando registros com ID = 0 no banco origem...")
        
        source_db = replication_manager.source_db
        target_db = replication_manager.target_db
        
        # Lista de tabelas para verificar
        test_tables = ["agencies", "users"]  # Substitua pelos nomes reais das tabelas
        
        zero_id_records = {}
        
        for table in test_tables:
            try:
                # Busca registros com ID = 0
                query = f"SELECT * FROM `{table}` WHERE id = 0"
                records = source_db.execute_query(query)
                
                if records:
                    zero_id_records[table] = records
                    print(f"   📍 Tabela '{table}': {len(records)} registro(s) com ID = 0")
                    for record in records:
                        print(f"      → {record}")
                else:
                    print(f"   ⚪ Tabela '{table}': Nenhum registro com ID = 0")
                    
            except Exception as e:
                print(f"   ⚠️  Erro ao verificar tabela '{table}': {e}")
        
        if not zero_id_records:
            print("\n⚠️  Nenhum registro com ID = 0 encontrado para testar")
            print("💡 Vou criar registros de teste...")
            
            # Criar registro de teste na tabela agencies
            try:
                # Verificar se tabela existe
                tables = source_db.get_tables()
                if "agencies" in tables:
                    # Tentar inserir registro com ID = 0
                    source_db.execute_query("SET sql_mode = ''", fetch_results=False)
                    insert_query = "INSERT INTO `agencies` (id, name, code) VALUES (0, 'Agência Principal', '0000')"
                    source_db.execute_query(insert_query, fetch_results=False)
                    
                    # Verificar se foi inserido
                    check_query = "SELECT * FROM `agencies` WHERE id = 0"
                    test_record = source_db.execute_query(check_query)
                    
                    if test_record:
                        zero_id_records["agencies"] = test_record
                        print(f"   ✅ Registro de teste criado: {test_record[0]}")
                    else:
                        print("   ❌ Falha ao criar registro de teste")
                        
            except Exception as e:
                print(f"   ❌ Erro ao criar registro de teste: {e}")
        
        # 4. Executar replicação
        if zero_id_records:
            print("\n4️⃣ Executando replicação...")
            
            # Executar replicação das tabelas com registros ID = 0
            for table in zero_id_records.keys():
                print(f"   🔄 Replicando tabela '{table}'...")
                try:
                    replication_manager.execute_replication([table])
                    print(f"   ✅ Tabela '{table}' replicada")
                except Exception as e:
                    print(f"   ❌ Erro na replicação de '{table}': {e}")
            
            # 5. Validar preservação de IDs
            print("\n5️⃣ Validando preservação de IDs com valor 0...")
            
            validation_passed = True
            
            for table, original_records in zero_id_records.items():
                print(f"\n   📋 Validando tabela '{table}':")
                
                try:
                    # Buscar registros com ID = 0 no destino
                    query = f"SELECT * FROM `{table}` WHERE id = 0"
                    replicated_records = target_db.execute_query(query)
                    
                    if replicated_records:
                        print(f"      ✅ {len(replicated_records)} registro(s) com ID = 0 preservado(s)")
                        
                        # Comparar dados
                        for i, original in enumerate(original_records):
                            if i < len(replicated_records):
                                replicated = replicated_records[i]
                                print(f"         Original:  {original}")
                                print(f"         Replicado: {replicated}")
                                
                                # Verificar se ID foi preservado
                                if original.get('id') == 0 and replicated.get('id') == 0:
                                    print(f"         ✅ ID = 0 preservado corretamente")
                                else:
                                    print(f"         ❌ ID não preservado! Original: {original.get('id')} → Replicado: {replicated.get('id')}")
                                    validation_passed = False
                                    
                            else:
                                print(f"         ❌ Registro {i+1} não encontrado no destino")
                                validation_passed = False
                    else:
                        print(f"      ❌ Nenhum registro com ID = 0 encontrado no destino!")
                        validation_passed = False
                        
                        # Verificar se foi inserido com outro ID
                        all_records_query = f"SELECT * FROM `{table}` ORDER BY id LIMIT 10"
                        all_records = target_db.execute_query(all_records_query)
                        
                        print(f"         Primeiros registros no destino:")
                        for record in all_records[:3]:
                            print(f"         → {record}")
                        
                except Exception as e:
                    print(f"      ❌ Erro ao validar '{table}': {e}")
                    validation_passed = False
            
            # 6. Resultado final
            print("\n" + "=" * 60)
            if validation_passed:
                print("🎉 TESTE PASSOU: IDs com valor 0 foram preservados corretamente!")
                return True
            else:
                print("❌ TESTE FALHOU: IDs com valor 0 NÃO foram preservados!")
                return False
        
        else:
            print("\n❌ Teste não pôde ser executado: nenhum registro com ID = 0 disponível")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_zero_id_preservation()
    exit(0 if success else 1)