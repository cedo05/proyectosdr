#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Transmisor de emergencia
# Author: Cesar Diaz & Lisa Garcia
# Generated: Sat Jun 22 16:10:26 2019
##################################################

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt5 import Qt, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtGui import QIcon
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import sys
import threading
import time
import os
import shutil
from gnuradio import qtgui
import mysql.connector
from mysql.connector import Error
from datetime import date, datetime
import pyaudio
import wave
from ftplib import FTP
import fileinput

# Funcion para insertar tupla al iniciar transmision
def insert_onState(id_equipo, fecha_encendido, hora_encendido):
    try:
        #Abriendo conexion con la base de datos
        connection = mysql.connector.connect(host='localhost',
                             database= 'dbproyectosdr',
                             user='root',
                             password='password')
        cursor = connection.cursor(prepared=True)

        #Query para insertar tupla a tabla estado
        sql_insert_query = """ INSERT INTO `estado`
                          (`id_equipo`, `fecha_encendido`, `hora_encendido`) VALUES (%s,%s,%s)"""
        insert_tuple = (id_equipo, fecha_encendido, hora_encendido)
        cursor.execute(sql_insert_query, insert_tuple)
        connection.commit()
        print ("Informacion insertada con exito")
    except mysql.connector.Error as error :
        connection.rollback()
        print("Error al insertar la informacion: {}".format(error))
    finally:
        #Cerrando conexion con la base de datos.
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            print("Conexion terminada")

# Funcion para insertar tupla al terminar transmision
def insert_offState(id_equipo, fecha_apagado, hora_apagado):
    try:
        #Abriendo conexion con la base de datos
        connection = mysql.connector.connect(host='localhost',
                             database= 'dbproyectosdr',
                             user='root',
                             password='password')
        cursor = connection.cursor(prepared=True)

        #Query para insertar tupla a tabla estado
        sql_insert_query = """ UPDATE `estado` SET
                          fecha_apagado = %s, hora_apagado = %s WHERE id_equipo = %s ORDER BY id_estado DESC LIMIT 1"""
        insert_tuple = (fecha_apagado, hora_apagado, id_equipo)
        cursor.execute(sql_insert_query, insert_tuple)
        connection.commit()
        print ("Informacion insertada con exito")
    except mysql.connector.Error as error :
        connection.rollback()
        print("Error al insertar la informacion: {}".format(error))
    finally:
        #Cerrando conexion con la base de datos.
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            print("Conexion terminada")

# Funcion para subir archivos al servidor FTP
def UploadFTP(host, port, user, password, foldername, filename, newfilename):
    #Abriendo conexion con el servidor FTP
    ftp = FTP()
    ftp.connect(host, port)
    ftp.login(user, password)
    
    # Seleccion de directorio
    if foldername in ftp.nlst():
        ftp.cwd('/%s' % foldername)
    else:
        ftp.mkd('/%s' % foldername)
        ftp.cwd('/%s' % foldername)

    # Subida de archivo   
    fp = open(filename, 'rb')
    ftp.storbinary('STOR %s' % os.path.basename(filename), fp)
    fp.close()
    
    # Renombrar archivo
    ftp.rename(filename, newfilename)
    # Finalizar sesion
    ftp.quit()

# Clase del transmisor 
class Transmisor_de_emergencia(gr.top_block, Qt.QWidget):
    # Funcion para inicializar los bloques del tranmisor.
    def __init__(self):
        gr.top_block.__init__(self, "Transmisor_de_emergencia")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Transmisor_de_emergencia")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)            

        # Funcion para iniciar la transmision
        def on_click_start():
            self.start()
            self.buttonStart.setEnabled(False)
            self.buttonStop.setEnabled(True)
            self.buttonRecord.setEnabled(False)
            self.buttonDefault.setEnabled(False)
            insert_onState(self.id_equipo, date.today(), datetime.now().time())

        # Funcion para detener la transmision
        def on_click_stop():
            self.stop()
            self.wait()
            self.buttonStart.setEnabled(True)
            self.buttonStop.setEnabled(False)
            self.buttonRecord.setEnabled(True)
            self.buttonDefault.setEnabled(True)
            insert_offState(self.id_equipo, date.today(), datetime.now().time())

        # Funcion para seleccionar audio base
        def defaultAudio():
            try:
                shutil.copyfile('base.wav', 'audio.wav')
                print 'Archivo copiado'
            except IOError as e:
                print 'No se pudo copiar'

        # Funcion para grabar audio
        def audioRecord():
            chunk = 1024  # Grabar en bloques de 1024 muestras
            sample_format = pyaudio.paInt16  # 16 bits por muestras
            channels = 2
            fs = 44100  # Grabar a 44100 muestras por segundo 
            seconds = self.time_rec
            filename = "audio.wav"

            p = pyaudio.PyAudio()  # Creacion de interfaz a PortAudio

            print('Recording')

            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input=True)

            frames = []  

            # Guardar datos en trozos de 3 segundos
            for i in range(0, int(fs / chunk * seconds)):
                data = stream.read(chunk)
                frames.append(data)

            # Parar y cerrar flujo de audio
            stream.stop_stream()
            stream.close()
            # Terminar la interfaz de PortAudio
            p.terminate()

            print('Finished recording')

            # Guardar la data como un archivo .wav
            wf = wave.open(filename, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
            wf.close()

            # Subir archivo grabado
            UploadFTP(self.HostFTP, self.PortFTP, self.UserFTP, self.PassFTP, str(self.id_equipo), "audio.wav", '%s_%s_%s_%s.wav' % (self.id_equipo,self.id_ambulancia, date.today(),datetime.now().time()))

        # Inicializacion de los botones en la GUI
        self.buttonStart = QPushButton('Iniciar', self)
        self.buttonStart.clicked.connect(on_click_start)
        self.buttonStop = QPushButton('Detener', self)
        self.buttonStop.move(100, 0)
        self.buttonStop.setEnabled(False)
        self.buttonStop.clicked.connect(on_click_stop)
        self.buttonRecord = QPushButton('Grabar', self)
        self.buttonRecord.move(0,50)
        self.buttonRecord.clicked.connect(audioRecord)
        self.buttonDefault = QPushButton('Por Defecto', self)
        self.buttonDefault.move(100,50)
        self.buttonDefault.clicked.connect(defaultAudio)

        self.settings = Qt.QSettings("GNU Radio", "Transmisor_de_emergencia")

        if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
            self.restoreGeometry(self.settings.value("geometry").toByteArray())
        else:
            self.restoreGeometry(self.settings.value("geometry", type=QtCore.QByteArray))

        ##################################################
        # Variables
        ##################################################
        self.variable_function_probe_0 = variable_function_probe_0 = 0
        self.samp_rate = samp_rate = 250e3
        self.Freq = Freq = 88.5e6
        self.id_equipo = 1
        self.id_ambulancia = 1
        self.time_rec = 1        
        self.HostFTP = '127.0.0.1'
        self.PortFTP = 21
        self.UserFTP = 'proyectosdr'
        self.PassFTP = 'proyectosdr'

        ##################################################
        # Bloques
        ##################################################

        # Funcion para barrido de frecuencia
        def _variable_function_probe_0_probe():
            while True:
                val = self.get_Freq()
                print val
                if val == 107500000:
                    self.set_Freq(88500000)
                else:
                    self.set_Freq(val+1000000)
                try:
                    self.set_variable_function_probe_0(val)
                except AttributeError:
                    pass
                time.sleep(1.0 / (1))
        _variable_function_probe_0_thread = threading.Thread(target=_variable_function_probe_0_probe)
        _variable_function_probe_0_thread.daemon = True
        _variable_function_probe_0_thread.start()


        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_sink_0.set_samp_rate(1.28e6)
        self.uhd_usrp_sink_0.set_center_freq(Freq, 0)
        self.uhd_usrp_sink_0.set_gain(20, 0)
        self.uhd_usrp_sink_0.set_antenna('TX/RX', 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=4,
                decimation=1,
                taps=None,
                fractional_bw=None,
        )
        self.low_pass_filter_0 = filter.fir_filter_fff(1, firdes.low_pass(
        	1, 44.1e3, 15e3, 1e3, firdes.WIN_HAMMING, 6.76))
        self.blocks_wavfile_source_0 = blocks.wavfile_source('/home/proyectosdr/proyectosdr/audio.wav', True)
        self.blocks_multiply_xx_3 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_2 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_1 = blocks.multiply_vcc(1)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((200e-3, ))
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_wfm_tx_0 = analog.wfm_tx(
        	audio_rate=44100,
        	quad_rate=44100*7,
        	tau=75e-6,
        	max_dev=75e3,
        	fh=-1.0,
        )
        self.analog_sig_source_x_3 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 400e3, 1, 0)
        self.analog_sig_source_x_2 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, -200e3, 1, 0)
        self.analog_sig_source_x_1 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 200e3, 1, 0)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, -400e3, 1, 0)
        self.analog_fm_preemph_0 = analog.fm_preemph(fs=54e3, tau=75e-6, fh=-1.0)

        ##################################################
        # Conexiones
        ##################################################
        
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_2, 1))
        self.connect((self.analog_sig_source_x_1, 0), (self.blocks_multiply_xx_1, 1))
        self.connect((self.analog_sig_source_x_2, 0), (self.blocks_multiply_xx_3, 1))
        self.connect((self.analog_sig_source_x_3, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.analog_wfm_tx_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_xx_1, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_xx_2, 0), (self.blocks_add_xx_0, 3))
        self.connect((self.blocks_multiply_xx_3, 0), (self.blocks_add_xx_0, 2))
        self.connect((self.blocks_wavfile_source_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_wfm_tx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_multiply_xx_1, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_multiply_xx_2, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_multiply_xx_3, 0))

    # Funcion para finalizar el programa
    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "Transmisor_de_emergencia")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    # Getters and setters
    def get_variable_function_probe_0(self):
        return self.variable_function_probe_0

    def set_variable_function_probe_0(self, variable_function_probe_0):
        self.variable_function_probe_0 = variable_function_probe_0

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.analog_sig_source_x_3.set_sampling_freq(self.samp_rate)
        self.analog_sig_source_x_2.set_sampling_freq(self.samp_rate)
        self.analog_sig_source_x_1.set_sampling_freq(self.samp_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_Freq(self):
        return self.Freq

    def set_Freq(self, Freq):
        self.Freq = Freq
        self.uhd_usrp_sink_0.set_center_freq(self.Freq, 0)

# Programa principal
def main(top_block_cls=Transmisor_de_emergencia, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    # Inicializacion del programa
    tb = top_block_cls()
    tb.show()
    # Funcion para detener el programa
    def quitting():
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()

if __name__ == '__main__':
    main()
