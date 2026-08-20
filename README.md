# Odo Feriados — Sistema de Notificação por Email

Sistema automático que verifica os feriados municipais associados às estâncias aduaneiras e envia uma notificação por email através do GitHub Actions.

## Configuração no GitHub

No repositório GitHub, aceda a **Settings → Secrets and variables → Actions** e configure:

| Secret | Tipo | Descrição |
|---|---|---|
| `SMTP_SERVER` | string | Nome ou endereço do servidor SMTP. |
| `SMTP_PORT` | inteiro | Porta SMTP. A porta `465` usa SSL; as restantes usam SMTP com STARTTLS. |
| `SMTP_USER` | string | Utilizador/endereço de autenticação SMTP. |
| `SMTP_PASSWORD` | string | Palavra-passe SMTP. |
| `RECIPIENTS_API_URL` | string | Opcional. URL da API que devolve os destinatários. |

Se `RECIPIENTS_API_URL` não estiver configurado, ou se a consulta à API falhar, o programa usa a lista de destinatários definida no código. Se a API responder com uma lista vazia, não é usado esse fallback e a execução termina sem enviar email.

## Desenvolvimento local

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar no Linux/macOS
source venv/bin/activate

# Ativar no Windows PowerShell
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Criar a configuração local
cp .env.example .env       # Linux/macOS
Copy-Item .env.example .env  # Windows PowerShell

# Preencher os valores reais no ficheiro .env e executar
python main.py
```

O ficheiro `.env` não deve ser commitado.

## Execução no GitHub Actions

O workflow está em [.github/workflows/send-email.yml](.github/workflows/send-email.yml) e pode ser executado de duas formas:

- **Agendada:** todos os dias às **10:07**, no fuso horário `Europe/Lisbon`.
- **Manual:** em **Actions → Send Email Notification → Run workflow**.

As execuções agendadas usam o commit mais recente da branch predefinida do repositório e podem sofrer algum atraso devido à carga do GitHub Actions.

## Regras de notificação

O programa envia emails apenas quando a data atual é o último dia útil anterior a um feriado municipal.

Para determinar o dia útil anterior:

- sábados e domingos são ignorados;
- feriados nacionais são ignorados;
- o cálculo pode atravessar a mudança de ano.

Quando existem várias estâncias associadas ao mesmo feriado e à mesma data, são incluídas no mesmo email. Feriados diferentes ou com datas diferentes originam emails separados.

Se não houver nenhum feriado elegível no dia, o programa termina normalmente sem enviar email.

## Dados de feriados

Atualmente estão disponíveis dados para 2026 e 2027:

```text
json/
├── feriados_municipais_2026.json
├── feriados_municipais_2027.json
├── feriados_nacionais_2026.json
└── feriados_nacionais_2027.json
```

Para que um novo ano seja suportado, é necessário adicionar os respetivos ficheiros de feriados municipais e nacionais com os nomes esperados pelo programa.

## Estrutura do projeto

```text
odo_feriados/
├── main.py
├── json/
├── requirements.txt
├── .env.example
├── .github/
│   └── workflows/
│       └── send-email.yml
└── README.md
```

## Variáveis locais de ambiente

Exemplo de configuração no `.env`:

```dotenv
SMTP_SERVER=smtp.exemplo.pt
SMTP_PORT=465
SMTP_USER=utilizador@exemplo.pt
SMTP_PASSWORD=coloque_a_password

# Opcional
# RECIPIENTS_API_URL=https://api.exemplo.pt/v1/emails
```

## Segurança

- Nunca commite credenciais SMTP.
- Use GitHub Secrets nas execuções do GitHub Actions.
- Mantenha a lista de destinatários e a API devidamente controladas.
- O `RECIPIENTS_API_URL` deve usar HTTPS quando estiver disponível.

## Recursos

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Sintaxe de workflows do GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Git Secrets](https://github.com/awslabs/git-secrets)
