@echo off
setlocal

echo ========================================
echo Instalador do Leitor de Placa Veicular
echo ========================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python nao encontrado no PATH.
    echo Instale o Python e marque a opcao "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo [1/4] Criando ambiente virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo Erro ao criar ambiente virtual.
    pause
    exit /b 1
)

echo.
echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Erro ao ativar ambiente virtual.
    pause
    exit /b 1
)

echo.
echo [3/4] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [4/4] Instalando dependencias...
pip install playwright
if %errorlevel% neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Instalando navegadores do Playwright...
playwright install
if %errorlevel% neq 0 (
    echo Erro ao instalar navegadores do Playwright.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalacao concluida com sucesso!
echo ========================================
echo Para executar:
echo venv\Scripts\activate
echo python leitor_placa_veiculo.py ABC1234
echo.
pause