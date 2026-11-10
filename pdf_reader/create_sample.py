import pymupdf

def create_sample_pdf(filepath="sample.pdf"):
    doc = pymupdf.open()

    # Страница 1
    page1 = doc.new_page(width=595, height=842) # A4
    page1.insert_text((60, 100), "Добро пожаловать в PDF Читалка!", fontsize=24, color=(0.15, 0.4, 0.8))
    page1.insert_text((60, 140), "Это тестовый многостраничный документ для демонстрации возможностей программы.", fontsize=12)

    page1.insert_text((60, 180), "Основные возможности вашей новой читалки:", fontsize=14)
    features = [
        "1. Навигация по страницам: стрелки влево/вправо, PageUp/PageDown, Пробел.",
        "2. Масштабирование: кнопки +/-, колесико мыши с зажатым Ctrl, кнопки «По ширине».",
        "3. Ночной режим: кнопка «Ночной режим» инвертирует цвета для комфортного чтения в темноте.",
        "4. Полнотекстовый поиск: нажмите Ctrl+F, чтобы быстро найти любое слово с подсветкой.",
        "5. Поворот страниц: кнопка «Поворот» поворачивает документ на 90 градусов.",
        "6. Запоминание прогресса: читалка помнит последний открытый файл и номер страницы.",
        "7. Поддержка открытия через контекстное меню Windows («Открыть с помощью»)."
    ]
    y = 215
    for f in features:
        page1.insert_text((75, y), f, fontsize=11)
        y += 28

    page1.insert_text((60, 480), "Попробуйте выполнить поиск слова «Масштабирование» через Ctrl+F!", fontsize=12, color=(0.2, 0.6, 0.2))
    page1.insert_text((60, 780), "Страница 1 из 3", fontsize=10, color=(0.5, 0.5, 0.5))

    # Страница 2
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((60, 100), "Страница 2: Горячие клавиши", fontsize=22, color=(0.8, 0.3, 0.1))

    shortcuts = [
        ("Ctrl + O", "Открыть другой PDF документ"),
        ("← / → или PageUp / PageDown", "Перейти на предыдущую / следующую страницу"),
        ("Пробел / Backspace", "Быстрое перелистывание вперед / назад"),
        ("Home / End", "Перейти на самую первую / последнюю страницу"),
        ("Ctrl + Колесико мыши", "Плавное увеличение / уменьшение масштаба"),
        ("Ctrl + 0", "Сброс масштаба к исходным 100%"),
        ("Ctrl + W", "Автоматически подогнать страницу по ширине окна"),
        ("Ctrl + H", "Подогнать страницу целиком по высоте окна"),
        ("Ctrl + I", "Включить / выключить ночной режим (инверсия цветов)"),
        ("Ctrl + F", "Открыть панель поиска по тексту"),
        ("F11", "Режим на весь экран (Fullscreen)")
    ]

    y = 150
    for key, desc in shortcuts:
        page2.insert_text((75, y), key, fontsize=11, fontname="Helvetica-Bold", color=(0.1, 0.1, 0.1))
        page2.insert_text((280, y), "— " + desc, fontsize=11, color=(0.2, 0.2, 0.2))
        y += 32

    page2.insert_text((60, 780), "Страница 2 из 3", fontsize=10, color=(0.5, 0.5, 0.5))

    # Страница 3
    page3 = doc.new_page(width=595, height=842)
    page3.insert_text((60, 100), "Страница 3: Заключение", fontsize=22, color=(0.2, 0.5, 0.3))
    page3.insert_text((60, 150), "Вы можете открывать любые свои файлы PDF через меню «Открыть»", fontsize=13)
    page3.insert_text((60, 180), "или просто перетащив нужный файл на ярлык запуска читалки.", fontsize=13)
    page3.insert_text((60, 240), "Приятного и комфортного чтения!", fontsize=16, color=(0.15, 0.4, 0.8))
    page3.insert_text((60, 780), "Страница 3 из 3", fontsize=10, color=(0.5, 0.5, 0.5))

    doc.save(filepath)
    print(f"Sample PDF created successfully at {filepath}")

if __name__ == "__main__":
    create_sample_pdf("C:/Users/Admin/.gemini/antigravity/scratch/pdf_reader/sample.pdf")
