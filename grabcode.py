#!/usr/bin/env python3
import time
import pigpio
import actools as ac

in_code = False
code_timeout = 10
prevtick = 0
rawcode = []

# Some of Zanussi Paradiso AC frame
sample_frame = [
    0b11000011,     # 01 - May be type of header?
    0b01110111,     # 02 - Temp 22 - 8 (first four bits), last three bits - swing (000 - off, 111 - on)
    0b00000000,     # 03 - COOL(00000000 - COOL, 11100000 - HEAT)
    0b00000000,     # 04 - last bit means +0.5 to the Temp
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

def raw2bin(rawcode):
    byte = 0
    byteptr = 0
    bytearr = []
    for i in range(len(rawcode)):
        if i < 3:			#Ignore first three pulses
            continue
        if i % 2 == 0:		#Ignore gap pulses
            continue
        if rawcode[i] > 900:	#All pulses that are above 900 - interpret as '1'
            byte = byte | (1 << byteptr)

        byteptr += 1
        if byteptr > 7:
            bytearr.append(byte)
            byteptr = byte = 0

    if len(bytearr) < 2:
        print("Wrong code!")
        return False

    for i in range(len(bytearr)):
        print('{0:02d} {1:08b} {1:02X} {1:d}'.format(i+1, bytearr[i]))

    print('-----')
    for i in range(len(bytearr)):
    	print('{:02X}'.format(bytearr[i]),end=" ")
    print('')
    print('-----')
    print('CRC: {0:08b} {0:02X}'.format(crc(bytearr)))
    print('')
    return bytearr

def crc(bytearr):
    if len(bytearr) == 13:
        return crcZanussi(bytearr)
    if len(bytearr) == 16:
        return crcFujitsu(bytearr)
    return False

def crcZanussi(bytearr):
    bytesum = 0
    for i in range(len(bytearr)-1):
        bytesum += bytearr[i]
    return bytesum % 256

def crcFujitsu(bytearr):
    if len(bytearr) < 16:
        return crc(bytearr)
    bytesum = 0
    bytes = bytearr[8:15]

# For testing purpose:
    for i in range(len(bytes)):
#         print('{:08b} '.format(bytes[i]),end=" ")
        bytesum += bytes[i]
#     print("---")
    return (208 - bytesum) % 256

def printraw(rawcode):
#     signal = ac.ACSignal(rawcode = rawcode)
#     signal.setTemperature(31)
#     signal.printRaw()

    for i in range(len(rawcode)):
        print('{: 9d}'.format(rawcode[i]), end="")
        if (i+1) % 6 == 0:
            print("")
    print("")

def cbf(gpio, level, tick):

    global pi, in_code, code_timeout, prevtick, rawcode

    if level != pigpio.TIMEOUT:

        pi.set_watchdog(gpio, code_timeout)

        if in_code == False:
            in_code = True

        else:
            tickDiff = pigpio.tickDiff(prevtick,tick)
            if tickDiff > code_timeout*1000:        # fix situation, when two frames comes nearly (buttons pressing very fast)
#                 printraw(rawcode)
                rawcode = []
            else:
                rawcode.append(tickDiff)

        prevtick = tick

    else:
        pi.set_watchdog(gpio, 0)
        if in_code:
            in_code = False
            raw2bin(rawcode)
#             printraw(rawcode)
            rawcode = []

pi = pigpio.pi()
if not pi.connected:
    print("No connect ot pigpiod!")
    exit()

pi.set_mode(18, pigpio.INPUT)

cb = pi.callback(18, pigpio.EITHER_EDGE, cbf)

time.sleep(120)

pi.stop()
