from flask import Flask, render_template, Response, request
import threading
import time
import RPi.GPIO as GPIO
import flask
from linuxpy.video.device import Device

app = Flask(__name__)
camera = cv2.VideoCapture(0)  # веб-камера

controlX, controlY = 0, 0  # глобальные переменные положения джойстика с web-страницы

# GPIO setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setwarnings(False)

# Motor A (LEFT) pins
ENA = 17  # Enable pin for Motor A (PWM)
IN1 = 22  # Input 1 for Motor A
IN2 = 27  # Input 2 for Motor A

# Motor B (RIGHT) pins
ENB = 18  # Enable pin for Motor B (PWM)
IN3 = 23  # Input 3 for Motor B
IN4 = 24  # Input 4 for Motor B

# Setup pins as output
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# Initialize PWM for speed control
PWM_FREQ = 100  # PWM frequency in Hz
pwm_a = GPIO.PWM(ENA, PWM_FREQ)
pwm_b = GPIO.PWM(ENB, PWM_FREQ)

# Start PWM with 0 duty cycle (stopped)
pwm_a.start(0)
pwm_b.start(0)


def set_motor_a(speed, direction):
    """Set speed and direction for Motor A"""
    if direction == "forward":
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
    else:  # Stop
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)

    pwm_a.ChangeDutyCycle(abs(speed))


def set_motor_b(speed, direction):
    """Set speed and direction for Motor B"""
    if direction == "forward":
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
    else:  # Stop
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.LOW)

    pwm_b.ChangeDutyCycle(abs(speed))



def gen_frames():
    with Device.from_id(0) as cam:
        for frame in cam:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame.data + b"\r\n"

            
@app.route('/video_feed')
def video_feed():
    return flask.Response(
        gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Render index page"""
    return render_template('index.html')


@app.route('/control')
def control():
    """Receive joystick control input"""
    global controlX, controlY
    controlX = float(request.args.get('x')) / 100.0
    controlY = float(request.args.get('y')) / 100.0
    return '', 200, {'Content-Type': 'text/plain'}


def sender():
    """Continuous control loop for motors"""
    global controlX, controlY
    maxAbsSpeed = 100  # Maximum speed (PWM duty cycle)
    speedScale = 0.65  # Scale for speed (percentage of max speed)
    sendFreq = 10  # Update frequency in Hz

    while True:
        # Calculate motor speeds based on joystick input
        speed_a = maxAbsSpeed * (controlY + controlX)
        speed_b = maxAbsSpeed * (controlY - controlX)

        # Constrain speeds to allowed range
        speed_a = max(-maxAbsSpeed, min(speed_a, maxAbsSpeed))
        speed_b = max(-maxAbsSpeed, min(speed_b, maxAbsSpeed))

        # Determine direction
        dir_a = "forward" if speed_a > 0 else "backward" if speed_a < 0 else "stop"
        dir_b = "forward" if speed_b > 0 else "backward" if speed_b < 0 else "stop"

        # Set motor speeds and directions
        set_motor_a(speedScale * abs(speed_a), dir_a)
        set_motor_b(speedScale * abs(speed_b), dir_b)

        time.sleep(1 / sendFreq)


if __name__ == '__main__':
    threading.Thread(target=sender, daemon=True).start()
    app.run(debug=False, host='0.0.0.0', port=5000)

    # Cleanup GPIO on exit
    GPIO.cleanup()
