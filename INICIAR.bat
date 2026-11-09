@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Escola de Musica - Group 8
echo.
echo  ==============================================
echo   Escola de Musica - preparando a demonstracao
echo  ==============================================
echo.

rem 1. Python instalado?
where python >nul 2>nul
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado neste computador.
    echo  Instale em python.org marcando "Add Python to PATH" e rode de novo.
    pause
    exit /b 1
)

rem 2. Arquivo de configuracao (.env). As senhas de demonstracao ja vem prontas.
if not exist .env copy .env.example .env >nul

rem 3. Bibliotecas (so na primeira vez demora; precisa de internet)
if not exist .venv (
    echo  Instalando as bibliotecas, aguarde...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERRO] Nao consegui instalar as bibliotecas. Confira a internet.
    pause
    exit /b 1
)

rem 4. Banco de dados do zero (pede a senha do root do MySQL)
echo.
echo  Preparando o banco. Digite a senha do root do MySQL quando pedir.
echo  (se o MySQL do computador nao tiver senha, so aperte Enter)
echo.
python ferramentas\preparar_banco.py
if errorlevel 1 (
    echo.
    echo  [ERRO] O banco nao foi preparado. Veja a mensagem acima.
    pause
    exit /b 1
)

rem 5. Sobe a aplicacao e abre o navegador
echo.
echo  Abrindo a aplicacao. NAO FECHE ESTA JANELA durante a apresentacao.
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"
python app\app.py
pause
