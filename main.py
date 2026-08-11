import os
import smtplib
import requests
import json
import traceback
from typing import Any, Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente do ficheiro .env (opcional, para desenvolvimento)
# No GitHub Actions, as variáveis vêm de secrets
load_dotenv()

def load_holidays_json() -> Optional[Dict[str, Any]]:
    """
    Carrega dados de feriados do ficheiro JSON.
    Tenta primeiro feriados_2026.json, depois feriados_2027.json.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, "json")
    current_year = datetime.now().year
    
    # Tentar carregar JSON do ano atual
    for year in [current_year, current_year + 1]:
        json_file = os.path.join(json_dir, f"feriados_{year}.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar {json_file}: {e}")
    
    print(f"Ficheiro de feriados não encontrado em {json_dir}")
    return None

def format_customs_unit(holiday: Dict[str, Any]) -> str:
    """
    Formata o nome da unidade aduaneira com base no tipo.
    Exemplo: "Aeroporto de Faro" com tipo "Delegação" → "Delegação do Aeroporto de Faro"
    """
    estancia = holiday.get("estancia", "")
    tipo = holiday.get("tipo", "")
    
    if tipo and tipo.lower() not in ["", "padrão"]:
        return f"{tipo} do {estancia}"
    return estancia

def get_recipients() -> List[str]:
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

def get_holidays_for_tomorrow() -> List[Dict[str, Any]]:
    """
    Retorna lista de estâncias com feriado para amanhã.
    Cada item contém: codigo, estancia, tipo, referencia_territorial, date, name.
    """
    holidays_data = load_holidays_json()
    if not holidays_data:
        return []

    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date_str = tomorrow.strftime("%Y-%m-%d")
    current_year = datetime.now().year
    feriado_key = f"feriado_{current_year}"

    holidays_tomorrow: List[Dict[str, Any]] = []
    estancias = holidays_data.get("estancias", [])
    if isinstance(estancias, list):
        for estancia in estancias:
            if estancia.get(feriado_key) == tomorrow_date_str:
                holidays_tomorrow.append({
                    "codigo": estancia.get("codigo"),
                    "estancia": estancia.get("estancia"),
                    "tipo": estancia.get("tipo"),
                    "referencia_territorial": estancia.get("referencia_territorial"),
                    "date": estancia.get(feriado_key),
                    "name": estancia.get("feriado_descricao"),
                    "revisao_especifica": estancia.get("revisao_especifica", False)
                })

    return holidays_tomorrow


def send_email(recipients: List[str], holidays: List[Dict[str, Any]]) -> bool:
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

    # Obter o nome do feriado para o assunto
    holiday_name = holidays[0]["name"] if holidays else "Feriado Municipal"

    body = f"""Informamos os(as) Colegas que na próxima {tomorrow.strftime('%A').lower()}, {date_formatted}, realiza-se o Feriado Municipal referido em título, afetando os seguintes serviços:

"""

    # Adicionar informações dos feriados
    for holiday in holidays:
        unit_name = format_customs_unit(holiday)
        body += f"""- {unit_name} ({holiday['codigo']}) — {holiday['referencia_territorial']}

"""

    body += """Apresentamos os nossos melhores cumprimentos.

O CONSELHO DIRETIVO"""

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    # Definir o assunto com base no nome do feriado e localidade
    if holidays:
        location = holidays[0]["referencia_territorial"]
        msg["Subject"] = f"Aviso de Feriado Municipal - {holiday_name} de {location}"
    else:
        msg["Subject"] = "Aviso de Feriado Municipal"

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
        traceback.print_exc()
        return False

def main() -> int:
    print("🔍 Verificando feriados para amanhã...")
    holidays = get_holidays_for_tomorrow()

    if not holidays:
        print("✓ Nenhum feriado municipal amanhã. Email não será enviado.")
        return 0

    print(f"✓ {len(holidays)} feriado(s) encontrado(s) para amanhã:")
    for holiday in holidays:
        print(f"  • {holiday['name']} em {holiday['estancia']} ({holiday['referencia_territorial']})")

    destinatarios = get_recipients()
    if destinatarios:
        success = send_email(destinatarios, holidays)
        return 0 if success else 1
    else:
        print("Nenhum destinatário encontrado.")
        return 1


if __name__ == "__main__":
    exit(main())
