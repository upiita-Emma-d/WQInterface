import fake_rpigpio as RPi
import json 
import sys
import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QWidget,
    QSpinBox,
    QComboBox,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QLCDNumber,
    QRadioButton,
    )

import matplotlib 
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import serial
import numpy as np
import glob
import sys
from serialport_helpers.serialport import get_serial_ports 
from interface_helpers.interfacecustom import add_port
from arduino_helpers.arduino_helpers import (limpiar_buffer,
                                             main_arduino,
                                             create_array_structure,
                                             init_arduinos,
                                             )
import platform
import random


if platform.system() == 'Linux' and platform.machine() == 'armv7l':
    from w1thermsensor import W1ThermSensor, Sensor
    sensor = W1ThermSensor(Sensor.DS18B20, "0517c1fd10ff")
else:
    W1ThermSensor = None
    Sensor = None
    sensor = None

def cov_fq_data(ph_data_list , orp_data_list, nivel_data_list):
    ph = 0
    orp = 0
    nivel = 0
    print(f"{ph_data_list} {orp_data_list} {nivel_data_list}")
    if len(ph_data_list) > 0:
        ph = (np.mean(ph_data_list) * (5/1023) * (-5.746)) + 22.371
    if len(orp_data_list) > 0:
        orp = ( ( np.mean(orp_data_list) * (5/1023) ) * (1152.2) ) - 1951.6 #- 1.66074766) / (0.00093458)                    
    if len(nivel_data_list) > 0:
        nivel = np.mean(nivel_data_list) * (5/1023)
    return ph, orp, nivel
            
def operation_in_trans_data(data_flat):
    #print(data_flat)
    data_flat.sort()
    #print(data_flat)
    if data_flat is not None:
        mayores_array = data_flat[7:]
        menores_array = data_flat[3:9]
        #data_np = np.mean(data_flat)
        promedio = np.mean(data_flat)
        #print(promedio)
        mayores_promedio =  np.mean(mayores_array)
        menores_promedio =  np.mean(menores_array)
        #promedio = np.mean(data_flat)
        return mayores_promedio, menores_promedio, promedio
    else :
        return (0,0,0)

class CreateLcdData:
    """
    This is the CreateLcdData class, which is used to create a QLabel and a QLCDNumber and add them to a layout.
    """

    def __init__(self, control_layout, label_to_LCD ,value = 0, column_data = 5):
        """
        This is the constructor method of the class. It is executed when a new
        instance of the class is created.

        Parameters:
        control_layout (QLayout): Layout where the QLabel and QLCDNumber will be added.
        label_to_LCD (str): Text for the QLabel.
        value (int): Initial value for the QLCDNumber. Default is 0.
        column_data (int): Column of the layout where the QLabel and QLCDNumber will be added.
        """
        self.lcds_label = QLabel(label_to_LCD)
        
        self.lcd = QLCDNumber(5)  # 5 digits
        self.lcd.display(value)
        control_layout.addWidget( self.lcds_label,0,column_data)
        control_layout.addWidget( self.lcd,1,column_data)
        
    def update_lcd(self, value):
        self.lcd.display(value)

def get_temperature_general():
    if W1ThermSensor is not None:
        for sensor in W1ThermSensor.get_available_sensors():
            print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
        return "%.2f" % (sensor.id, sensor.get_temperature())
    else: 
        return 1

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Create a Figure object with the specified size and resolution
        fig = Figure(figsize=(width, height), dpi=dpi)
        # Add a subplot to the Figure
        self.axes = fig.add_subplot(111)
        # Set the titles of the graph's axes
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Voltage (V)")
        # Call the constructor of the parent class FigureCanvasQTAgg with the Figure object as an argument
        super(MplCanvas, self).__init__(fig)

def spb_config(max_value : int, min_value : int, steps_in_buttons : int):
    # this object allows the user to enter and select an integer numeric value within a specified range. 
    spb_samples = QSpinBox()
    spb_samples.setMinimum(max_value)
    spb_samples.setMaximum(min_value)
    # Is used to set the step size to be used when incrementing or decrementing
    spb_samples.setSingleStep(steps_in_buttons)
    return spb_samples

class MainWindow(QMainWindow):
    # Call the __init__ method of the parent class
    def __init__(self):
        super().__init__()
        # Set the window title
        self.setWindowTitle("Data acquisition system")
        # Create a MplCanvas object for drawing the graph and place it in a vertical QVBoxLayout
        self.canvas = MplCanvas(self, width=5, 
                                height=5, dpi=100)
        layout_hor = QVBoxLayout()
        self.progress_bar = QProgressBar()
        # Establecer el rango mínimo y máximo de la barra de progreso en 0 y 100, respectivamente
        self.progress_bar.setMinimum(26)#0.2
        self.progress_bar.setMaximum(50)#0.4
        layout_hor.addWidget(self.progress_bar)
        # Create a QVBoxLayout object for insert to widgets
        main_layout = QVBoxLayout()
        # Add widgets to the main_layout
        main_layout.addWidget(self.canvas)
        # Create a QGridLayout to hold the user interface controls
        control_layout = QGridLayout()
        # Create labels, combo boxes, buttons, and a number selector to display various options to the user
        lbl_sample_size =QLabel("Sample size:")
        self.com_port = ""
        # Create a QComboBox object  
        # It is similar to a drop-down menu or a selection box in a web browser.
        self.cb_port = QComboBox()
        # We receive a list of the ports that are available and pass it as a parameter to create the items 
        lbl_com_port = QLabel("PLACA FQ:")
        #self.cb_port.addItems(get_serial_ports(self))
        print(get_serial_ports(self))
        self.cb_port.addItems([x for x in get_serial_ports(self) if "USB" in x])
        self.cb_port.activated.connect(self.add_port)
        
        lbl_com_port_2 = QLabel("PLACA NyT:")
        self.cb_port_2 = QComboBox()
        self.cb_port_2.addItems([x for x in get_serial_ports(self) if "ACM" in x])
        self.cb_port_2.activated.connect(self.add_port_2)
        
        
        # initialize the variable samples to 1
        self.samples = 100
    
        spb_samples = spb_config(50, 3000, 10)
        spb_samples.valueChanged.connect(self.spb_samples_changed)
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.start_acquisition)
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_acquisition)
        
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_file)
        
        self.pH = CreateLcdData(control_layout, "pH", 10, 5)
        self.orp = CreateLcdData(control_layout, "ORP", 10, 6)
        self.temperatura = CreateLcdData(control_layout, "Temperatura", 10, 7)
        self.nivel = CreateLcdData(control_layout, "Nivel",10,8)
        
        
        # Add the controls to the QGridLayout
        control_layout.addWidget(lbl_com_port,0,0)
        control_layout.addWidget(self.cb_port,1,0)
        
        control_layout.addWidget(lbl_com_port_2,0,1)
        control_layout.addWidget(self.cb_port_2,1,1)
        
        control_layout.addWidget(lbl_sample_size,0,2)

        control_layout.addWidget(spb_samples,1,2)
        control_layout.addWidget(self.btn_start,1,3)
        control_layout.addWidget(self.btn_stop,1,4)
        control_layout.addWidget(self.btn_save,1,5)
        # Add the layouts to a central widget and show it in the window
        main_layout.addLayout(control_layout)
        main_layout.addLayout(layout_hor)
        widget = QWidget()
        widget.setLayout(main_layout)
        # Set some properties for the controls 
        self.setCentralWidget(widget)
        self.btn_start.show()
        self.btn_stop.hide()
        self.btn_save.hide()
        self.count = 0        
        self.micro_board = None
        self.high_value_board = 3.3
        self.board_resolution = 2**12-1

        self.btn_dev_mode = QPushButton("Modo de desarrollo")
        self.statusBar().showMessage("Modo de desarrollo activado")
        self.btn_dev_mode.clicked.connect(self.toggle_dev_mode)
        control_layout.addWidget(self.btn_dev_mode, 2, 0)

    def toggle_dev_mode(self):
        if self.btn_dev_mode.text() == "Modo de desarrollo":
            self.btn_dev_mode.setText("Modo de producción")
            # Realizar acciones necesarias en el modo de desarrollo
            self.statusBar().clearMessage()

        else:
            self.btn_dev_mode.setText("Modo de desarrollo")
            # Realizar acciones necesarias en el modo de producción
            self.statusBar().showMessage("Modo de desarrollo activado")

    def add_port(self):
        self.com_port = str(self.cb_port.currentText()) 
        print(self.com_port)
    
    def add_port_2(self):
        self.com_port_2 = str(self.cb_port_2.currentText()) 
        print(self.com_port_2)
        
    
    def spb_samples_changed(self,val_samples):
        self.samples = val_samples


    def start_acquisition(self):

        try:
            import Adafruit_ADS1x15
            self.adc = Adafruit_ADS1x15.ADS1115()  
            self.GAIN = 1       
        except RuntimeError:
            print("ERR_____--")
            self.adc = None
            pass
        # Manejar la excepción personalizada aquí

        if self.btn_dev_mode.text() == "Modo de desarrollo":
            print("HOLA BNEBE")
            self.btn_start.hide()
            self.btn_stop.show()
            self.btn_save.hide()
            # If this is the first time this code block 
            # is being executed, we initialize some variables and set a timer
            if (self.count == 0):
              
                self.time_val = 0
                self.values = []
                self.x = np.asarray([])
                self.vprom = np.asarray([])
                self.vmax = np.asanyarray([])
                self.vmin = np.asanyarray([])
                self.timer = QTimer()
                self.timer.setInterval(100)
                self.timer.timeout.connect(self.update_plot)
                self.timer.start()
                print("Time (s) \t Voltage (V)")
        else:
            self.stp_acq = False
            try:
                self.micro_board = serial.Serial(str(self.com_port), 
                                                9600,timeout=2)
                
                self.board_nefe = serial.Serial(str(self.com_port_2), 
                                                9600,timeout=2)
            except:
                dlg_board = QMessageBox()
                dlg_board.setWindowTitle("COM Port Error!")
                str_dlg_board ="The board cannot be read "
                str_dlg_board += "or it wasn't selected!"
                dlg_board.setText(str_dlg_board)
                dlg_board.setStandardButtons(QMessageBox.Ok)
                dlg_board.setIcon(QMessageBox.Warning)
                dlg_board.exec_()
                self.micro_board = None
                self.board_nefe = None
            # We check if a COM port has been specified and 
            # if a microboard object has been provided
            if (self.com_port != "" and self.micro_board != None and self.board_nefe != None and self.com_port_2 != ""):
                # We hide some buttons and show others            
                self.btn_start.hide()
                self.btn_stop.show()
                self.btn_save.hide()
                # If this is the first time this code block 
                # is being executed, we initialize some variables and set a timer
                if (self.count == 0):
                    self.time_val = 0
                    self.values = []
                    self.x = np.asarray([])
                    self.vprom = np.asarray([])
                    self.vmax = np.asanyarray([])
                    self.vmin = np.asanyarray([])
                    if (self.micro_board != None):
                        self.micro_board.reset_input_buffer()
                        #init_arduinos(self.micro_board)
                    if (self.board_nefe != None):
                        self.board_nefe.reset_input_buffer()
                        #init_arduinos(self.micro_board)
                    self.timer = QTimer()
                    self.timer.setInterval(100)
                    self.timer.timeout.connect(self.update_plot)
                    self.timer.start()
                    print("Time (s) \t Voltage (V)")
        
    def stop_acquisition(self):
        self.micro_board.write(bytes("salir", 'utf-8'))
        self.stp_acq = True      
        
    
    def update_plot(self):
        if self.adc is not None:
            value = self.adc.read_adc(0, gain=self.GAIN)             
        else:
            value = 1.2
        msg_console = str(self.time_val) + " (s)" + "\t\t "
        msg_console += "{0:0.3f}".format(value) + " (V)"
        print(msg_console)
        self.values.append(str(self.time_val) +","+
                                    str("{0:.3f}".format(value)))
        self.canvas.axes.cla()
        self.x = np.append(self.x,self.time_val)
        self.vprom = np.append(self.vprom,value)
        #self.vmax = np.append(self.vprom,mayores_promedio)

        self.canvas.axes.set_xlabel("Time (s)")
        self.canvas.axes.set_ylabel("Voltage (V)")
        self.canvas.axes.plot(self.x,self.vprom, 'C1--o')
        #self.canvas.axes.plot(self.x,self.vmax,'C2--o')
        self.canvas.draw()
        self.count += 1
        self.time_val += 1
        if (self.count >= self.samples):
                
                self.timer.stop()
                self.count = 0
                self.stp_acq = False
                self.btn_start.show()
                self.btn_stop.hide()
                self.btn_save.show()


    
    def save_file(self):
        self.btn_start.hide()
        self.btn_save.hide()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,
                                    "QFileDialog.getSaveFileName()",""
                        ,"All Files (*);;csv Files (*.csv)", options=options)
        if (fileName):
            file = open(fileName,'w')
            file.write("Time (s),Voltage (V)"+"\n")
            for i in range(len(self.x)-1):
                file.write(str(self.x[i])+","
                               +'{:0.6f}'.format(self.y[i]) +"\n")
            file.write(str(self.x[len(self.x)-1])+","
                           +'{:0.6f}'.format(self.y[len(self.x)-1]))
            file.close()
            
        self.btn_start.show()
        self.btn_save.show()    
        
    
    def closeEvent(self, event):
        try:
            if (self.micro_board != None):
                self.micro_board.close()
        except:
            pass
    
        
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
        
