@echo off
setlocal EnableDelayedExpansion

:: ========================================
:: ReplicOOP - Gerenciador Principal
:: Sistema de Replicacao MySQL
:: Autor: Marcus Geraldino
:: ========================================

title ReplicOOP Manager

:: Verifica se Python esta instalado
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ERRO: Python nao encontrado! Instale o Python 3.7+ primeiro.
    pause
    exit /b 1
)

:: Menu Principal
:main_menu
cls
echo ==============================================
echo         ReplicOOP Manager v1.0.0
echo     Sistema de Replicacao de Estrutura MySQL
echo ==============================================
echo.
echo Escolha uma opcao:
echo.
echo [1] - Instalar/Configurar Ambiente (venv + dependencias)
echo [2] - Executar ReplicOOP (menu interativo)
echo [0] - Sair
echo.
set /p escolha=Digite sua escolha (0-2): 

if "%escolha%"=="1" goto setup_environment
if "%escolha%"=="2" goto run_replicoop
if "%escolha%"=="0" goto exit_script

echo ERRO: Opcao invalida! Tente novamente.
timeout /t 2 >nul
goto main_menu

:: ========================================
:: INSTALACAO/CONFIGURACAO DO AMBIENTE
:: ========================================

:setup_environment
cls
echo Configuracao do Ambiente Virtual
echo.

:: Verifica se ja existe venv
if exist ".venv" (
    echo AVISO: Ambiente virtual ja existe!
    echo.
    echo Escolha uma opcao:
    echo [1] - Recriar ambiente (remove o atual)
    echo [2] - Manter ambiente atual
    echo [0] - Voltar ao menu principal
    echo.
    set /p "venv_choice=Digite sua escolha (0-2): "
    
    if "!venv_choice!"=="1" (
        echo Removendo ambiente virtual atual...
        rmdir /s /q ".venv" 2>nul
        goto create_venv
    )
    if "!venv_choice!"=="2" goto install_deps
    if "!venv_choice!"=="0" goto main_menu
    
    echo ERRO: Opcao invalida!
    timeout /t 2 >nul
    goto setup_environment
)

:create_venv
echo Criando ambiente virtual...
python -m venv .venv

if !errorlevel! neq 0 (
    echo ERRO: Erro ao criar ambiente virtual!
    echo Verifique se o modulo venv esta instalado:
    echo python -m pip install virtualenv
    pause
    goto main_menu
)

echo Ambiente virtual criado com sucesso!

:install_deps
echo.
echo Instalando dependencias...

:: Ativa o ambiente virtual e instala dependencias
call .venv\Scripts\activate.bat

if not exist requirements.txt (
    echo ERRO: Arquivo requirements.txt nao encontrado!
    pause
    goto main_menu
)

pip install -r requirements.txt

if !errorlevel! equ 0 (
    echo.
    echo Dependencias instaladas com sucesso!
    
    :: Cria pastas necessarias
    if not exist backups mkdir backups
    if not exist logs mkdir logs
    if not exist docs mkdir docs
    
    echo Estrutura de pastas criada
    
    :: Verifica configuracao
    if exist config.json (
        echo Arquivo de configuracao encontrado
    ) else (
        echo AVISO: Arquivo config.json nao encontrado
        echo        Sera necessario configurar antes do primeiro uso
    )
    
    echo.
    echo Ambiente configurado com sucesso!
    echo Dica: Use a opcao [2] no menu para executar o ReplicOOP
    
) else (
    echo ERRO: Erro ao instalar dependencias
    echo Verifique sua conexao com internet e tente novamente
)

call .venv\Scripts\deactivate.bat 2>nul
echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto main_menu

:: ========================================
:: EXECUCAO DO REPLICOOP
:: ========================================

:run_replicoop
cls
echo Iniciando ReplicOOP
echo.

:: Verifica se ambiente virtual existe
if not exist ".venv" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute a opcao [1] primeiro para configurar o ambiente
    echo.
    echo Pressione qualquer tecla para voltar ao menu...
    pause >nul
    goto main_menu
)

:: Verifica se main.py existe
if not exist "main.py" (
    echo ERRO: Arquivo main.py nao encontrado!
    pause
    goto main_menu
)

:: Ativa ambiente virtual e executa
call .venv\Scripts\activate.bat
python main.py
call .venv\Scripts\deactivate.bat 2>nul

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto main_menu

:: ========================================
:: SAIDA
:: ========================================

:exit_script
cls
echo Obrigado por usar o ReplicOOP!
echo.
exit /b 0