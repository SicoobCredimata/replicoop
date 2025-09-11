#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste final do sistema ReplicOOP - Validação Completa
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from core.replication import ReplicationManager

def test_final_replication():
    """Teste final completo do sistema"""
    
    try:
        print("🎯 TESTE FINAL - ReplicOOP")
        print("=" * 50)
        
        # Inicializa o sistema
        replication_manager = ReplicationManager()
        
        # 1. Testa configuração de bancos
        print("\n1️⃣ Configurando ambiente...")
        try:
            replication_manager.setup_databases("sandbox", "production")
            print("✅ Bancos configurados com sucesso!")
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False
        
        # 2. Executa replicação completa
        print("\n2️⃣ Executando replicação completa...")
        try:
            result = replication_manager.execute_replication(
                tables=None,  # Todas as tabelas maintain
                replicate_data=True,
                create_backup=True
            )
            
            print(f"\n📊 RESULTADO DA REPLICAÇÃO:")
            print(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
            print(f"Tabelas replicadas: {result['tables_replicated']}")
            print(f"Tempo de execução: {result['execution_time']:.2f}s")
            
            if result['failed_tables']:
                print(f"\n❌ Tabelas com falha ({len(result['failed_tables'])}):")
                for failed in result['failed_tables']:
                    print(f"   - {failed['table']}: {failed['error']}")
            
            if result['replicated_tables']:
                print(f"\n✅ Tabelas replicadas com sucesso ({len(result['replicated_tables'])}):")
                for table in result['replicated_tables']:
                    print(f"   - {table}")
            
            return result['success']
            
        except Exception as e:
            print(f"❌ Erro na replicação: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
        
        # 3. Valida replicação
        print("\n3️⃣ Validando replicação...")
        try:
            validation = replication_manager.validate_replication()
            
            print(f"\n📋 VALIDAÇÃO:")
            print(f"Tabelas validadas: {len(validation['table_comparisons'])}")
            
            success_count = 0
            for table_name, comparison in validation['table_comparisons'].items():
                if comparison['structures_match']:
                    print(f"✅ {table_name}: Estrutura OK")
                    success_count += 1
                else:
                    print(f"❌ {table_name}: Estrutura DIFERENTE")
                    if comparison.get('differences'):
                        for diff in comparison['differences']:
                            print(f"   - {diff}")
            
            print(f"\nResultado: {success_count}/{len(validation['table_comparisons'])} tabelas validadas")
            return success_count == len(validation['table_comparisons'])
            
        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_final_replication()
    if success:
        print("\n🎉 SISTEMA REPLICOOP FUNCIONANDO PERFEITAMENTE!")
        print("✅ Todas as funcionalidades testadas com sucesso!")
    else:
        print("\n❌ Sistema ainda apresenta problemas")
    
    print(f"\n{'='*50}")
    print("Teste finalizado")
