#!/usr/bin/env python3

import pigpio
import time
from datetime import datetime

sample_frame = [
    0b11000011,     # 01 - May be type of header?
    0b01110111,     # 02 - Temp 22 - 8 (first five bits)
    0b00000000,     # 03 - COOL(00000000 - COOL, 11100000 - HEAT)
    0b00000000,     # 04 - first bit means +0.5 to the Temp
    0b10100000,     # 05 - Fan speed (10100000 means AUTO)
    0b00000000,     # 06 -
    0b00100000,     # 07 - (00100000 - COOL, 10000000 - HEAT)
    0b00000000,     # 08 -
    0b00000000,     # 09 -
    0b00100000,     # 10 - 3-d byte means On|Off
    0b00000000,     # 11 -
    0b00000101,     # 12 - Pressed key code (I believe)
    0b00011111      # 13 - CRC (Modulo 256)
]
IR_PIN = 17

def crc(bytearr):
    bytesum = 0
    for i in range(12):
        bytesum += bytearr[i]
    return bytesum % 256

def printframe(frame):
    for i in range(len(frame)):
        print('{0:02d} {1:08b} {1:02X}'.format(i+1, frame[i]))

def printraw(rawcode):
    for i in range(len(rawcode)):
        print('{: 9d}'.format(rawcode[i]), end="")
        if (i+1) % 6 == 0:
            print("")
    print("")

def settemp(temp, frame):
    temp = temp - 8
    temp = temp << 3
    temp = temp | 7
    frame[1] = temp
    frame[12] = crc(frame)
    return frame

def acoff(frame):
    frame[9] = 0
    frame[12] = crc(frame)
    return frame

def bin2raw(frame):
    rawcode = [9000,4500,600]
    for byte in frame:
        for i in range(8):
            lastbit = byte & 1
            byte >>= 1
            if lastbit:
                rawcode.append(1650)
            else:
                rawcode.append(550)
            rawcode.append(600)
    return rawcode

def addCarrier(code, duration):                 #  when transmit ones we need not just continuosly lighting LED, but pulsing with 38 kHz frequency
    global IR_PIN
    oneCycleTime = 1000000.0 / 38000            # 1000000 microseconds in a second
    onDuration = round(oneCycleTime * 0.5)      # Half a time its on,
    offDuration = round(oneCycleTime * 0.5)     # and a half its off
    totalCycles = round(duration / oneCycleTime)
    totalPulses = totalCycles * 2
    for i in range(totalPulses):
        if i % 2 == 0:
            code.append(pigpio.pulse(0, 1<<IR_PIN, onDuration))
        else:
            code.append(pigpio.pulse(1<<IR_PIN, 0, offDuration))
    return code

def addGap(code, duration):
    code.append(pigpio.pulse(0, 0, duration))
    return code

def makewave(frame):
    global IR_PIN

    rawcode = bin2raw(frame)
    # printraw(rawcode)
    wave = []
    for i in range(len(rawcode)):
        if i % 2 == 0:
            wave = addCarrier(wave, rawcode[i])
        else:
            wave = addGap(wave, rawcode[i])
    wave.append(pigpio.pulse(1<<IR_PIN, 0, 0))
    wave.append(pigpio.pulse(0, 1<<IR_PIN, 0))

    return wave

def sendwave(wave):
    chunklen = 3000
    wavelen = len(wave)
    codechunks = int(wavelen/chunklen)
    wavechain = []

    pi.wave_clear()

    for i in range(codechunks):
        pi.wave_add_generic(wave[:chunklen])
        wavechain.append(pi.wave_create())
        wave = wave[chunklen:]

    pi.wave_add_generic(wave)
    wavechain.append(pi.wave_create())

    pi.set_mode(IR_PIN, pigpio.OUTPUT)
    pi.wave_chain(wavechain)
    print(datetime.now())
#     time.sleep(1)
    while pi.wave_tx_busy():
        time.sleep(0.1);
    pi.wave_tx_stop() # stop waveform
    pi.wave_clear() # clear all waveforms

print(datetime.now())
pi = pigpio.pi()
if not pi.connected:
    print("No connect ot pigpiod!")
    exit()


# frame = settemp(23,sample_frame)
frame = acoff(sample_frame)

wave = makewave(frame)

sendwave(wave)

printframe(frame)










