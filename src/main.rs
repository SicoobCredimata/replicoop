mod backup;
mod config;
mod database;
mod error;
mod logger;
mod replication;

use clap::{Parser, Subcommand};
use dialoguer::{theme::ColorfulTheme, Confirm, Select};
use std::sync::Arc;

use config::Config;
use error::Result;
use logger::Logger;
use replication::ReplicationManager;

#[derive(Parser)]
#[command(name = "ReplicOOP")]
#[command(author = "Marcus Geraldino")]
#[command(version = "1.0.0")]
#[command(about = "Sistema Profissional de Replicação MySQL em Rust", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    /// Caminho para o arquivo de configuração
    #[arg(short, long, default_value = "config.json")]
    config: String,
}

#[derive(Subcommand)]
enum Commands {
    /// Replica estruturas e/ou dados entre ambientes
    Replicate {
        /// Ambiente de origem
        #[arg(short, long)]
        source: Option<String>,

        /// Ambiente de destino
        #[arg(short, long)]
        target: Option<String>,

        /// Criar backup antes da replicação
        #[arg(short, long, default_value = "true")]
        backup: bool,

        /// Replicar dados das tabelas maintain
        #[arg(short, long)]
        data: bool,
    },

    /// Testa conexões com todos os ambientes configurados
    TestConnections,

    /// Lista todos os backups disponíveis
    ListBackups,

    /// Cria um backup manual
    CreateBackup {
        /// Ambiente para backup
        #[arg(short, long)]
        environment: Option<String>,
    },

    /// Modo interativo com menu
    Interactive,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    let logger = Arc::new(Logger::new("logs"));

    logger.header("🚀 ReplicOOP - Sistema de Replicação MySQL v1.0.0");
    logger.info("Sistema Profissional de Replicação em Rust");

    match cli.command {
        Some(Commands::Replicate {
            source,
            target,
            backup,
            data,
        }) => {
            replicate_command(&cli.config, source, target, backup, data, &logger)?;
        }
        Some(Commands::TestConnections) => {
            test_connections_command(&cli.config, &logger)?;
        }
        Some(Commands::ListBackups) => {
            list_backups_command(&cli.config, &logger)?;
        }
        Some(Commands::CreateBackup { environment }) => {
            create_backup_command(&cli.config, environment, &logger)?;
        }
        Some(Commands::Interactive) | None => {
            interactive_mode(&cli.config, &logger)?;
        }
    }

    Ok(())
}

fn interactive_mode(config_path: &str, logger: &Arc<Logger>) -> Result<()> {
    let config = Config::from_file(config_path)?;

    loop {
        logger.header("📋 MENU PRINCIPAL");

        let options = vec![
            "🔄 Replicar Estruturas (com opções)",
            "🔄 Replicar Tudo (estrutura + dados maintain)",
            "🔌 Testar Conexões",
            "💾 Criar Backup Manual",
            "📦 Listar Backups",
            "❌ Sair",
        ];

        let selection = Select::with_theme(&ColorfulTheme::default())
            .with_prompt("Escolha uma opção")
            .items(&options)
            .default(0)
            .interact()
            .unwrap();

        match selection {
            0 => replicate_interactive(&config, false, logger)?,
            1 => replicate_interactive(&config, true, logger)?,
            2 => test_connections_command(config_path, logger)?,
            3 => create_backup_interactive(&config, logger)?,
            4 => list_backups_command(config_path, logger)?,
            5 => {
                logger.info("👋 Obrigado por usar o ReplicOOP!");
                break;
            }
            _ => {}
        }

        println!("\nPressione Enter para continuar...");
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).ok();
    }

    Ok(())
}

fn replicate_interactive(
    config: &Config,
    replicate_data: bool,
    logger: &Arc<Logger>,
) -> Result<()> {
    let environments = config.get_available_environments();

    let source_idx = Select::with_theme(&ColorfulTheme::default())
        .with_prompt("Selecione o ambiente de ORIGEM")
        .items(&environments)
        .default(0)
        .interact()
        .unwrap();

    let target_idx = Select::with_theme(&ColorfulTheme::default())
        .with_prompt("Selecione o ambiente de DESTINO")
        .items(&environments)
        .default(0)
        .interact()
        .unwrap();

    let source_env = &environments[source_idx];
    let target_env = &environments[target_idx];

    let create_backup = Confirm::with_theme(&ColorfulTheme::default())
        .with_prompt("Criar backup antes da replicação?")
        .default(true)
        .interact()
        .unwrap();

    logger.subheader("📋 RESUMO DA OPERAÇÃO");
    println!("   Origem: {}", source_env);
    println!("   Destino: {}", target_env);
    println!("   Backup: {}", if create_backup { "Sim" } else { "Não" });
    println!(
        "   Dados: {}",
        if replicate_data {
            "Tabelas maintain"
        } else {
            "Não"
        }
    );

    let confirm = Confirm::with_theme(&ColorfulTheme::default())
        .with_prompt("Confirma a replicação?")
        .default(false)
        .interact()
        .unwrap();

    if !confirm {
        logger.warning("❌ Operação cancelada");
        return Ok(());
    }

    let mut replication_manager = ReplicationManager::new(config.clone(), Arc::clone(logger))?;
    replication_manager.setup_databases(source_env, target_env)?;

    let result = replication_manager.execute_replication(None, create_backup, replicate_data)?;

    show_replication_results(&result, logger);

    Ok(())
}

fn replicate_command(
    config_path: &str,
    source: Option<String>,
    target: Option<String>,
    create_backup: bool,
    replicate_data: bool,
    logger: &Arc<Logger>,
) -> Result<()> {
    let config = Config::from_file(config_path)?;

    let source_env = source.unwrap_or_else(|| "sandbox".to_string());
    let target_env = target.unwrap_or_else(|| "production".to_string());

    let mut replication_manager = ReplicationManager::new(config, Arc::clone(logger))?;
    replication_manager.setup_databases(&source_env, &target_env)?;

    let result = replication_manager.execute_replication(None, create_backup, replicate_data)?;

    show_replication_results(&result, logger);

    Ok(())
}

fn test_connections_command(config_path: &str, logger: &Arc<Logger>) -> Result<()> {
    logger.header("🔌 TESTE DE CONEXÕES");

    let config = Config::from_file(config_path)?;
    let replication_manager = ReplicationManager::new(config, Arc::clone(logger))?;

    let results = replication_manager.test_connections()?;

    logger.subheader("Testando conexões...");

    for (env, success) in &results {
        if *success {
            logger.success(&format!("{}: Conexão OK", env));
        } else {
            logger.error(&format!("{}: Falha na conexão", env));
        }
    }

    let success_count = results.iter().filter(|(_, s)| *s).count();
    logger.info(&format!(
        "\n📊 RESULTADO: {}/{} conexões bem-sucedidas",
        success_count,
        results.len()
    ));

    Ok(())
}

fn list_backups_command(config_path: &str, logger: &Arc<Logger>) -> Result<()> {
    logger.header("📦 BACKUPS DISPONÍVEIS");

    let config = Config::from_file(config_path)?;
    let backup_manager = backup::BackupManager::new(&config.get_backup_path(), Arc::clone(logger))?;

    let backups = backup_manager.list_backups()?;

    if backups.is_empty() {
        logger.info("📭 Nenhum backup encontrado");
        return Ok(());
    }

    logger.info(&format!("\n📋 {} backups encontrados:\n", backups.len()));

    for (i, backup) in backups.iter().enumerate() {
        println!(
            "[{:2}] 📁 {}\n     🗄️  Banco: {}\n     🏷️  Ambiente: {}\n     📅 Data: {}\n     📏 Tamanho: {:.1} MB\n",
            i + 1,
            backup.backup_file,
            backup.database,
            backup.environment,
            backup.timestamp.format("%d/%m/%Y %H:%M:%S"),
            backup.size_bytes as f64 / 1024.0 / 1024.0
        );
    }

    Ok(())
}

fn create_backup_command(
    config_path: &str,
    environment: Option<String>,
    logger: &Arc<Logger>,
) -> Result<()> {
    logger.header("💾 CRIAR BACKUP MANUAL");

    let config = Config::from_file(config_path)?;

    let env = if let Some(env) = environment {
        env
    } else {
        let environments = config.get_available_environments();
        let idx = Select::with_theme(&ColorfulTheme::default())
            .with_prompt("Selecione o ambiente para backup")
            .items(&environments)
            .default(0)
            .interact()
            .unwrap();
        environments[idx].clone()
    };

    let db_config = config.get_database_config(&env)?.clone();
    let db_manager = database::DatabaseManager::new(db_config, Arc::clone(logger))?;
    let backup_manager = backup::BackupManager::new(&config.get_backup_path(), Arc::clone(logger))?;

    let backup_path = backup_manager.create_backup(&db_manager, &env)?;

    logger.success(&format!(
        "✅ Backup criado com sucesso: {}",
        backup_path.display()
    ));

    Ok(())
}

fn create_backup_interactive(config: &Config, logger: &Arc<Logger>) -> Result<()> {
    let environments = config.get_available_environments();

    let idx = Select::with_theme(&ColorfulTheme::default())
        .with_prompt("Selecione o ambiente para backup")
        .items(&environments)
        .default(0)
        .interact()
        .unwrap();

    let env = &environments[idx];

    let db_config = config.get_database_config(env)?.clone();
    let db_manager = database::DatabaseManager::new(db_config, Arc::clone(logger))?;
    let backup_manager = backup::BackupManager::new(&config.get_backup_path(), Arc::clone(logger))?;

    let backup_path = backup_manager.create_backup(&db_manager, env)?;

    logger.success(&format!(
        "✅ Backup criado com sucesso: {}",
        backup_path.display()
    ));

    Ok(())
}

fn show_replication_results(result: &replication::ReplicationResult, logger: &Arc<Logger>) {
    logger.header("📊 RELATÓRIO DE REPLICAÇÃO");

    if result.success {
        logger.success("✅ SUCESSO");
    } else {
        logger.error("❌ FALHAS ENCONTRADAS");
    }

    println!("📊 Tabelas processadas: {}", result.tables_replicated);

    if !result.data_replicated_tables.is_empty() {
        println!(
            "🔄 Tabelas com dados replicados: {}",
            result.data_replicated_tables.len()
        );
    }

    println!("⏱️  Tempo de execução: {:.2}s", result.execution_time);

    if let Some(ref backup) = result.backup_created {
        println!("💾 Backup criado: {}", backup);
    }

    if !result.replicated_tables.is_empty() {
        println!(
            "\n✅ Tabelas Replicadas ({}):",
            result.replicated_tables.len()
        );
        for (i, table) in result.replicated_tables.iter().enumerate() {
            println!("   {:2}. {}", i + 1, table);
        }
    }

    if !result.failed_tables.is_empty() {
        println!("\n❌ Tabelas com Falha ({}):", result.failed_tables.len());
        for (i, failed) in result.failed_tables.iter().enumerate() {
            println!("   {:2}. {}: {}", i + 1, failed.table, failed.error);
        }
    }
}
