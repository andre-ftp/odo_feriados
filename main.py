import os
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env se existir
load_dotenv()

def get_recipients():
    """
    Obtém a lista de destinatários.
    Atualmente retorna uma lista fixa, mas está preparado para buscar via API.
    """
    # Exemplo de como seria a busca via API no futuro:
    # api_url = os.getenv("RECIPIENTS_API_URL")
    # if api_url:
    #     response = requests.get(api_url)
    #     return response.json()["emails"]
    
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
