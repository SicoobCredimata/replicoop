#!/usr/bin/env python3
"""
Script de debug específico para testar o plano de replicação
"""

import sys
import os

# Adiciona o diretório root ao path
sys.path.append(os.path.dirname(__file__))

from core.config import ConfigManager
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.replication import ReplicationManager

def debug_replication_plan():
    try:
        print("🔍 DEBUG: Testando plano de replicação")
        print("=" * 50)
        
        # Inicializa o ReplicationManager
        replication_manager = ReplicationManager("config.json")
        
        # Configura os bancos
        print("\n1️⃣ Configurando bancos...")
        replication_manager.setup_databases("sandbox", "production")
        print("✅ Bancos configurados")
        
        # Testa tabelas individualmente
        print("\n2️⃣ Testando acesso às tabelas...")
        
        # Tabelas de origem
        print("📤 ORIGEM (sandbox):")
        source_tables = replication_manager.source_db.get_tables()
        print(f"   Total: {len(source_tables)} tabelas")
        if source_tables:
            for i, table in enumerate(source_tables[:5], 1):
                print(f"   {i}. {table}")
            if len(source_tables) > 5:
                print(f"   ... e mais {len(source_tables) - 5}")
        
        # Tabelas de destino
        print("\n📥 DESTINO (production):")
        target_tables = replication_manager.target_db.get_tables()
        print(f"   Total: {len(target_tables)} tabelas")
        if target_tables:
            for table in target_tables:
                print(f"   - {table}")
        
        # Tabelas para manter
        print("\n🔧 TABELAS MAINTAIN:")
        maintain_tables = replication_manager.config_manager.get_maintain_tables()
        print(f"   Configuradas: {maintain_tables}")
        
        # Testa criação do plano
        print("\n3️⃣ Testando criação do plano...")
        try:
            plan = replication_manager.get_replication_plan()
            print("✅ Plano criado com sucesso!")
            
            print(f"\n📊 DETALHES DO PLANO:")
            print(f"   Tabelas origem: {plan['source_tables']}")
            print(f"   Tabelas destino: {plan['target_tables']}")
            print(f"   Para replicar: {len(plan['tables_to_replicate'])}")
            print(f"   Para dropar: {len(plan['tables_to_drop'])}")
            print(f"   Avisos: {len(plan['warnings'])}")
            
            if plan['warnings']:
                print(f"\n⚠️  AVISOS:")
                for warning in plan['warnings']:
                    print(f"   - {warning}")
            
        except Exception as e:
            print(f"❌ Erro na criação do plano: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # Testa cada passo individualmente
            print(f"\n🔍 DEBUG DETALHADO:")
            
            # Testa get_maintain_tables
            try:
                maintain = replication_manager.config_manager.get_maintain_tables()
                print(f"   get_maintain_tables(): {maintain}")
            except Exception as e:
                print(f"   get_maintain_tables() ERRO: {e}")
            
            # Testa source_db.get_tables()
            try:
                source = replication_manager.source_db.get_tables()
                print(f"   source_db.get_tables(): {len(source)} tabelas")
            except Exception as e:
                print(f"   source_db.get_tables() ERRO: {e}")
            
            # Testa target_db.get_tables()
            try:
                target = replication_manager.target_db.get_tables()
                print(f"   target_db.get_tables(): {len(target)} tabelas")
            except Exception as e:
                print(f"   target_db.get_tables() ERRO: {e}")
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_replication_plan()
