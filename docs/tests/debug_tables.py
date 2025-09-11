#!/usr/bin/env python3
"""
Script de debug para verificar as tabelas dos bancos
"""

import sys
import os

# Adiciona o diretório root ao path
sys.path.append(os.path.dirname(__file__))

from core.config import ConfigManager
from core.database import DatabaseManager
from core.logger import LoggerManager

def debug_tables():
    try:
        # Inicializa componentes
        config_manager = ConfigManager("config.json")
        logger = LoggerManager()
        
        # Testa ambos os ambientes
        for env_name in ['sandbox', 'production']:
            print(f"\n=== TESTANDO AMBIENTE: {env_name} ===")
            
            try:
                # Obtém configuração
                db_config = config_manager.get_database_config(env_name)
                db_manager = DatabaseManager(db_config, logger)
                
                print(f"Banco: {db_config.dbname}")
                print(f"Host: {db_config.host}:{db_config.port}")
                print(f"User: {db_config.username}")
                
                # Testa conexão
                if db_manager.test_connection():
                    print("✅ Conexão OK")
                    
                    # Lista tabelas
                    tables = db_manager.get_tables()
                    print(f"📊 Total de tabelas: {len(tables)}")
                    
                    if tables:
                        print("📋 Tabelas encontradas:")
                        for i, table in enumerate(tables[:10], 1):  # Mostra apenas as 10 primeiras
                            print(f"  {i}. {table}")
                        if len(tables) > 10:
                            print(f"  ... e mais {len(tables) - 10} tabelas")
                    else:
                        print("❌ Nenhuma tabela encontrada!")
                        
                        # Debug adicional - executa SHOW TABLES manualmente
                        print("\n🔍 Debug: Executando SHOW TABLES manualmente...")
                        with db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("SHOW TABLES")
                            raw_results = cursor.fetchall()
                            print(f"Raw results: {raw_results}")
                            cursor.close()
                else:
                    print("❌ Falha na conexão")
                    
            except Exception as e:
                print(f"❌ Erro no ambiente {env_name}: {e}")
        
        # Testa configuração maintain
        print(f"\n=== TABELAS PARA MANTER ===")
        maintain_tables = config_manager.get_maintain_tables()
        print(f"Tabelas configuradas: {maintain_tables}")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    debug_tables()
