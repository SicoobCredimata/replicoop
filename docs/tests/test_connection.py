#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de conectividade com o banco de dados
"""

import sys
import os
# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from core.config import ConfigManager
from core.database import DatabaseManager
from core.logger import LoggerManager

def test_connection():
    """Testa conectividade com o banco"""
    
    try:
        print("🔧 TESTE DE CONECTIVIDADE")
        print("=" * 50)
        
        # Inicializa logger
        logger = LoggerManager("test_connection").logger
        
        # Carrega configuração
        config_manager = ConfigManager()
        
        # Testa ambiente sandbox
        print("\n1️⃣ Testando ambiente SANDBOX...")
        try:
            sandbox_config = config_manager.get_database_config("sandbox")
            print(f"   Host: {sandbox_config.host}")
            print(f"   Database: {sandbox_config.dbname}")
            print(f"   Usuario: {sandbox_config.username}")
            
            sandbox_db = DatabaseManager(sandbox_config, logger)
            if sandbox_db.test_connection():
                print("   ✅ SANDBOX conectado com sucesso!")
            else:
                print("   ❌ SANDBOX falhou na conexão")
                
        except Exception as e:
            print(f"   ❌ Erro no SANDBOX: {e}")
        
        # Testa ambiente production
        print("\n2️⃣ Testando ambiente PRODUCTION...")
        try:
            production_config = config_manager.get_database_config("production")
            print(f"   Host: {production_config.host}")
            print(f"   Database: {production_config.dbname}")
            print(f"   Usuario: {production_config.username}")
            
            production_db = DatabaseManager(production_config, logger)
            if production_db.test_connection():
                print("   ✅ PRODUCTION conectado com sucesso!")
            else:
                print("   ❌ PRODUCTION falhou na conexão")
                
        except Exception as e:
            print(f"   ❌ Erro no PRODUCTION: {e}")
            
        print("\n✅ Teste de conectividade concluído")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_connection()
