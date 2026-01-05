use indicatif::{ProgressBar, ProgressStyle};
use std::sync::Arc;
use std::time::Instant;

use crate::backup::BackupManager;
use crate::config::Config;
use crate::database::DatabaseManager;
use crate::error::{ReplicoopError, Result};
use crate::logger::Logger;

pub struct ReplicationManager {
    config: Config,
    logger: Arc<Logger>,
    source_db: Option<DatabaseManager>,
    target_db: Option<DatabaseManager>,
    backup_manager: Option<BackupManager>,
}

impl ReplicationManager {
    pub fn new(config: Config, logger: Arc<Logger>) -> Result<Self> {
        Ok(ReplicationManager {
            config,
            logger,
            source_db: None,
            target_db: None,
            backup_manager: None,
        })
    }

    pub fn setup_databases(&mut self, source_env: &str, target_env: &str) -> Result<()> {
        self.logger.info(&format!(
            "Configurando bancos de dados: {} → {}",
            source_env, target_env
        ));

        let source_config = self.config.get_database_config(source_env)?.clone();
        let target_config = self.config.get_database_config(target_env)?.clone();

        self.source_db = Some(DatabaseManager::new(
            source_config,
            Arc::clone(&self.logger),
        )?);

        self.target_db = Some(DatabaseManager::new(
            target_config,
            Arc::clone(&self.logger),
        )?);

        self.backup_manager = Some(BackupManager::new(
            &self.config.get_backup_path(),
            Arc::clone(&self.logger),
        )?);

        self.logger.success("Bancos de dados configurados");

        Ok(())
    }

    pub fn execute_replication(
        &self,
        tables: Option<Vec<String>>,
        create_backup: bool,
        replicate_data: bool,
    ) -> Result<ReplicationResult> {
        let start_time = Instant::now();

        let source_db = self
            .source_db
            .as_ref()
            .ok_or_else(|| ReplicoopError::Replication("Banco de origem não configurado".into()))?;

        let target_db = self.target_db.as_ref().ok_or_else(|| {
            ReplicoopError::Replication("Banco de destino não configurado".into())
        })?;

        let backup_path = if create_backup {
            self.logger.info("Criando backup antes da replicação...");

            let backup_mgr = self
                .backup_manager
                .as_ref()
                .ok_or_else(|| ReplicoopError::Backup("BackupManager não inicializado".into()))?;

            Some(backup_mgr.create_backup(target_db, "target")?)
        } else {
            None
        };

        // Determina quais tabelas replicar
        let tables_to_replicate = if let Some(tables) = tables {
            tables
        } else {
            source_db.get_tables()?
        };

        self.logger.header(&format!(
            "INICIANDO REPLICAÇÃO DE {} TABELAS",
            tables_to_replicate.len()
        ));

        let maintain_tables = self.config.get_maintain_tables();

        let pb = ProgressBar::new(tables_to_replicate.len() as u64);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("[{elapsed_precise}] {bar:40.cyan/blue} {pos}/{len} {msg}")
                .unwrap()
                .progress_chars("█▓▒░"),
        );

        let mut replicated_tables = Vec::new();
        let mut data_replicated_tables = Vec::new();
        let mut failed_tables = Vec::new();

        // Desabilita verificação de chaves estrangeiras
        target_db.execute("SET FOREIGN_KEY_CHECKS=0")?;

        for table in &tables_to_replicate {
            pb.set_message(format!("Replicando {}", table));

            match self.replicate_table(source_db, target_db, table, replicate_data, maintain_tables)
            {
                Ok(has_data) => {
                    replicated_tables.push(table.clone());
                    if has_data {
                        data_replicated_tables.push(table.clone());
                    }
                }
                Err(e) => {
                    self.logger
                        .error(&format!("Erro ao replicar {}: {}", table, e));
                    failed_tables.push(FailedTable {
                        table: table.clone(),
                        error: e.to_string(),
                    });
                }
            }

            pb.inc(1);
        }

        // Reabilita verificação de chaves estrangeiras
        target_db.execute("SET FOREIGN_KEY_CHECKS=1")?;

        pb.finish_with_message("Replicação concluída");

        let execution_time = start_time.elapsed().as_secs_f64();

        Ok(ReplicationResult {
            success: failed_tables.is_empty(),
            tables_replicated: replicated_tables.len(),
            replicated_tables,
            data_replicated_tables,
            failed_tables,
            execution_time,
            backup_created: backup_path.map(|p| p.to_string_lossy().to_string()),
        })
    }

    fn replicate_table(
        &self,
        source_db: &DatabaseManager,
        target_db: &DatabaseManager,
        table: &str,
        replicate_data: bool,
        maintain_tables: &[String],
    ) -> Result<bool> {
        // Obter CREATE TABLE da origem
        let create_stmt = source_db.get_create_table(table)?;

        // Drop da tabela no destino se existir
        target_db.drop_table(table)?;

        // Criar tabela no destino
        target_db.execute(&create_stmt)?;

        // Replica dados se for tabela maintain e replicate_data estiver ativado
        let should_replicate_data = replicate_data && maintain_tables.contains(&table.to_string());

        if should_replicate_data {
            let mut source_conn = source_db.get_conn()?;
            target_db.copy_table_data(&mut source_conn, table)?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn test_connections(&self) -> Result<Vec<(String, bool)>> {
        let environments = self.config.get_available_environments();
        let mut results = Vec::new();

        for env in environments {
            let config = self.config.get_database_config(&env)?.clone();

            match DatabaseManager::new(config, Arc::clone(&self.logger)) {
                Ok(db_manager) => {
                    let connected = db_manager.test_connection().unwrap_or(false);
                    results.push((env, connected));
                }
                Err(_) => {
                    results.push((env, false));
                }
            }
        }

        Ok(results)
    }

    pub fn get_config(&self) -> &Config {
        &self.config
    }
}

#[derive(Debug)]
pub struct ReplicationResult {
    pub success: bool,
    pub tables_replicated: usize,
    pub replicated_tables: Vec<String>,
    pub data_replicated_tables: Vec<String>,
    pub failed_tables: Vec<FailedTable>,
    pub execution_time: f64,
    pub backup_created: Option<String>,
}

#[derive(Debug)]
pub struct FailedTable {
    pub table: String,
    pub error: String,
}
