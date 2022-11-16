@echo off
call venv\Scripts\activate.bat
start "StockAPI" /min "stock_quality_API\run.bat"
start "PortfolioAPI" /min "portfolio_API\run.bat"
start "ClientInterface" /min "client\run.bat"

set /p=Press enter to exit

taskkill /FI "WindowTitle eq StockAPI*" /T /F
taskkill /FI "WindowTitle eq PortfolioAPI*" /T /F
taskkill /FI "WindowTitle eq ClientInterface*" /T /F
