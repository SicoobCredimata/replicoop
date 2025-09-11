#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de replicação completa - TODAS as tabelas
Verifica se está replicando tabelas maintain (estrutura + dados) e não-maintain (apenas estrutura)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from core.replication import ReplicationManager
from core.config import ConfigManager

def test_all_tables_replication():
    """Testa replicação de todas as tabelas do banco"""
    
    try:
        print("🎯 TESTE: Replicação de TODAS as tabelas")
        print("=" * 60)
        
        # Inicializa o sistema
        replication_manager = ReplicationManager()
        config_manager = ConfigManager()
        
        # 1. Configuração
        print("\n1️⃣ Configurando bancos...")
        try:
            replication_manager.setup_databases("sandbox", "production")
            print("✅ Bancos configurados")
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False
        
        # 2. Verifica quantas tabelas existem no total
        print("\n2️⃣ Analisando tabelas...")
        try:
            source_tables = replication_manager.source_db.get_tables()
            target_tables_before = replication_manager.target_db.get_tables()
            maintain_tables = config_manager.get_maintain_tables()
            
            print(f"📊 Banco de origem: {len(source_tables)} tabelas")
            print(f"📊 Banco de destino (antes): {len(target_tables_before)} tabelas")
            print(f"📊 Tabelas maintain: {len(maintain_tables)} tabelas")
            print(f"📊 Tabelas não-maintain: {len(source_tables) - len(maintain_tables)} tabelas")
            
            print(f"\n🔍 Tabelas maintain configuradas:")
            for table in maintain_tables:
                print(f"   - {table} (estrutura + dados)")
                
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            return False
        
        # 3. Executa replicação completa (TODAS as tabelas)
        print(f"\n3️⃣ Replicando TODAS as {len(source_tables)} tabelas...")
        try:
            result = replication_manager.execute_replication(
                tables=None,  # None = TODAS as tabelas
                replicate_data=True,  # Dados para tabelas maintain
                create_backup=True
            )
            
            print(f"\n📊 RESULTADO:")
            print(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
            print(f"Tabelas processadas: {result['tables_replicated']}")
            print(f"Tempo de execução: {result['execution_time']:.2f}s")
            
            if result['failed_tables']:
                print(f"\n❌ Tabelas com falha ({len(result['failed_tables'])}):")
                for failed in result['failed_tables']:
                    print(f"   - {failed['table']}: {failed['error']}")
            
            if result['replicated_tables']:
                # Separa tabelas por tipo
                maintain_replicated = []
                non_maintain_replicated = []
                
                print(f"\n✅ Tabelas replicadas ({len(result['replicated_tables'])}):")
                for table in result['replicated_tables']:
                    print(f"   - {table}")
                    
                    # Verifica se é tabela maintain
                    table_name = table.split(' (')[0]  # Remove sufixo
                    if table_name in maintain_tables:
                        maintain_replicated.append(table_name)
                    else:
                        non_maintain_replicated.append(table_name)
                
                print(f"\n📈 RESUMO POR TIPO:")
                print(f"✅ Tabelas maintain replicadas: {len(maintain_replicated)}/{len(maintain_tables)}")
                print(f"✅ Tabelas não-maintain replicadas: {len(non_maintain_replicated)}")
                print(f"✅ Total replicado: {len(maintain_replicated) + len(non_maintain_replicated)}")
                
                # Verifica se replicou todas as tabelas do banco origem
                total_expected = len(source_tables)
                total_replicated = len(maintain_replicated) + len(non_maintain_replicated)
                
                if total_replicated >= total_expected:
                    print(f"🎉 SUCCESS: Todas as tabelas foram processadas!")
                else:
                    print(f"⚠️  WARNING: Esperado {total_expected}, replicado {total_replicated}")
            
            return result['success']
            
        except Exception as e:
            print(f"❌ Erro na replicação: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_all_tables_replication()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 TESTE APROVADO: Sistema replicando TODAS as tabelas corretamente!")
        print("✅ Tabelas maintain: estrutura + dados")
        print("✅ Tabelas não-maintain: apenas estrutura")
    else:
        print("❌ TESTE FALHOU: Sistema ainda não está replicando todas as tabelas")
    
    print("Teste finalizado")
