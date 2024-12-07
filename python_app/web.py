import flask
import time
from picamera2 import Picamera2
import io
app = flask.Flask('basic-web-cam')

picam2 = Picamera2()

# Настроим поток изображения
def gen_frames():
    # Настроим камеру (если нужно, выберите настройки)
    picam2.start_preview()  # Этот метод для предварительного просмотра, можно не использовать, если не нужно отображать на экране
    picam2.start()  # Запуск камеры

    try:
        while True:
            
            # Преобразуем в JPEG
            with io.BytesIO() as output:
                picam2.capture_file(output, format='jpeg')  # Сохраняем изображение в JPEG
                frame = output.getvalue()  # Получаем JPEG данные

                # Отправляем JPEG данные через поток
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            time.sleep(0.1)  # Небольшая задержка, чтобы снизить нагрузку на процессор
    finally:
        picam2.stop()  # Остановить камеру, когда поток завершится

@app.route("/")
def index():
    return '<html><img src="/stream" /></html>'

@app.route("/stream")
def stream():
    return flask.Response(
        gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
