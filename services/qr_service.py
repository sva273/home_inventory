import qrcode
from io import BytesIO
from django.core.files import File

def generate_qr_for_box(box):
    """
    Генерируем QR-код для коробки. QR содержит ссылку на коробку в веб-приложении.
    """
    url = f"http://localhost:8000/boxes/{box.id}/"
    qr_img = qrcode.make(url)
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    filename = f'{box.id}.png'
    box.qr_code.save(filename, File(buffer), save=False)
    return box.qr_code
