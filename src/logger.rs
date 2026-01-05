use chrono::Local;
use colored::*;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;

pub struct Logger {
    log_file: Option<PathBuf>,
}

impl Logger {
    pub fn new(logs_path: &str) -> Self {
        // Cria o diretório de logs se não existir
        fs::create_dir_all(logs_path).ok();

        let log_file = PathBuf::from(logs_path).join(format!(
            "replicoop_{}.log",
            Local::now().format("%Y-%m-%d")
        ));

        Logger {
            log_file: Some(log_file),
        }
    }

    fn write_to_file(&self, level: &str, message: &str) {
        if let Some(ref log_file) = self.log_file {
            if let Ok(mut file) = OpenOptions::new()
                .create(true)
                .append(true)
                .open(log_file)
            {
                let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S");
                writeln!(file, "[{}] [{}] {}", timestamp, level, message).ok();
            }
        }
    }

    pub fn info(&self, message: &str) {
        println!("{} {}", "ℹ️ ".blue(), message);
        self.write_to_file("INFO", message);
    }

    pub fn success(&self, message: &str) {
        println!("{} {}", "✅".green(), message);
        self.write_to_file("SUCCESS", message);
    }

    pub fn warning(&self, message: &str) {
        println!("{} {}", "⚠️ ".yellow(), message);
        self.write_to_file("WARNING", message);
    }

    pub fn error(&self, message: &str) {
        println!("{} {}", "❌".red(), message);
        self.write_to_file("ERROR", message);
    }

    pub fn debug(&self, message: &str) {
        println!("{} {}", "🔍".cyan(), message);
        self.write_to_file("DEBUG", message);
    }

    pub fn header(&self, message: &str) {
        let line = "=".repeat(70);
        println!("\n{}", line.bright_blue());
        println!("{}", message.bright_white().bold());
        println!("{}", line.bright_blue());
    }

    pub fn subheader(&self, message: &str) {
        let line = "-".repeat(50);
        println!("\n{}", line.bright_cyan());
        println!("{}", message.bright_white());
        println!("{}", line.bright_cyan());
    }
}
