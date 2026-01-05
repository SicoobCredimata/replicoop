use chrono::{DateTime, Local};
use flate2::write::GzEncoder;
use flate2::Compression;
use serde::{Deserialize, Serialize};
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::sync::Arc;

use crate::database::DatabaseManager;
use crate::error::Result;
use crate::logger::Logger;

#[derive(Debug, Serialize, Deserialize)]
pub struct BackupMetadata {
    pub timestamp: DateTime<Local>,
    pub database: String,
    pub environment: String,
    pub backup_file: String,
    pub size_bytes: u64,
    pub tables_count: usize,
}

pub struct BackupManager {
    backup_path: PathBuf,
    logger: Arc<Logger>,
}

impl BackupManager {
    pub fn new(backup_path: &str, logger: Arc<Logger>) -> Result<Self> {
        fs::create_dir_all(backup_path)?;

        Ok(BackupManager {
            backup_path: PathBuf::from(backup_path),
            logger,
        })
    }

    pub fn create_backup(
        &self,
        db_manager: &DatabaseManager,
        environment: &str,
    ) -> Result<PathBuf> {
        let timestamp = Local::now();
        let filename = format!(
            "backup_{}_{}_{}.sql.gz",
            environment,
            db_manager.get_database_name(),
            timestamp.format("%Y%m%d_%H%M%S")
        );

        let backup_file = self.backup_path.join(&filename);

        self.logger.info(&format!("Criando backup: {}", filename));

        // Obtém todas as tabelas
        let tables = db_manager.get_tables()?;

        self.logger
            .info(&format!("Backup de {} tabelas", tables.len()));

        // Cria o arquivo comprimido
        let file = File::create(&backup_file)?;
        let buf_writer = BufWriter::new(file);
        let mut encoder = GzEncoder::new(buf_writer, Compression::default());

        // Escreve cabeçalho
        writeln!(
            encoder,
            "-- ReplicOOP Backup\n-- Database: {}\n-- Environment: {}\n-- Date: {}\n",
            db_manager.get_database_name(),
            environment,
            timestamp.format("%Y-%m-%d %H:%M:%S")
        )?;

        writeln!(encoder, "SET FOREIGN_KEY_CHECKS=0;\n")?;

        // Backup de cada tabela
        for table in &tables {
            let create_stmt = db_manager.get_create_table(table)?;

            writeln!(encoder, "-- Table: {}", table)?;
            writeln!(encoder, "DROP TABLE IF EXISTS `{}`;", table)?;
            writeln!(encoder, "{};", create_stmt)?;
            writeln!(encoder)?;
        }

        writeln!(encoder, "SET FOREIGN_KEY_CHECKS=1;\n")?;

        encoder.finish()?;

        // Salva metadados
        let metadata = BackupMetadata {
            timestamp,
            database: db_manager.get_database_name().to_string(),
            environment: environment.to_string(),
            backup_file: filename.clone(),
            size_bytes: fs::metadata(&backup_file)?.len(),
            tables_count: tables.len(),
        };

        self.save_metadata(&metadata)?;

        self.logger
            .success(&format!("Backup criado com sucesso: {}", filename));

        Ok(backup_file)
    }

    fn save_metadata(&self, metadata: &BackupMetadata) -> Result<()> {
        let metadata_file = self
            .backup_path
            .join(format!("{}.json", metadata.backup_file));

        let json = serde_json::to_string_pretty(metadata)?;
        fs::write(metadata_file, json)?;

        Ok(())
    }

    pub fn list_backups(&self) -> Result<Vec<BackupMetadata>> {
        let mut backups = Vec::new();

        if !self.backup_path.exists() {
            return Ok(backups);
        }

        for entry in fs::read_dir(&self.backup_path)? {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Ok(content) = fs::read_to_string(&path) {
                    if let Ok(metadata) = serde_json::from_str::<BackupMetadata>(&content) {
                        backups.push(metadata);
                    }
                }
            }
        }

        // Ordena por data, mais recentes primeiro
        backups.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));

        Ok(backups)
    }

    pub fn get_backup_path(&self, filename: &str) -> PathBuf {
        self.backup_path.join(filename)
    }
}
