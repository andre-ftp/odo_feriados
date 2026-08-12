# Odo Feriados - Email Notification System

Sistema automático de notificação por email usando **GitHub Actions** e **git secrets**.

## 🚀 Quick Start

### 1. Configurar GitHub Secrets

No repositório GitHub, vá a **Settings → Secrets and variables → Actions** e adicione:

```
SMTP_SERVER      = smtp.ftpweb.dev
SMTP_PORT        = 587
SMTP_USER        = odo@ftpweb.dev
SMTP_PASSWORD    = (sua senha segura)
RECIPIENTS_API_URL = (opcional)
```

### 2. Desenvolvimento Local

```bash
# Criar virtual environment
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` no Windows

# Instalar dependências
pip install -r requirements.txt

# Criar .env local (NÃO commitar!)
cp .env.example .env
# Preencher com valores reais

# Testar script
python main.py
```

### 3. Executar no GitHub Actions

- **Automático**: Corre diariamente às 09:00 UTC
- **Manual**: Aceda a **Actions → Send Email Notification → Run workflow**

## 🔒 Git Secrets (Opcional)

Para evitar commitar credenciais acidentalmente, instale [git-secrets](https://github.com/awslabs/git-secrets):

```bash
# Instalar (macOS/Linux)
brew install git-secrets

# Ou Windows: https://github.com/awslabs/git-secrets/releases

# Configurar para o repositório
git secrets --install
git secrets --register-aws  # Deteta padrões de credenciais

# Testar
git secrets --scan
```

## 📁 Estrutura

```
odo_feriados/
├── main.py                 # Script principal
├── json/
│   ├── feriados_municipais_2026.json
│   └── feriados_municipais_2027.json
├── requirements.txt        # Dependências Python
├── .env.example           # Template de configuração
├── .github/
│   └── workflows/
│       └── send-email.yml # GitHub Actions workflow
└── README.md              # Esta documentação
```

## 📝 Variáveis de Ambiente

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `SMTP_SERVER` | string | Servidor SMTP (ex: smtp.ftpweb.dev) |
| `SMTP_PORT` | int | Porta SMTP (ex: 587) |
| `SMTP_USER` | string | Utilizador SMTP |
| `SMTP_PASSWORD` | string | Senha SMTP |
| `RECIPIENTS_API_URL` | string | (Opcional) URL para obter destinatários |

## 🧪 Testes Locais

```bash
# Definir variáveis e testar
export SMTP_SERVER=smtp.ftpweb.dev
export SMTP_PORT=587
export SMTP_USER=odo@ftpweb.dev
export SMTP_PASSWORD=sua_senha
python main.py
```

## 🔄 Agendamento

Atualmente configurado para rodar diariamente às 09:00 UTC.

Para alterar, edite `.github/workflows/send-email.yml` e mude o `cron`:

```yaml
- cron: '0 9 * * *'  # Formato: minuto hora dia mês dia_semana
```

Referência: https://crontab.guru

## 📚 Recursos

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Git Secrets](https://github.com/awslabs/git-secrets)
- [Cron Expression Generator](https://crontab.guru)

---

**Nota**: Nunca commita credenciais! Use `.env.example` como template e configure secrets no GitHub.
