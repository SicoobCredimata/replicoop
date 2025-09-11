"""
Utilitários diversos para o sistema ReplicOOP
"""
import re
import hashlib
from typing import Dict, Any, List
from datetime import datetime


class DatabaseUtils:
    """Utilitários para operações com banco de dados"""
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitiza nome de tabela para evitar SQL injection
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            str: Nome sanitizado
        """
        # Remove caracteres não alfanuméricos (exceto underscore)
        sanitized = re.sub(r'[^\w]', '', table_name)
        return sanitized
    
    @staticmethod
    def generate_backup_checksum(filepath: str) -> str:
        """
        Gera checksum MD5 para arquivo de backup
        
        Args:
            filepath (str): Caminho do arquivo
            
        Returns:
            str: Hash MD5
        """
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Formata tamanho de arquivo em formato legível
        
        Args:
            size_bytes (int): Tamanho em bytes
            
        Returns:
            str: Tamanho formatado
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def parse_mysql_data_type(data_type: str) -> Dict[str, Any]:
        """
        Analisa tipo de dado MySQL e extrai informações
        
        Args:
            data_type (str): Tipo de dado (ex: 'varchar(255)', 'int(11)')
            
        Returns:
            Dict[str, Any]: Informações do tipo de dado
        """
        # Padrão para capturar tipo, tamanho e atributos
        pattern = r'(\w+)(?:\(([^)]+)\))?(?:\s+(.+))?'
        match = re.match(pattern, data_type.lower())
        
        if not match:
            return {'type': data_type, 'size': None, 'attributes': []}
        
        base_type = match.group(1)
        size_info = match.group(2)
        attributes = match.group(3)
        
        result = {
            'type': base_type,
            'size': None,
            'precision': None,
            'scale': None,
            'attributes': []
        }
        
        # Processa informações de tamanho
        if size_info:
            if ',' in size_info:
                # Tipo com precisão e escala (ex: decimal(10,2))
                parts = size_info.split(',')
                result['precision'] = int(parts[0].strip()) if parts[0].strip().isdigit() else None
                result['scale'] = int(parts[1].strip()) if parts[1].strip().isdigit() else None
            else:
                # Tipo com tamanho simples (ex: varchar(255))
                result['size'] = int(size_info) if size_info.isdigit() else size_info
        
        # Processa atributos
        if attributes:
            result['attributes'] = [attr.strip() for attr in attributes.split()]
        
        return result


class ReportUtils:
    """Utilitários para geração de relatórios"""
    
    @staticmethod
    def generate_execution_summary(start_time: datetime, end_time: datetime,
                                 success_count: int, total_count: int) -> Dict[str, Any]:
        """
        Gera resumo de execução
        
        Args:
            start_time (datetime): Hora de início
            end_time (datetime): Hora de fim
            success_count (int): Número de sucessos
            total_count (int): Total de operações
            
        Returns:
            Dict[str, Any]: Resumo da execução
        """
        duration = end_time - start_time
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        return {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration),
            'total_operations': total_count,
            'successful_operations': success_count,
            'failed_operations': total_count - success_count,
            'success_rate': round(success_rate, 2)
        }
    
    @staticmethod
    def format_table_list(tables: List[str], max_per_line: int = 5) -> str:
        """
        Formata lista de tabelas em múltiplas linhas
        
        Args:
            tables (List[str]): Lista de tabelas
            max_per_line (int): Máximo de tabelas por linha
            
        Returns:
            str: Lista formatada
        """
        if not tables:
            return "Nenhuma tabela"
        
        lines = []
        for i in range(0, len(tables), max_per_line):
            chunk = tables[i:i + max_per_line]
            lines.append(", ".join(chunk))
        
        return "\n".join(f"  {line}" for line in lines)


class ValidationUtils:
    """Utilitários para validação"""
    
    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """
        Valida nome de tabela MySQL
        
        Args:
            table_name (str): Nome da tabela
            
        Returns:
            bool: True se válido
        """
        # Nome da tabela deve ter 1-64 caracteres
        if not table_name or len(table_name) > 64:
            return False
        
        # Deve começar com letra ou underscore
        if not re.match(r'^[a-zA-Z_]', table_name):
            return False
        
        # Pode conter apenas letras, números, underscore e $
        if not re.match(r'^[a-zA-Z0-9_$]+$', table_name):
            return False
        
        return True
    
    @staticmethod
    def validate_database_name(db_name: str) -> bool:
        """
        Valida nome de banco de dados MySQL
        
        Args:
            db_name (str): Nome do banco
            
        Returns:
            bool: True se válido
        """
        # Nome do banco deve ter 1-64 caracteres
        if not db_name or len(db_name) > 64:
            return False
        
        # Não pode conter caracteres especiais problemáticos
        invalid_chars = ['/', '\\', '?', '*', ':', '"', '<', '>', '|']
        if any(char in db_name for char in invalid_chars):
            return False
        
        return True
    
    @staticmethod
    def validate_connection_config(config: Dict[str, Any]) -> List[str]:
        """
        Valida configuração de conexão
        
        Args:
            config (Dict[str, Any]): Configuração de conexão
            
        Returns:
            List[str]: Lista de erros encontrados
        """
        errors = []
        required_fields = ['host', 'port', 'username', 'password', 'dbname']
        
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Campo obrigatório ausente ou vazio: {field}")
        
        # Valida porta
        if 'port' in config:
            try:
                port = int(config['port'])
                if port < 1 or port > 65535:
                    errors.append("Porta deve estar entre 1 e 65535")
            except (ValueError, TypeError):
                errors.append("Porta deve ser um número válido")
        
        # Valida nome do banco
        if 'dbname' in config and config['dbname']:
            if not ValidationUtils.validate_database_name(config['dbname']):
                errors.append("Nome do banco de dados inválido")
        
        return errors