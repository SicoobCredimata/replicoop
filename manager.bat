@echo off
setlocal EnableDelayedExpansion

:: ========================================
:: ReplicOOP - Gerenciador Principal
:: Sistema de Replicação MySQL
:: Autor: Marcus Geraldino
:: ========================================

title ReplicOOP Manager

:: Cores para output
set "RED=[91m"
set "GREEN=[92m"  
set "YELLOW=[93m"
set "BLUE=[94m"
set "MAGENTA=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

:: Verifica se Python está instalado
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo %RED%❌ Python não encontrado! Instale o Python 3.7+ primeiro.%RESET%
    pause
    exit /b 1
)

:: Menu Principal
:main_menu
cls
echo %CYAN%
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    🚀 ReplicOOP Manager v1.0.0                   ║
echo ║              Sistema de Replicação de Estrutura MySQL           ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo %RESET%
echo.
echo %WHITE%Escolha uma opção:%RESET%
echo.
echo %GREEN% [1]%RESET% - 📦 Instalar/Configurar Ambiente (venv + dependências)
echo %GREEN% [2]%RESET% - 🚀 Executar ReplicOOP (menu interativo)
echo %GREEN% [0]%RESET% - ❌ Sair
echo.
set /p "choice=Digite sua escolha (0-2): "

if "%choice%"=="1" goto setup_environment
if "%choice%"=="2" goto run_replicoop
if "%choice%"=="0" goto exit_script

echo %RED%❌ Opção inválida! Tente novamente.%RESET%
timeout /t 2 >nul
goto main_menu

echo %RED%❌ Opção inválida! Tente novamente.%RESET%
timeout /t 2 >nul
goto main_menu

:: ========================================
:: INSTALAÇÃO/CONFIGURAÇÃO DO AMBIENTE
:: ========================================

:setup_environment
cls
echo %CYAN%� Configuração do Ambiente Virtual%RESET%
echo.

:: Verifica se já existe venv
if exist ".venv" (
    echo %YELLOW%⚠️  Ambiente virtual já existe!%RESET%
    echo.
    echo %WHITE%Escolha uma opção:%RESET%
    echo %GREEN% [1]%RESET% - Recriar ambiente (remove o atual)
    echo %GREEN% [2]%RESET% - Manter ambiente atual
    echo %GREEN% [0]%RESET% - Voltar ao menu principal
    echo.
    set /p "venv_choice=Digite sua escolha (0-2): "
    
    if "!venv_choice!"=="1" (
        echo %YELLOW%🗑️  Removendo ambiente virtual atual...%RESET%
        rmdir /s /q ".venv" 2>nul
        goto create_venv
    )
    if "!venv_choice!"=="2" goto install_deps
    if "!venv_choice!"=="0" goto main_menu
    
    echo %RED%❌ Opção inválida!%RESET%
    timeout /t 2 >nul
    goto setup_environment
)

:create_venv
echo %CYAN%� Criando ambiente virtual...%RESET%
python -m venv .venv

if !errorlevel! neq 0 (
    echo %RED%❌ Erro ao criar ambiente virtual!%RESET%
    echo %YELLOW%Verifique se o módulo venv está instalado:%RESET%
    echo %WHITE%python -m pip install virtualenv%RESET%
    pause
    goto main_menu
)

echo %GREEN%✅ Ambiente virtual criado com sucesso!%RESET%

:install_deps
echo.
echo %CYAN%📦 Instalando dependências...%RESET%

:: Ativa o ambiente virtual e instala dependências
call .venv\Scripts\activate.bat

if not exist requirements.txt (
    echo %RED%❌ Arquivo requirements.txt não encontrado!%RESET%
    pause
    goto main_menu
)

pip install -r requirements.txt

if !errorlevel! equ 0 (
    echo.
    echo %GREEN%✅ Dependências instaladas com sucesso!%RESET%
    
    :: Cria pastas necessárias
    if not exist backups mkdir backups
    if not exist logs mkdir logs
    if not exist docs mkdir docs
    
    echo %GREEN%✅ Estrutura de pastas criada%RESET%
    
    :: Verifica configuração
    if exist config.json (
        echo %GREEN%✅ Arquivo de configuração encontrado%RESET%
    ) else (
        echo %YELLOW%⚠️  Arquivo config.json não encontrado%RESET%
        echo %YELLOW%   Será necessário configurar antes do primeiro uso%RESET%
    )
    
    echo.
    echo %GREEN%🎉 Ambiente configurado com sucesso!%RESET%
    echo %YELLOW%💡 Use a opção [2] no menu para executar o ReplicOOP%RESET%
    
) else (
    echo %RED%❌ Erro ao instalar dependências%RESET%
    echo %YELLOW%Verifique sua conexão com internet e tente novamente%RESET%
)

call .venv\Scripts\deactivate.bat 2>nul
echo.
echo %WHITE%Pressione qualquer tecla para voltar ao menu...%RESET%
pause >nul
goto main_menu

:: ========================================
:: EXECUÇÃO DO REPLICOOP
:: ========================================

:run_replicoop
cls
echo %CYAN%🚀 Iniciando ReplicOOP%RESET%
echo.

:: Verifica se ambiente virtual existe
if not exist ".venv" (
    echo %RED%❌ Ambiente virtual não encontrado!%RESET%
    echo %YELLOW%Execute a opção [1] primeiro para configurar o ambiente%RESET%
    echo.
    echo %WHITE%Pressione qualquer tecla para voltar ao menu...%RESET%
    pause >nul
    goto main_menu
)

:: Verifica se main.py existe
if not exist "main.py" (
    echo %RED%❌ Arquivo main.py não encontrado!%RESET%
    pause
    goto main_menu
)

:: Ativa ambiente virtual e executa
call .venv\Scripts\activate.bat
python main.py
call .venv\Scripts\deactivate.bat 2>nul

echo.
echo %WHITE%Pressione qualquer tecla para voltar ao menu...%RESET%
pause >nul
goto main_menu

:: ========================================
:: SAÍDA
:: ========================================

:exit_script
cls
echo %CYAN%� Obrigado por usar o ReplicOOP!%RESET%
echo.
exit /b 0