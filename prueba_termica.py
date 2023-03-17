from w1thermsensor import W1ThermSensor, Sensor

sensor = W1ThermSensor(Sensor.DS18B20, "0517c1fd10ff")
tem_in_c = sensor.get_temperature()
print(tem_in_c)
