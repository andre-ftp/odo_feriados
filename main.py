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
        print("✗ Erro: Credenciais SMTP não configuradas.")
        print(f"  SMTP_SERVER: {'✓ Configurado' if smtp_server else '✗ Falta'}")
        print(f"  SMTP_USER: {'✓ Configurado' if smtp_user else '✗ Falta'}")
        print(f"  SMTP_PASSWORD: {'✓ Configurado' if smtp_password else '✗ Falta'}")
        print("Configure SMTP_SERVER, SMTP_USER e SMTP_PASSWORD como variáveis de ambiente no GitHub Secrets.")
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
        print(f"📧 Conectando a {smtp_server}:{smtp_port}...")
        
        if smtp_port == 465:
            print("🔒 Usando SMTPS (porta 465)...")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            print("🔐 Usando SMTP com STARTTLS (porta 587)...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        print(f"🔑 Autenticando como {smtp_user}...")
        server.login(smtp_user, smtp_password)
        print(f"📤 Enviando e-mail para: {', '.join(recipients)}")
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
        print(f"✓ E-mail enviado com sucesso para: {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"✗ Erro ao enviar e-mail: {e}")
        import traceback
        traceback.print_exc()
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
