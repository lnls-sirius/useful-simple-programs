#!/usr/bin/python
# -*- coding: utf-8 -*-

# 4h-dose-pv.py

# This program provides an EPICS PV that corresponds to the 4h radiation dose associated to any
# radiation probe at Sirius. The program receives two arguments. One is the name of the dose rate
# input PV used for calculation. The other is the name of the 4h dose PV.
#
# Input PV should be an ai EPICS record, with the MDEL field set to -1.

# Python modules required: pcaspy and pyepics.
# Tested with Python 2.7.12, pcaspy 0.7.1 and pyepics 3.3.1.

# Necessary modules

from epics import camonitor
from pcaspy import Driver, SimpleServer
from Queue import Queue
import sys
import threading

# Driver for the integral PV

class IntegralDriver(Driver):

    # Constructor

    def __init__(self, input_pv_name, output_pv_name):

        Driver.__init__(self)

        self.input_pv_name = input_pv_name
        self.output_pv_name = output_pv_name

        self.data_buffer = []

        self.queue = Queue()

        self.process_thread = threading.Thread(target = self.processThread)
        self.process_thread.setDaemon(True)
        self.process_thread.start()

        camonitor(self.input_pv_name, callback = self.enqueueData)

    # The following function adds new data to the program's queue

    def enqueueData(self, **kwargs):
        self.queue.put({ "value" : kwargs["value"], "timestamp" : kwargs["timestamp"] })

    # Thread where the radiation dose is calculated

    def processThread(self):

        # Nested function for integral portion calculation. This function implements the trapezoidal
        # rule.

        def integral_portion(previous_data, data):
            time_difference = (data["timestamp"] - previous_data["timestamp"]) / 3600.0
            return((data["value"] + previous_data["value"]) * time_difference * 0.5)

        # Queue processing

        while (True):

            # The next line blocks the processing until it is time to update the dose PV value

            queue_item = self.queue.get(block = True)

            # This adds new data to the buffer

            if (self.data_buffer == []):
                self.data_buffer.append(queue_item)
                continue
            else:
                if (queue_item["timestamp"] <= self.data_buffer[-1]["timestamp"]):
                    continue
                else:
                    self.data_buffer.append(queue_item)

            # If there is more than one value/timestamp pair in the buffer and also new data has
            # arrived, then some steps should be performed.

            new_integral_value = self.getParam(self.output_pv_name)
            new_integral_value += integral_portion(self.data_buffer[-2], self.data_buffer[-1])
            while (self.data_buffer[-1]["timestamp"] - self.data_buffer[1]["timestamp"] > 14400.0):
                new_integral_value -= integral_portion(self.data_buffer[0], self.data_buffer[1])
                self.data_buffer = self.data_buffer[1:]

            # Here the value of the integral PV is updated and notified to the connected clients

            self.setParam(self.output_pv_name, new_integral_value)
            self.updatePVs()

# Main routine

if (__name__ == "__main__"):

    # Input and output PV names are defined through program arguments

    input_pv_name = sys.argv[1]
    output_pv_name = sys.argv[2]

    # This program provides only one PV

    PVs = { output_pv_name : { "type" : "float",
                               "prec" : 3,
                               "unit" : "uSv",
                               "low" : -0.1,
                               "high" : 1.5,
                               "lolo" : -0.1,
                               "hihi" : 2.0 } }

    # Channel Access server initialization

    CA_server = SimpleServer()
    CA_server.createPV("", PVs)
    driver = IntegralDriver(input_pv_name, output_pv_name)

    # Loop

    while (True):
        CA_server.process(0.1)
