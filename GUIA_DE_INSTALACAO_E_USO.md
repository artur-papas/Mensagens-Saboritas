# Guia de Instalação e Uso

## Instalação no Windows

### 1. Instale o Python

Site oficial:

- https://www.python.org/downloads/windows/

Instale o Python 3.11 ou superior e marque `Add Python to PATH`.

Verifique no PowerShell:

```powershell
py -3 --version
```

### 2. Instale o Node.js

Site oficial:

- https://nodejs.org/

Verifique:

```powershell
node --version
npm --version
```

### 3. Instale o Appium

Site oficial:

- https://appium.io/

```powershell
npm install -g appium
appium --version
```

### 4. Prepare o Android

- habilite a depuração USB
- conecte o aparelho ou use um emulador
- instale o WhatsApp Business

Se for usar `adb`, instale as platform tools:

- https://developer.android.com/tools/releases/platform-tools

Verifique:

```powershell
adb devices
```

### 5. Instale o projeto

Opção recomendada:

- dê duplo clique em [scripts/Instalar_Mensagens.bat](/C:/Users/artur/Mensagens_Saboritas/scripts/Instalar_Mensagens.bat)

Opção manual:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item configuracao.exemplo.json configuracao.json
```

## Execução

### Abrir o aplicativo

- dê duplo clique em [scripts/Mensagens.bat](/C:/Users/artur/Mensagens_Saboritas/scripts/Mensagens.bat)

Ou:

```powershell
.venv\Scripts\python.exe scripts\launcher.py
```

### Antes de usar

- deixe o aparelho desbloqueado
- abra o WhatsApp Business
- confirme que o contato de origem está visível na lista de conversas
- confirme que o Appium está rodando ou use `--manage-appium`

## Uso básico

### Coletar contatos

1. Abra a aba `Coletar Contatos`.
2. Defina o nome do arquivo de saída.
3. Revise a lista de contatos bloqueados.
4. Clique em `Iniciar`.

### Enviar mensagens

1. Abra a aba `Enviar Mensagens`.
2. Selecione o CSV de contatos.
3. Informe o contato de origem.
4. Escolha a quantidade por lote, máximo `5`.
5. Clique em `Iniciar`.
