import flask
import time
from picamera2 import Picamera2
import io

app = flask.Flask('basic-web-cam')

picam2 = Picamera2()

# Настроим поток изображения
def gen_frames():
    # Запуск камеры
    picam2.start()  

    try:
        while True:
            # Преобразуем в JPEG
            with io.BytesIO() as output:
                picam2.capture_file(output, format='jpeg')  # Сохраняем изображение в JPEG
                frame = output.getvalue()  # Получаем JPEG данные

                # Отправляем JPEG данные через поток
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            time.sleep(0.1)  # Небольшая задержка для снижения нагрузки на процессор
    finally:
        picam2.stop()  # Остановить камеру, когда поток завершится

@app.route("/")
def index():
    # HTML для отображения видео на весь экран
    return '''
    <html>
        <head>
            <style>
                body, html {
                    height: 100%;
                    margin: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: black;
                }
                img {
                    width: 100vw;
                    height: 100vh;
                    object-fit: cover;
                }
            </style>
        </head>
        <body>
            <img src="/stream" />
        </body>
    </html>
    '''

@app.route("/stream")
def stream():
    return flask.Response(
        gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
