use mysql::prelude::*;
use mysql::{OptsBuilder, Pool, PooledConn};
use std::sync::Arc;

use crate::config::DatabaseConfig;
use crate::error::{ReplicoopError, Result};
use crate::logger::Logger;

pub struct DatabaseManager {
    pool: Pool,
    config: DatabaseConfig,
    logger: Arc<Logger>,
}

impl DatabaseManager {
    pub fn new(config: DatabaseConfig, logger: Arc<Logger>) -> Result<Self> {
        let opts = OptsBuilder::new()
            .ip_or_hostname(Some(&config.host))
            .tcp_port(config.port)
            .user(Some(&config.username))
            .pass(Some(&config.password))
            .db_name(Some(&config.dbname));

        let pool = Pool::new(opts)?;

        Ok(DatabaseManager {
            pool,
            config,
            logger,
        })
    }

    /// Valida nome de tabela para prevenir SQL injection
    /// Apenas permite caracteres alfanuméricos, underscore e hífen
    fn validate_table_name(table: &str) -> Result<()> {
        if table.is_empty() {
            return Err(ReplicoopError::Config(
                "Nome de tabela não pode ser vazio".to_string(),
            ));
        }

        // Verifica se contém apenas caracteres seguros
        if !table
            .chars()
            .all(|c| c.is_alphanumeric() || c == '_' || c == '-')
        {
            return Err(ReplicoopError::Config(format!(
                "Nome de tabela inválido: '{}'. Apenas alfanuméricos, _ e - são permitidos",
                table
            )));
        }

        // Verifica tamanho razoável (MySQL limit)
        if table.len() > 64 {
            return Err(ReplicoopError::Config(
                "Nome de tabela muito longo (max 64 caracteres)".to_string(),
            ));
        }

        Ok(())
    }

    /// Escapa nome de tabela com backticks após validação
    fn escape_table_name(table: &str) -> Result<String> {
        Self::validate_table_name(table)?;
        Ok(format!("`{}`", table))
    }

    pub fn test_connection(&self) -> Result<bool> {
        match self.pool.get_conn() {
            Ok(mut conn) => {
                let result: Result<Vec<String>> = conn
                    .query("SELECT 'connection_test'")
                    .map_err(ReplicoopError::from);
                result.map(|_| true)
            }
            Err(e) => Err(ReplicoopError::Database(e)),
        }
    }

    pub fn get_conn(&self) -> Result<PooledConn> {
        self.pool.get_conn().map_err(ReplicoopError::from)
    }

    pub fn get_tables(&self) -> Result<Vec<String>> {
        let mut conn = self.get_conn()?;
        let tables: Vec<String> = conn.query("SHOW TABLES").map_err(ReplicoopError::from)?;
        Ok(tables)
    }

    pub fn get_create_table(&self, table: &str) -> Result<String> {
        let mut conn = self.get_conn()?;
        let escaped_table = Self::escape_table_name(table)?;
        let query = format!("SHOW CREATE TABLE {}", escaped_table);

        let result: Vec<(String, String)> = conn.query(query).map_err(ReplicoopError::from)?;

        result
            .first()
            .map(|(_, create_stmt)| create_stmt.clone())
            .ok_or_else(|| ReplicoopError::Replication("Erro ao obter CREATE TABLE".to_string()))
    }

    pub fn execute(&self, query: &str) -> Result<()> {
        let mut conn = self.get_conn()?;
        conn.query_drop(query).map_err(ReplicoopError::from)
    }

    pub fn execute_multiple(&self, queries: Vec<String>) -> Result<()> {
        let mut conn = self.get_conn()?;

        for query in queries {
            conn.query_drop(query).map_err(ReplicoopError::from)?;
        }

        Ok(())
    }

    pub fn drop_table(&self, table: &str) -> Result<()> {
        let escaped_table = Self::escape_table_name(table)?;
        let query = format!("DROP TABLE IF EXISTS {}", escaped_table);
        self.execute(&query)
    }

    pub fn get_foreign_keys(&self, table: &str) -> Result<Vec<ForeignKey>> {
        Self::validate_table_name(table)?;
        let mut conn = self.get_conn()?;

        let query = "SELECT 
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
             FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
             WHERE TABLE_SCHEMA = ?
             AND TABLE_NAME = ?
             AND REFERENCED_TABLE_NAME IS NOT NULL";

        let results: Vec<(String, String, String, String)> = conn
            .exec(query, (&self.config.dbname, table))
            .map_err(ReplicoopError::from)?;

        Ok(results
            .into_iter()
            .map(
                |(constraint_name, column_name, ref_table, ref_column)| ForeignKey {
                    constraint_name,
                    column_name,
                    referenced_table: ref_table,
                    referenced_column: ref_column,
                },
            )
            .collect())
    }

    pub fn get_table_row_count(&self, table: &str) -> Result<u64> {
        let escaped_table = Self::escape_table_name(table)?;
        let mut conn = self.get_conn()?;
        let query = format!("SELECT COUNT(*) as count FROM {}", escaped_table);

        let result: Option<u64> = conn.query_first(query).map_err(ReplicoopError::from)?;

        Ok(result.unwrap_or(0))
    }

    pub fn copy_table_data(&self, source_conn: &mut PooledConn, table: &str) -> Result<u64> {
        let escaped_table = Self::escape_table_name(table)?;
        let query = format!("SELECT * FROM {}", escaped_table);

        let mut source_rows: Vec<mysql::Row> =
            source_conn.query(query).map_err(ReplicoopError::from)?;

        if source_rows.is_empty() {
            return Ok(0);
        }

        let column_count = source_rows[0].len();
        let mut target_conn = self.get_conn()?;

        let placeholders = (0..column_count)
            .map(|_| "?")
            .collect::<Vec<_>>()
            .join(", ");

        let insert_query = format!("INSERT INTO {} VALUES ({})", escaped_table, placeholders);

        let mut inserted = 0u64;

        for row in source_rows.drain(..) {
            let values: Vec<mysql::Value> = (0..column_count)
                .map(|i| row.get(i).unwrap_or(mysql::Value::NULL))
                .collect();

            target_conn
                .exec_drop(&insert_query, values)
                .map_err(ReplicoopError::from)?;

            inserted += 1;
        }

        Ok(inserted)
    }

    pub fn get_database_name(&self) -> &str {
        &self.config.dbname
    }
}

#[derive(Debug, Clone)]
pub struct ForeignKey {
    pub constraint_name: String,
    pub column_name: String,
    pub referenced_table: String,
    pub referenced_column: String,
}
