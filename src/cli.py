#!/usr/bin/env python3
"""
CLI entry point для ExperimentalHTTPServer.
"""

import argparse
import sys
from typing import Sequence

from . import ExperimentalHTTPServer, __version__


def create_parser() -> argparse.ArgumentParser:
    """Создание и настройка парсера аргументов."""
    parser = argparse.ArgumentParser(
        prog="exphttp",
        description="Экспериментальный HTTP-сервер с кастомными методами, TLS и OPSEC режимом.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
    exphttp                              # Запуск на localhost:8080
    exphttp --tls --auth random          # HTTPS со случайными credentials
    exphttp -H 0.0.0.0 -p 443 --tls      # Публичный HTTPS на порту 443
    exphttp --opsec --sandbox            # OPSEC + Sandbox режимы

Поддерживаемые HTTP методы:
    GET, POST, PUT, OPTIONS              # Стандартные
    FETCH, INFO, PING, NONE, SMUGGLE     # Кастомные
        """
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    # Сетевые опции
    network = parser.add_argument_group("Сетевые опции")
    network.add_argument(
        "-H", "--host",
        default="127.0.0.1",
        metavar="HOST",
        help="Хост для привязки (по умолчанию: 127.0.0.1)"
    )
    network.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        metavar="PORT",
        help="Порт для прослушивания (по умолчанию: 8080)"
    )

    # Директория
    parser.add_argument(
        "-d", "--dir",
        default=".",
        metavar="DIR",
        help="Корневая директория (по умолчанию: текущая)"
    )

    # Режимы работы
    modes = parser.add_argument_group("Режимы работы")
    modes.add_argument(
        "-o", "--opsec",
        action="store_true",
        help="OPSEC режим (случайные имена методов, маскировка под nginx)"
    )
    modes.add_argument(
        "-s", "--sandbox",
        action="store_true",
        help="Sandbox режим (доступ только к uploads/)"
    )
    modes.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Тихий режим (минимум логов)"
    )

    # Лимиты
    limits = parser.add_argument_group("Лимиты")
    limits.add_argument(
        "-m", "--max-size",
        type=int,
        default=100,
        metavar="MB",
        help="Макс. размер загрузки в MB (по умолчанию: 100)"
    )
    limits.add_argument(
        "-w", "--workers",
        type=int,
        default=10,
        metavar="N",
        help="Количество worker потоков (по умолчанию: 10)"
    )

    # TLS опции
    tls = parser.add_argument_group("TLS опции")
    tls.add_argument(
        "--tls",
        action="store_true",
        help="Включить HTTPS (генерирует самоподписный сертификат)"
    )
    tls.add_argument(
        "--cert",
        metavar="FILE",
        help="Путь к файлу сертификата (PEM)"
    )
    tls.add_argument(
        "--key",
        metavar="FILE",
        help="Путь к файлу приватного ключа (PEM)"
    )

    # Аутентификация
    auth = parser.add_argument_group("Аутентификация")
    auth.add_argument(
        "--auth",
        metavar="CREDS",
        help="Basic Auth: 'user:pass', 'random', или 'user' (random пароль)"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Главная точка входа."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Собираем конфиг из аргументов
    config = {
        "host": args.host,
        "port": args.port,
        "root_dir": args.dir,
        "opsec_mode": args.opsec,
        "sandbox_mode": args.sandbox,
        "max_upload_size": args.max_size * 1024 * 1024,
        "max_workers": args.workers,
        "quiet": args.quiet,
        "tls": args.tls or bool(args.cert),
        "cert_file": args.cert,
        "key_file": args.key,
        "auth": args.auth,
    }

    try:
        server = ExperimentalHTTPServer(**config)
        server.start()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
