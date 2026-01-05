use thiserror::Error;

#[derive(Error, Debug)]
pub enum ReplicoopError {
    #[error("Erro de banco de dados: {0}")]
    Database(#[from] mysql::Error),

    #[error("Erro de configuração: {0}")]
    Config(String),

    #[error("Erro de replicação: {0}")]
    Replication(String),

    #[error("Erro de backup: {0}")]
    Backup(String),

    #[error("Erro de restauração: {0}")]
    Restore(String),

    #[error("Erro de I/O: {0}")]
    Io(#[from] std::io::Error),

    #[error("Erro de JSON: {0}")]
    Json(#[from] serde_json::Error),

    #[error("Erro: {0}")]
    Other(String),
}

pub type Result<T> = std::result::Result<T, ReplicoopError>;
