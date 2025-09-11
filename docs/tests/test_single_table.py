#!/usr/bin/env python3
"""
Script de teste específico para testar replicação de uma única tabela
"""

import sys
import os

# Adiciona o diretório root ao path
sys.path.append(os.path.dirname(__file__))

from core.config import ConfigManager
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.replication import ReplicationManager

def test_single_table_replication():
    try:
        print("🔧 TESTE: Replicação de uma única tabela")
        print("=" * 50)
        
        # Inicializa o ReplicationManager
        replication_manager = ReplicationManager("config.json")
        
        # Configura os bancos
        print("\n1️⃣ Configurando bancos...")
        replication_manager.setup_databases("sandbox", "production")
        print("✅ Bancos configurados")
        
        # Testa criação do statement para uma tabela específica
        table_name = "agencies"  # Vamos testar com agencies
        
        print(f"\n2️⃣ Testando tabela: {table_name}")
        
        try:
            # Testa se tabela existe no origem
            source_tables = replication_manager.source_db.get_tables()
            if table_name not in source_tables:
                print(f"❌ Tabela {table_name} não existe no banco de origem!")
                return
            
            print(f"✅ Tabela {table_name} encontrada no banco de origem")
            
            # Testa obtenção do CREATE TABLE statement
            print(f"\n3️⃣ Obtendo CREATE TABLE statement...")
            create_statement = replication_manager.source_db.get_create_table_statement(table_name)
            print(f"✅ CREATE TABLE obtido com sucesso!")
            print(f"📄 Statement (primeiros 200 chars):")
            print(f"   {create_statement[:200]}...")
            
            # Testa criação da tabela no destino
            print(f"\n4️⃣ Testando criação no banco de destino...")
            
            # Remove tabela se existir
            replication_manager.target_db.drop_table_if_exists(table_name)
            print(f"✅ Tabela {table_name} removida do destino (se existia)")
            
            # Cria tabela
            replication_manager.target_db.create_table_from_statement(create_statement)
            print(f"✅ Tabela {table_name} criada no destino!")
            
            # Verifica se foi criada corretamente
            target_tables = replication_manager.target_db.get_tables()
            if table_name in target_tables:
                print(f"✅ Confirmado: {table_name} está presente no banco de destino")
                
                # Testa estrutura
                structure = replication_manager.target_db.get_table_structure(table_name)
                print(f"📊 Estrutura da tabela: {len(structure)} colunas")
                for col in structure[:3]:  # Mostra primeiras 3 colunas
                    if isinstance(col, dict) and 'Field' in col:
                        print(f"   - {col['Field']}: {col.get('Type', 'N/A')}")
                    else:
                        print(f"   - {col}")
                
            else:
                print(f"❌ Erro: {table_name} não foi encontrada no destino após criação")
            
        except Exception as e:
            print(f"❌ Erro no teste da tabela {table_name}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_single_table_replication()
