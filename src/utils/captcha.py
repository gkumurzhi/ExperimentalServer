"""
Генератор CAPTCHA-подобных изображений с паролем.
Использует SVG для генерации без внешних зависимостей.
"""

import base64
import random
import math


def generate_password_captcha(password: str, width: int = 280, height: int = 80) -> str:
    """
    Генерация SVG изображения с паролем в стиле капчи.

    Args:
        password: Пароль для отображения
        width: Ширина изображения
        height: Высота изображения

    Returns:
        Base64-encoded SVG data URI
    """
    # Цвета для символов (контрастные на тёмном фоне)
    colors = ['#00d4ff', '#7b2cbf', '#4ade80', '#facc15', '#fb7185', '#f97316', '#a78bfa']

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        # Фон
        '<rect width="100%" height="100%" fill="#0d1117"/>',
    ]

    # Добавляем шум - случайные линии
    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = random.choice(['#30363d', '#21262d', '#161b22'])
        stroke_width = random.uniform(1, 3)
        svg_parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{stroke_width}"/>'
        )

    # Добавляем точки-шум
    for _ in range(30):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        r = random.uniform(1, 3)
        color = random.choice(['#30363d', '#21262d', '#3d4450'])
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')

    # Рисуем символы пароля
    char_width = (width - 40) / len(password)
    start_x = 20

    for i, char in enumerate(password):
        x = start_x + i * char_width + char_width / 2
        y = height / 2

        # Случайные искажения
        rotation = random.randint(-15, 15)
        y_offset = random.randint(-8, 8)
        font_size = random.randint(24, 32)
        color = random.choice(colors)

        # Небольшой сдвиг для каждого символа
        x_offset = random.randint(-3, 3)

        svg_parts.append(
            f'<text x="{x + x_offset}" y="{y + y_offset + font_size/3}" '
            f'font-family="Consolas, Monaco, monospace" '
            f'font-size="{font_size}" font-weight="bold" '
            f'fill="{color}" text-anchor="middle" '
            f'transform="rotate({rotation}, {x + x_offset}, {y + y_offset})">'
            f'{_escape_xml(char)}</text>'
        )

    # Добавляем волнистые линии поверх текста
    for _ in range(3):
        points = []
        y_base = random.randint(20, height - 20)
        amplitude = random.randint(5, 15)
        frequency = random.uniform(0.02, 0.05)
        phase = random.uniform(0, 2 * math.pi)

        for x in range(0, width, 5):
            y = y_base + amplitude * math.sin(frequency * x + phase)
            points.append(f"{x},{y:.1f}")

        color = random.choice(['#30363d', '#21262d', '#2d333b'])
        svg_parts.append(
            f'<polyline points="{" ".join(points)}" '
            f'fill="none" stroke="{color}" stroke-width="2"/>'
        )

    svg_parts.append('</svg>')

    svg_content = ''.join(svg_parts)

    # Кодируем в base64
    svg_b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    return f'data:image/svg+xml;base64,{svg_b64}'


def _escape_xml(text: str) -> str:
    """Экранирование специальных символов XML."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
