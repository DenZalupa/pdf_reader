import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_app_icon(output_ico="app.ico", output_png="app.png"):
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Тень под базовым значком (squircle)
    shadow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    pad = 90
    shadow_offset = 35
    shadow_draw.rounded_rectangle(
        [pad, pad + shadow_offset, size - pad, size - pad + shadow_offset],
        radius=210,
        fill=(0, 0, 0, 110)
    )
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(38))
    img.alpha_composite(shadow_img)

    # 2. Основная подложка (Squircle с градиентом)
    squircle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sq_draw = ImageDraw.Draw(squircle)
    sq_draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=210,
        fill=(255, 255, 255, 255)
    )

    # Создаем красивый градиент: от кораллово-красного (#FF334B) к глубокому рубиновому (#990014)
    grad = Image.new("RGBA", (size, size))
    for y in range(size):
        ratio = y / size
        # Интерполяция цветов
        r = int(255 * (1 - ratio) + 160 * ratio)
        g = int(55 * (1 - ratio) + 10 * ratio)
        b = int(75 * (1 - ratio) + 25 * ratio)
        for x in range(size):
            # Диагональный оттенок
            diag_boost = int((size - x) / size * 20)
            grad.putpixel((x, y), (min(255, r + diag_boost), g, b, 255))

    # Маскируем градиент по форме скругленного квадрата
    squircle_mask = squircle.split()[3]
    base_tile = Image.composite(grad, Image.new("RGBA", (size, size), (0, 0, 0, 0)), squircle_mask)
    img.alpha_composite(base_tile)

    # 3. Внутренний тонкий светлый блик по контуру
    sq_highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(sq_highlight)
    h_draw.rounded_rectangle(
        [pad + 2, pad + 2, size - pad - 2, size - pad - 2],
        radius=208,
        outline=(255, 255, 255, 70),
        width=4
    )
    img.alpha_composite(sq_highlight)

    # 4. Тень от листа бумаги внутри значка
    doc_left = 260
    doc_top = 210
    doc_right = 764
    doc_bottom = 814
    fold_size = 140

    sheet_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sheet_shadow)
    s_draw.rounded_rectangle(
        [doc_left, doc_top + 20, doc_right, doc_bottom + 20],
        radius=36,
        fill=(0, 0, 0, 95)
    )
    sheet_shadow = sheet_shadow.filter(ImageFilter.GaussianBlur(24))
    img.alpha_composite(sheet_shadow)

    # 5. Лист бумаги с загнутым уголком
    # Полигон листа без правого верхнего угла
    sheet = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(sheet)

    # Координаты загнутого угла
    corner_x = doc_right - fold_size
    corner_y = doc_top + fold_size

    paper_poly = [
        (doc_left + 36, doc_top),
        (corner_x, doc_top),
        (doc_right, corner_y),
        (doc_right, doc_bottom - 36),
        (doc_right - 36, doc_bottom),
        (doc_left + 36, doc_bottom),
        (doc_left, doc_bottom - 36),
        (doc_left, doc_top + 36)
    ]
    sh_draw.polygon(paper_poly, fill=(255, 255, 255, 255))
    # Скругленные углы
    sh_draw.pieslice([doc_left, doc_top, doc_left + 72, doc_top + 72], 180, 270, fill=(255, 255, 255, 255))
    sh_draw.pieslice([doc_left, doc_bottom - 72, doc_left + 72, doc_bottom], 90, 180, fill=(255, 255, 255, 255))
    sh_draw.pieslice([doc_right - 72, doc_bottom - 72, doc_right, doc_bottom], 0, 90, fill=(255, 255, 255, 255))

    # Смягченный край бумаги
    img.alpha_composite(sheet)

    # Загнутый уголок (треугольник с тенью)
    fold_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fs_draw = ImageDraw.Draw(fold_shadow)
    fs_draw.polygon([
        (corner_x, doc_top),
        (corner_x, corner_y),
        (doc_right, corner_y)
    ], fill=(0, 0, 0, 60))
    fold_shadow = fold_shadow.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(fold_shadow)

    fold = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fold)
    f_draw.polygon([
        (corner_x, doc_top),
        (corner_x, corner_y),
        (doc_right, corner_y)
    ], fill=(232, 234, 238, 255))
    f_draw.line([(corner_x, doc_top), (doc_right, corner_y)], fill=(210, 214, 220, 255), width=3)
    img.alpha_composite(fold)

    # 6. Строки текста на документе (стилизованные мягкие полоски)
    lines_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    l_draw = ImageDraw.Draw(lines_img)
    line_color = (218, 224, 233, 255)

    l_draw.rounded_rectangle([doc_left + 65, doc_top + 105, doc_left + 260, doc_top + 125], radius=10, fill=line_color)
    l_draw.rounded_rectangle([doc_left + 65, doc_top + 155, doc_left + 200, doc_top + 175], radius=10, fill=line_color)

    l_draw.rounded_rectangle([doc_left + 65, doc_bottom - 165, doc_right - 65, doc_bottom - 145], radius=10, fill=line_color)
    l_draw.rounded_rectangle([doc_left + 65, doc_bottom - 115, doc_right - 140, doc_bottom - 95], radius=10, fill=line_color)
    img.alpha_composite(lines_img)

    # 7. Центральная плашка «PDF»
    badge_w = 350
    badge_h = 175
    badge_x1 = (size - badge_w) // 2
    badge_y1 = doc_top + 280
    badge_x2 = badge_x1 + badge_w
    badge_y2 = badge_y1 + badge_h

    # Тень под плашкой
    badge_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bs_draw = ImageDraw.Draw(badge_shadow)
    bs_draw.rounded_rectangle([badge_x1, badge_y1 + 10, badge_x2, badge_y2 + 10], radius=32, fill=(180, 0, 20, 110))
    badge_shadow = badge_shadow.filter(ImageFilter.GaussianBlur(16))
    img.alpha_composite(badge_shadow)

    # Сама красная плашка
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge)
    b_draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=30, fill=(229, 28, 50, 255))
    b_draw.rounded_rectangle([badge_x1 + 2, badge_y1 + 2, badge_x2 - 2, badge_y2 - 2], radius=28, outline=(255, 120, 130, 180), width=3)
    img.alpha_composite(badge)

    # Текст «PDF»
    font_size = 98
    font_path = r"C:\Windows\Fonts\segoeuib.ttf"
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\arialbd.ttf"
    font = ImageFont.truetype(font_path, font_size)

    # Центрирование текста
    bbox = font.getbbox("PDF")
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = badge_x1 + (badge_w - text_w) // 2
    ty = badge_y1 + (badge_h - text_h) // 2 - bbox[1]

    text_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(text_img)
    t_draw.text((tx, ty), "PDF", font=font, fill=(255, 255, 255, 255))
    img.alpha_composite(text_img)

    # Сохраняем иконки
    # 1. 256x256 PNG
    png_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    png_256.save(output_png, "PNG")

    # 2. Мультиразмерный ICO для Windows
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(output_ico, format="ICO", sizes=icon_sizes)
    print(f"Icon created successfully: {output_ico} and {output_png}")

if __name__ == "__main__":
    create_app_icon(
        output_ico=r"C:\Users\Admin\.gemini\antigravity\scratch\pdf_reader\app.ico",
        output_png=r"C:\Users\Admin\.gemini\antigravity\scratch\pdf_reader\app.png"
    )
