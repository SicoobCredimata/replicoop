#!/usr/bin/env python3
"""
Script de teste direto para replicação completa
"""

import sys
import os

# Adiciona o diretório root ao path
sys.path.append(os.path.dirname(__file__))

from core.config import ConfigManager
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.replication import ReplicationManager

def test_full_replication():
    try:
        print("🚀 TESTE: Replicação completa direta")
        print("=" * 50)
        
        # Inicializa o ReplicationManager
        replication_manager = ReplicationManager("config.json")
        
        # Configura os bancos diretamente
        print("\n1️⃣ Configurando bancos...")
        replication_manager.setup_databases("sandbox", "production")
        print("✅ Bancos configurados")
        
        # Executa replicação completa diretamente
        print(f"\n2️⃣ Executando replicação completa...")
        
        result = replication_manager.execute_replication(
            tables=None,  # Usa tabelas maintain
            create_backup=True,
            replicate_data=True  # Replica dados das tabelas maintain
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
            print(f"\n✅ Tabelas replicadas com sucesso ({len(result['replicated_tables'])}):")
            for table in result['replicated_tables']:
                print(f"   - {table}")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_full_replication()
