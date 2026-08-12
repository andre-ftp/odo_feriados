import json
import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


def load_holidays_json(year: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Carrega o ficheiro de feriados do ano indicado."""
    json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")
    target_year = year or datetime.now().year

    json_file = os.path.join(json_dir, f"feriados_municipais_{target_year}.json")
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Erro ao carregar {json_file}: {error}")

    print(f"Ficheiro de feriados não encontrado em {json_dir}")
    return None


def format_customs_unit(holiday: Dict[str, Any]) -> str:
    """Formata o nome da unidade aduaneira com base no seu tipo."""
    estancia = holiday.get("estancia", "")
    tipo = holiday.get("tipo", "")

    if tipo and tipo.lower() not in ("", "padrão"):
        return f"{tipo} do {estancia}"
    return estancia


def get_recipients() -> List[str]:
    """Obtém os destinatários através da API ou usa a lista predefinida."""
    api_url = os.getenv("RECIPIENTS_API_URL")
    if api_url:
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            emails = response.json().get("emails", [])
            if isinstance(emails, list):
                return [email for email in emails if isinstance(email, str) and email]
        except (requests.RequestException, ValueError, AttributeError) as error:
            print(f"Erro ao procurar destinatários na API: {error}")

    return ["andre.rodrigues@ftpporto.com", "cruz@dotlink.pt"]
    #return ["andre.rodrigues@ftpporto.com", "joao.danho@odo.pt", "sergio.martins@odo.pt", "rosa.sa@despachante.odo.pt"]


def get_next_holidays() -> List[Dict[str, Any]]:
    """Retorna as estâncias com feriado municipal para amanhã."""
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime("%Y-%m-%d")
    holiday_key = f"feriado_{tomorrow.year}"
    holidays_data = load_holidays_json(tomorrow.year)
    if not holidays_data:
        return []

    holidays_tomorrow: List[Dict[str, Any]] = []

    estancias = holidays_data.get("estancias", [])
    if not isinstance(estancias, list):
        return []

    for estancia in estancias:
        if not isinstance(estancia, dict) or estancia.get(holiday_key) != tomorrow_date:
            continue
        holidays_tomorrow.append(
            {
                "codigo": estancia.get("codigo"),
                "estancia": estancia.get("estancia"),
                "tipo": estancia.get("tipo"),
                "referencia_territorial": estancia.get("referencia_territorial"),
                "date": estancia.get(holiday_key),
                "name": estancia.get("feriado_descricao"),
                "revisao_especifica": estancia.get("revisao_especifica", False),
            }
        )

    return holidays_tomorrow


def send_email(recipients: List[str], holidays: List[Dict[str, Any]]) -> bool:
    """Envia o email com os detalhes dos feriados encontrados."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_server or not smtp_user or not smtp_password:
        print("Erro: credenciais SMTP não configuradas.")
        return False

    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        print("Erro: SMTP_PORT deve ser um número.")
        return False

    tomorrow = datetime.now() + timedelta(days=1)
    weekdays = (
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
    )
    months = (
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    )
    weekday = weekdays[tomorrow.weekday()]
    date_formatted = f"{tomorrow.day} de {months[tomorrow.month - 1]} de {tomorrow.year}"
    holiday_name = holidays[0].get("name") or "Feriado Municipal"
    body = (
        f"Informamos os(as) Colegas que na próxima {weekday}, {date_formatted}, "
        "realiza-se "
        "o Feriado Municipal referido em título, afetando os seguintes serviços:\n\n"
    )
    for holiday in holidays:
        body += (
            f"- {format_customs_unit(holiday)} ({holiday.get('codigo')}) — "
            f"{holiday.get('referencia_territorial')}\n"
        )
    body += "\nApresentamos os nossos melhores cumprimentos.\n\nO CONSELHO DIRETIVO"

    message = MIMEMultipart()
    message["From"] = smtp_user
    message["To"] = ", ".join(recipients)
    message["Subject"] = f"Aviso de Feriado Municipal - {holiday_name}"
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        with server:
            server.login(smtp_user, smtp_password)
            refused = server.sendmail(smtp_user, recipients, message.as_string())

        refused_recipients = set(refused)
        accepted_recipients = [
            recipient for recipient in recipients if recipient not in refused_recipients
        ]

        if accepted_recipients:
            print(
                "Destinatários aceites pelo servidor SMTP: "
                + ", ".join(accepted_recipients)
            )
        if refused:
            print("Destinatários recusados pelo servidor SMTP:")
            for recipient, error in refused.items():
                print(f"  - {recipient}: {error}")
            return False

        print(f"Email aceite pelo servidor SMTP para: {', '.join(recipients)}")
        return True
    except smtplib.SMTPRecipientsRefused as error:
        print("O servidor SMTP recusou todos os destinatários:")
        for recipient, recipient_error in error.recipients.items():
            print(f"  - {recipient}: {recipient_error}")
        return False
    except Exception as error:
        print(f"Erro ao enviar email: {error}")
        traceback.print_exc()
        return False


def group_holidays_by_name(
    holidays: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa as estâncias por feriado, preservando a ordem de ocorrência."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for holiday in holidays:
        name = holiday.get("name") or "Feriado Municipal"
        groups.setdefault(name, []).append(holiday)
    return groups


def main() -> int:
    print("Verificando feriados para amanhã...")
    holidays = get_next_holidays()

    if not holidays:
        print("Nenhum feriado municipal amanhã. Email não será enviado.")
        return 0

    print(f"{len(holidays)} feriado(s) encontrado(s) para amanhã:")
    for holiday in holidays:
        print(
            f"  - {holiday.get('name')} em {holiday.get('estancia')} "
            f"({holiday.get('referencia_territorial')})"
        )

    recipients = get_recipients()
    if not recipients:
        print("Nenhum destinatário encontrado.")
        return 1

    success = True
    holiday_groups = group_holidays_by_name(holidays)
    for holiday_name, holiday_group in holiday_groups.items():
        print(f"Enviando email para: {holiday_name}")
        if not send_email(recipients, holiday_group):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
