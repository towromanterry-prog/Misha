import smtplib
import socket
from email.message import EmailMessage

import config


SMTP_TIMEOUT_SECONDS = 15


def send_report_smtp(subject: str, body: str, attachment_name: str, attachment_bytes: bytes) -> None:
    if not config.SMTP_HOST:
        raise RuntimeError("SMTP не настроен: отсутствует SMTP_HOST")
    if not config.MAIL_TO:
        raise RuntimeError("SMTP не настроен: отсутствует MAIL_TO")
    if not config.MAIL_FROM:
        raise RuntimeError("SMTP не настроен: отсутствует MAIL_FROM")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.MAIL_FROM
    message["To"] = config.MAIL_TO
    message.set_content(body)
    message.add_attachment(
        attachment_bytes,
        maintype="text",
        subtype="plain",
        filename=attachment_name,
    )

    if config.SMTP_USE_SSL and config.SMTP_USE_STARTTLS:
        raise RuntimeError("Некорректная SMTP-конфигурация: одновременно включены SSL и STARTTLS")

    smtp_client = None
    try:
        if config.SMTP_USE_SSL:
            smtp_client = smtplib.SMTP_SSL(
                host=config.SMTP_HOST,
                port=config.SMTP_PORT,
                timeout=SMTP_TIMEOUT_SECONDS,
            )
        else:
            smtp_client = smtplib.SMTP(
                host=config.SMTP_HOST,
                port=config.SMTP_PORT,
                timeout=SMTP_TIMEOUT_SECONDS,
            )
            smtp_client.ehlo()
            if config.SMTP_USE_STARTTLS:
                smtp_client.starttls()
                smtp_client.ehlo()

        if config.SMTP_USER:
            smtp_client.login(config.SMTP_USER, config.SMTP_PASS)

        smtp_client.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError("Ошибка SMTP: неверный логин или пароль") from exc
    except smtplib.SMTPConnectError as exc:
        raise RuntimeError("Ошибка SMTP: не удалось подключиться к серверу") from exc
    except smtplib.SMTPServerDisconnected as exc:
        raise RuntimeError("Ошибка SMTP: сервер разорвал соединение") from exc
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Ошибка SMTP: {exc}") from exc
    except (socket.timeout, TimeoutError) as exc:
        raise RuntimeError("Ошибка SMTP: превышен таймаут подключения") from exc
    except OSError as exc:
        raise RuntimeError(f"Ошибка сети при отправке SMTP: {exc}") from exc
    finally:
        if smtp_client:
            try:
                smtp_client.quit()
            except Exception:
                pass
