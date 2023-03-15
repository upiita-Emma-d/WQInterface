import platform
import time

PIN_LIST = [37, 36, 35, 33]
if platform.system() == 'Linux' and platform.machine() == 'armv7l':
    print("*"*10)
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    for PIN in PIN_LIST:
        GPIO.setup(PIN, GPIO.OUT)

else:
    import fake_rpigpio as GPIO
#GPIO.setwarnings(False) 

def sleep_ms(tiempo):
    return tiempo / 1000
def switch_led(frecuencia = 1000, NUMBER_LED = 0):
    #frecuencia = input("Frecuencia :")
    frecuencia = int(frecuencia)
    ESPERA = (1/frecuencia)
    ACTUAL_PIN = PIN_LIST[NUMBER_LED]

    for i in range( int(frecuencia)):
        GPIO.output(ACTUAL_PIN, GPIO.HIGH)
        time.sleep(ESPERA)
        GPIO.output(ACTUAL_PIN, GPIO.LOW)
        time.sleep(ESPERA)
    # print("ACABO LED")
    GPIO.output(ACTUAL_PIN, GPIO.LOW)