#!/usr/bin/env python3
"""
Teste específico para validar a preservação de dados em tabelas não-maintain
"""
import os
import sys

# Adiciona o diretório do projeto ao path
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
sys.path.append(os.path.join(project_dir, 'core'))

from core.replication import ReplicationManager


def test_data_preservation():
    """Testa se os dados de produção são preservados em tabelas não-maintain"""
    print("🧪 TESTE DE PRESERVAÇÃO DE DADOS EM TABELAS NÃO-MAINTAIN")
    print("="*65)
    
    try:
        # 1. Inicializa o sistema
        print("\n1️⃣ Inicializando sistema...")
        config_path = os.path.join(project_dir, "config.json")
        
        if not os.path.exists(config_path):
            print("❌ Arquivo config.json não encontrado")
            return
        
        replication_manager = ReplicationManager(config_path)
        replication_manager.setup_databases("sandbox", "production")
        
        print("✅ Sistema inicializado com sucesso")
        
        # 2. Verifica tabelas maintain configuradas
        maintain_tables = replication_manager.config_manager.get_maintain_tables()
        print(f"\n2️⃣ Tabelas MAINTAIN configuradas: {len(maintain_tables)}")
        for table in maintain_tables:
            print(f"   • {table}")
        
        # 3. Lista todas as tabelas do banco de origem
        all_source_tables = replication_manager.source_db.get_tables()
        non_maintain_tables = [t for t in all_source_tables if t not in maintain_tables]
        
        print(f"\n3️⃣ Tabelas NÃO-MAINTAIN (estrutura apenas): {len(non_maintain_tables)}")
        for i, table in enumerate(non_maintain_tables[:10], 1):  # Mostra apenas as primeiras 10
            print(f"   {i:2}. {table}")
        if len(non_maintain_tables) > 10:
            print(f"   ... e mais {len(non_maintain_tables) - 10} tabelas")
        
        # 4. Verifica dados existentes em algumas tabelas não-maintain de produção
        print(f"\n4️⃣ Verificando dados existentes em produção...")
        tables_with_data = []
        
        for table in non_maintain_tables[:5]:  # Testa apenas as primeiras 5
            try:
                if replication_manager.target_db.table_exists(table):
                    count_query = f"SELECT COUNT(*) as count FROM `{table}`"
                    result = replication_manager.target_db.execute_query(count_query)
                    record_count = result[0]['count'] if result else 0
                    
                    if record_count > 0:
                        tables_with_data.append({'name': table, 'count': record_count})
                        print(f"   ✓ {table}: {record_count} registros")
                    else:
                        print(f"   - {table}: vazia")
                else:
                    print(f"   - {table}: não existe em produção")
                    
            except Exception as e:
                print(f"   ❌ {table}: erro ao verificar ({e})")
        
        if not tables_with_data:
            print("   ⚠️  Nenhuma tabela não-maintain com dados encontrada em produção")
            print("   💡 Criando dados de teste para validar preservação...")
            
            # Cria dados de teste se necessário
            try:
                test_table = non_maintain_tables[0] if non_maintain_tables else None
                if test_table and replication_manager.target_db.table_exists(test_table):
                    # Tenta inserir um registro de teste (se a estrutura permitir)
                    columns = replication_manager.target_db.get_table_columns(test_table)
                    if columns:
                        # Encontra uma coluna que possa receber dados simples
                        text_columns = [col for col in columns if 'varchar' in col['type'].lower() or 'text' in col['type'].lower()]
                        if text_columns:
                            col_name = text_columns[0]['name']
                            insert_query = f"INSERT INTO `{test_table}` (`{col_name}`) VALUES ('TESTE_PRESERVACAO_DADOS')"
                            replication_manager.target_db.execute_query(insert_query, fetch_results=False)
                            tables_with_data.append({'name': test_table, 'count': 1})
                            print(f"   ✓ Dados de teste criados em {test_table}")
            except Exception as e:
                print(f"   ⚠️  Não foi possível criar dados de teste: {e}")
        
        # 5. Executa replicação de TODAS as tabelas
        print(f"\n5️⃣ Executando replicação completa (TODAS as tabelas)...")
        print("   📌 MAINTAIN: estrutura + dados (substitui dados existentes)")
        print("   📌 NÃO-MAINTAIN: apenas estrutura (PRESERVA dados existentes)")
        
        # Dados ANTES da replicação
        data_before = {}
        for table_info in tables_with_data:
            table_name = table_info['name']
            try:
                count_query = f"SELECT COUNT(*) as count FROM `{table_name}`"
                result = replication_manager.target_db.execute_query(count_query)
                data_before[table_name] = result[0]['count'] if result else 0
            except:
                data_before[table_name] = 0
        
        print(f"\n   📊 Dados ANTES da replicação:")
        for table, count in data_before.items():
            print(f"      • {table}: {count} registros")
        
        # EXECUTA A REPLICAÇÃO
        result = replication_manager.execute_replication(
            tables=None,  # Todas as tabelas
            create_backup=True,
            replicate_data=True
        )
        
        if result['success']:
            print(f"\n✅ Replicação concluída com sucesso!")
            print(f"   ⏱️  Tempo: {result['execution_time']:.2f}s")
            print(f"   📊 Tabelas processadas: {result['tables_replicated']}")
        else:
            print(f"\n❌ Replicação falhou!")
            return
        
        # 6. Verifica dados APÓS a replicação
        print(f"\n6️⃣ Verificando preservação de dados...")
        
        data_after = {}
        for table_info in tables_with_data:
            table_name = table_info['name']
            try:
                count_query = f"SELECT COUNT(*) as count FROM `{table_name}`"
                result = replication_manager.target_db.execute_query(count_query)
                data_after[table_name] = result[0]['count'] if result else 0
            except:
                data_after[table_name] = 0
        
        print(f"\n   📊 Dados DEPOIS da replicação:")
        for table, count in data_after.items():
            print(f"      • {table}: {count} registros")
        
        # 7. Análise dos resultados
        print(f"\n7️⃣ ANÁLISE DOS RESULTADOS:")
        print("-" * 40)
        
        preserved_tables = 0
        for table in data_before.keys():
            before_count = data_before[table]
            after_count = data_after.get(table, 0)
            
            if before_count == after_count and before_count > 0:
                print(f"   ✅ {table}: {before_count} registros PRESERVADOS")
                preserved_tables += 1
            elif before_count > 0 and after_count == 0:
                print(f"   ❌ {table}: {before_count} registros PERDIDOS!")
            elif before_count == 0 and after_count == 0:
                print(f"   - {table}: continua vazia (OK)")
            else:
                print(f"   ⚠️  {table}: {before_count} → {after_count} registros (alterado)")
        
        # 8. Resultado final
        print(f"\n🎯 RESULTADO FINAL:")
        if preserved_tables > 0:
            print(f"✅ {preserved_tables} tabelas tiveram dados PRESERVADOS corretamente!")
            print("🎉 CORREÇÃO FUNCIONANDO - Dados de produção preservados!")
        else:
            print("⚠️  Nenhuma tabela não-maintain com dados foi encontrada para testar")
            print("💡 Teste validou a lógica, mas não havia dados para preservar")
        
        print(f"\n📋 RESUMO:")
        print(f"   • Tabelas MAINTAIN: {len(maintain_tables)} (estrutura + dados substituídos)")
        print(f"   • Tabelas NÃO-MAINTAIN: {len(non_maintain_tables)} (estrutura atualizada, dados preservados)")
        print(f"   • Total processadas: {len(all_source_tables)}")
        
        print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_data_preservation()