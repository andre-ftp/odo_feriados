import os
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente do ficheiro .env (opcional, para desenvolvimento)
# No GitHub Actions, as variáveis vêm de secrets
load_dotenv()

def get_recipients():
    """
    Obtém a lista de destinatários. No futuro será baseado na API ODO.
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
    return ["andre.rodrigues@ftpporto.com", "cruz@dotlink.pt"]

def load_holidays_json():
    """
    Carrega os feriados do ficheiro JSON.
    """
    json_path = "json/feriados_municipais_ate_2027.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON de feriados: {e}")
        return None

def get_holidays_for_tomorrow():
    """
    Retorna lista de feriados para amanhã.
    Cada item contém: municipality, district_or_region, name, date, weekday
    """
    holidays_data = load_holidays_json()
    if not holidays_data:
        return []
    
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date_str = tomorrow.strftime("%Y-%m-%d")
    tomorrow_weekday = tomorrow.strftime("%A")
    
    # Mapeamento português de dias da semana
    weekday_pt = {
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }
    
    holidays_tomorrow = []
    for holiday in holidays_data.get("holidays", []):
        for date_entry in holiday.get("dates", []):
            if date_entry["date"] == tomorrow_date_str:
                holidays_tomorrow.append({
                    "municipality": holiday["municipality"],
                    "district_or_region": holiday["district_or_region"],
                    "name": holiday["name"],
                    "date": date_entry["date"],
                    "weekday": date_entry["weekday"]
                })
    
    return holidays_tomorrow


def send_email(recipients, holidays):
    """
    Envia o e-mail para a lista de destinatários com detalhes dos feriados.
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

    # Construir o corpo do email com os detalhes dos feriados
    tomorrow = datetime.now() + timedelta(days=1)
    date_formatted = tomorrow.strftime("%d de %B de %Y").replace(
        "January", "Janeiro").replace(
        "February", "Fevereiro").replace(
        "March", "Março").replace(
        "April", "Abril").replace(
        "May", "Maio").replace(
        "June", "Junho").replace(
        "July", "Julho").replace(
        "August", "Agosto").replace(
        "September", "Setembro").replace(
        "October", "Outubro").replace(
        "November", "Novembro").replace(
        "December", "Dezembro")
    
    body = f"""Olá,

Aviso de Feriados Municipais - {date_formatted}

No dia de amanhã ({date_formatted}), existem os seguintes feriados municipais:

"""
    
    for holiday in holidays:
        body += f"""• {holiday['name']}
  Localidade: {holiday['municipality']}, {holiday['district_or_region']}
  Data: {holiday['date']} ({holiday['weekday']})

"""
    
    body += """---
Este é um e-mail automático enviado pelo sistema Odo Feriados.
"""
    
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"🎉 Feriados Municipais Amanhã ({tomorrow.strftime('%d/%m/%Y')})"
    msg.attach(MIMEText(body, "plain", "utf-8"))

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
    print("🔍 Verificando feriados para amanhã...")
    holidays = get_holidays_for_tomorrow()
    
    if not holidays:
        print("✓ Nenhum feriado municipal amanhã. Email não será enviado.")
        return 0
    
    print(f"✓ {len(holidays)} feriado(s) encontrado(s) para amanhã:")
    for holiday in holidays:
        print(f"  • {holiday['name']} em {holiday['municipality']}")
    
    destinatarios = get_recipients()
    if destinatarios:
        success = send_email(destinatarios, holidays)
        return 0 if success else 1
    else:
        print("Nenhum destinatário encontrado.")
        return 1

if __name__ == "__main__":
    exit(main())
