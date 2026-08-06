import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carrega variáveis de ambiente do ficheiro .env (opcional, para desenvolvimento)
# No GitHub Actions, as variáveis vêm de secrets
load_dotenv()

def get_recipients():
    """
    Obtém a lista de destinatários.
    Atualmente retorna uma lista fixa, preparada para API no futuro.
    """
    api_url = os.getenv("RECIPIENTS_API_URL")
    if api_url:
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return response.json().get("emails", [])
        except Exception as e:
            print(f"Erro ao procurar destinatários na API: {e}")
    
    # Lista inicial para testes
    return ["andre.rodrigues@ftpporto.com"]

def send_email(recipients):
    """
    Envia o e-mail para a lista de destinatários.
    As credenciais SMTP vêm de variáveis de ambiente (secrets no GitHub Actions).
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port_str = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_server or not smtp_user or not smtp_password:
        print("Erro: Credenciais SMTP não configuradas.")
        print("Configure SMTP_SERVER, SMTP_USER e SMTP_PASSWORD como variáveis de ambiente.")
        return False
    
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"Erro: SMTP_PORT deve ser um número. Recebido: {smtp_port_str}")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = "Notificação Odo Feriados"
    
    body = "Este é um e-mail automático enviado pelo sistema Odo Feriados."
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())
        print(f"✓ E-mail enviado com sucesso para: {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"✗ Erro ao enviar e-mail: {e}")
        return False

def main():
    destinatarios = get_recipients()
    if destinatarios:
        success = send_email(destinatarios)
        return 0 if success else 1
    else:
        print("Nenhum destinatário encontrado.")
        return 1

if __name__ == "__main__":
    exit(main())
