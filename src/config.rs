use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::error::{ReplicoopError, Result};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub host: String,
    pub port: u16,
    pub username: String,
    pub password: String,
    pub dbname: String,
    #[serde(default = "default_charset")]
    pub charset: String,
}

fn default_charset() -> String {
    "utf8mb4".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(flatten)]
    pub environments: HashMap<String, DatabaseConfig>,
    #[serde(default)]
    pub maintain: Vec<String>,
}

impl Config {
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let content = fs::read_to_string(path)
            .map_err(|e| ReplicoopError::Config(format!("Erro ao ler arquivo de configuração: {}", e)))?;
        
        let config: Config = serde_json::from_str(&content)?;
        Ok(config)
    }

    pub fn get_database_config(&self, environment: &str) -> Result<&DatabaseConfig> {
        self.environments
            .get(environment)
            .ok_or_else(|| ReplicoopError::Config(format!("Ambiente '{}' não encontrado", environment)))
    }

    pub fn get_available_environments(&self) -> Vec<String> {
        let mut envs: Vec<String> = self.environments.keys().cloned().collect();
        envs.sort();
        envs
    }

    pub fn get_maintain_tables(&self) -> &[String] {
        &self.maintain
    }

    pub fn get_backup_path(&self) -> String {
        "backups".to_string()
    }

    pub fn get_logs_path(&self) -> String {
        "logs".to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_parsing() {
        let json = r#"{
            "production": {
                "host": "localhost",
                "port": 3306,
                "username": "user",
                "password": "pass",
                "dbname": "db"
            },
            "maintain": ["table1", "table2"]
        }"#;

        let config: Config = serde_json::from_str(json).unwrap();
        assert_eq!(config.maintain.len(), 2);
        assert!(config.environments.contains_key("production"));
    }
}
