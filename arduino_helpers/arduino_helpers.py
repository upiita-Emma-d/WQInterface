import sys
import glob
import serial
import time
import json
import itertools
list2d = [[1,2,3], [4,5,6], [7], [8,9]]
merged = list(itertools.chain(*list2d))
from arduino_helpers.oscilador import switch_led
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def limpiar_buffer(serial_arduino):
    serial_arduino.flushInput()
    #serial_arduino.write(bytes("o", 'utf-8'))
    timeout=time.time()+3.0
    data = b""
    while serial_arduino.inWaiting() or time.time()-timeout<0.0:
        if serial_arduino.inWaiting()>0:
            data+=serial_arduino.read(serial_arduino.inWaiting())
            timeout=time.time()+1.0
def init_arduinos(serial_arduino):
    limpiar_buffer(serial_arduino)
    # Send a string to the Arduino indicating that we want to read data from sensor 0

def main_arduino(serial_arduino):
    #serial_arduino.write(bytes("sensor_0", 'utf-8'))
    # Create a new serial communication object using 
    # the specified port and a baud rate of 9600
    #serial_arduino = serial.Serial(port_string, 9600)
    # Clear the input buffer of the Arduino


    #print("Ya escribi")

    # Initialize an empty list to store the received data
    los_datos = []
    # Start an infinite loop
    while 1:
        # Read a line of data from the serial port
        data = serial_arduino.readline()#.decode('cp437')
        #serial_arduino.flushInput()
        # Convert the data from bytes to text
        data_i = data.decode("utf-8")
        # If we receive an "END" signal from the Arduino, break the loop
        if data ==  (b'END\r\n'):
            print("BREAK")
            break
  
        try:
            # If the JSON processing is successful, add the object to the "los_datos" list
            r_json = json.loads(data_i)
            #print(r_json)
            los_datos.append(r_json)
            #print(r_json)
            if r_json.get("accion", None) == "led_rojo":
                # Sensor 0 led rojo
                switch_led(frecuencia = 25, NUMBER_LED = 3)
            elif r_json.get("accion", None) == "led_verde":
                # Sensor 1 led rojo 
                switch_led(frecuencia = 25, NUMBER_LED = 2)
            elif r_json.get("accion", None) == "led_azul":
                # Sensor 1 led rojo 
                switch_led(frecuencia = 25, NUMBER_LED = 1)
            elif r_json.get("sensor_1", None) is not None:
                # sensor 2 uv
                print("Leyendo UV")
                #switch_led(frecuencia = 25, NUMBER_LED = 2)
            elif r_json.get("sensor_2", None) is not None:
                # sensot 3 
                print("leyendo_uv")
                #switch_led(frecuencia = 25, NUMBER_LED = 3)
            ## LED AMBAR
            # elif r_json.get("accion", None) == "led_ambar":
            #     #Medimos el sensor 4
            #     switch_led(frecuencia = 100, NUMBER_LED = 0)
            # elif r_json.get("accion", None) == "led_ambar":
            #     #Medimos el sensor 5
            #     switch_led(frecuencia = 100, NUMBER_LED = 0)
        # If there is an error processing the JSON, print an error message and move on to the next iteration of the loop
        except ValueError:
            #print("Error_Json")
            pass
    # Return the "los_datos" list as the result of the function
    return los_datos

def parser_values_to_voltage(dato):
            try:
                return int(dato)  * (5 /1023)
            except (ValueError,TypeError):
                pass

def filter_data_and_create(diccionario_actual,cadena):
    #print(diccionario_actual)
    data_list = diccionario_actual.get(str(cadena),None)
    #print(data_list)
    if data_list is not None:
        #print(data_list)
        data_list = data_list.replace('[','').replace(']','').split(',')
        data_list.sort()
        data_higth = data_list[12:19]
        data_low = data_list[3:10]
        data_list = data_low + data_higth
        data_list = [ parser_values_to_voltage(value) for value in data_list]
        #print(data_list)
        return data_list
    else:
        return []
def create_array_structure(datos_arduino):
    ph_data = 0
    orp_data = 0
    nivel_data = 0
    estado_bomba = 0
    ph_data_list = []
    orp_data_list = []
    nivel_data_list = []
    #g_list_sen_0_amb = []
    #g_list_sen_1_amb = []
    g_list_sen_4_r = []
    g_list_sen_4_v = []
    g_list_sen_4_a = []
    
    g_list_sen_5_r = []
    g_list_sen_5_v = []
    g_list_sen_5_a = []

    g_list_sen_2_uv = []
    g_list_sen_3_uv = []

    for i in datos_arduino:
            #g_list_sen_0_amb.append(filter_data_and_create(i,"sensor_0_amb"))
            #g_list_sen_1_amb.append(filter_data_and_create(i,"sensor_1_amb"))
            
            g_list_sen_4_r.append(filter_data_and_create(i,"sensor_4_r"))
            g_list_sen_4_v.append(filter_data_and_create(i,"sensor_4_v"))
            g_list_sen_4_a.append(filter_data_and_create(i,"sensor_4_a"))
            
            g_list_sen_5_r.append(filter_data_and_create(i,"sensor_5_r"))
            g_list_sen_5_v.append(filter_data_and_create(i,"sensor_5_v"))
            g_list_sen_5_a.append(filter_data_and_create(i,"sensor_5_a"))
            
            g_list_sen_2_uv.append(filter_data_and_create(i,"sensor_uv_0"))

            g_list_sen_3_uv.append(filter_data_and_create(i,"sensor_uv_1"))
          
            ph_data = i.get("sensor_ph",None)
            orp_data = i.get("sensor_orp",None)
            nivel_data = i.get("sensor_nivel",None)
            estado_bomba = i.get("estado",None)
            if ph_data is not None:
                ph_data_list.append(ph_data)
            if orp_data is not None:
                orp_data_list.append(orp_data)
            if nivel_data is not None:
                nivel_data_list.append(nivel_data)      
    return (None,#list(itertools.chain(*g_list_sen_0_amb)),
            None,#list(itertools.chain(*g_list_sen_1_amb)),

            list(itertools.chain(*g_list_sen_4_r)),
            list(itertools.chain(*g_list_sen_4_v)),
            list(itertools.chain(*g_list_sen_4_a)),

            list(itertools.chain(*g_list_sen_5_r)),
            list(itertools.chain(*g_list_sen_5_v)),
            list(itertools.chain(*g_list_sen_5_a)),

            list(itertools.chain(*g_list_sen_2_uv)),
            list(itertools.chain(*g_list_sen_3_uv)),  
            ph_data_list ,
            orp_data_list, 
            nivel_data_list,
            estado_bomba)
