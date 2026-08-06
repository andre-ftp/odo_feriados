import os
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def load_environment():
    """Carrega variáveis de ambiente de um arquivo .env, se existir."""
    env_file = Path(".env")
    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


load_environment()

def get_recipients():
    """
    Obtém a lista de destinatários.
    Atualmente retorna uma lista fixa, mas está preparado para buscar via API.
    """
    # A integração com uma API de destinatários será adicionada futuramente.
    
    # Lista reduzida inicial para teste
    return ["exemplo1@email.com", "exemplo2@email.com"]

def send_email(recipients):
    """
    Envia o e-mail para a lista de destinatários fornecida.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_password:
        print("Erro: Credenciais SMTP não configuradas nas variáveis de ambiente.")
        return

    subject = "Notificação Diária - Odo Feriados"
    body = "Este é um e-mail automático enviado diariamente."

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
        print(f"E-mail enviado com sucesso para: {', '.join(recipients)}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def main():
    recipients = get_recipients()
    if recipients:
        send_email(recipients)
    else:
        print("Nenhum destinatário encontrado.")

if __name__ == "__main__":
    main()
