# Written by Rohith Saradhy rohithsaradhy@gmail.com and Zachariah Eberle zachariaheberle@gmail.com
import numpy as np
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
import time

def convert_int(x,extract_pos=False): # splits a single string to int
#     print(x.split(" "))
    if extract_pos:
        print(x.split(" "))
        return [int(i) for i in list(filter(None,x.split(" ")))],
    else:
        return [int(i) for i in list(filter(None,x.split(" ")))]

def parse_text_file(file_name, start_event=0, stop_event=-1): #expects a certain type of data, proceed with caution
    """
    Function to unpack the uHTR.txt data files
    returns numpy arrays of TDC, AMPL, CH, BX, ORBIT, RUN
    """
    if (stop_event == -1): stop_flag = False #disable stop event
    else: stop_flag = True #enable stop event
    evt_status = ""
    TDC = []  # Time of the pulse in the 40 MHz clock. 0 to 25 ns in steps of 0.5 ns.
    TDC2 = [] # if the threhold was crossed prior to recording
    BX = []   #  Bunch crossing is ranges from zero to 3564.
    AMPL = [] # Pulse height of signal.
    CH = []   # channel number 1 to 20
    ORBIT = []  # Orbit counter which tells you where in the fill (run?) the event occured.
    RUN_NO = [] # Number of the data collection run.
    with open(file_name, "r") as fp:
        for line in fp: # reads lines individually
            if ("---------------------------------------------------------------------------" in line):
                continue
            if ("--- START" in line): #parse the event information
                evt_stat = list(filter(None, line.split(" ")))
                #print(evt_stat) #debugging
                # collect evt information
                evt_no = int(evt_stat[3][:-1])
                bx_no = int(evt_stat[5][:-1])
                orbit_no = int(evt_stat[7][:-1])
                run_no = int(evt_stat[9])
                fp.readline() # skips a line
    #           print(evt_no,bx_no,orbit_no,run_no) #debugging
            else:
                if (evt_no >= start_event): # start from event number 
                    if ((evt_no > stop_event)&(stop_flag)): break # break if the events exceed stop event
    #                 data = convert_int(l[i]) #convert strings to integer list
                    try:
                        adc_line = line
                        tdc_line = fp.readline() # read the next line in sequence for tdc values
                        if len(tdc_line.strip()) > 0: #if TDC triggered
                            tdc = convert_int(tdc_line[:-1])
                            if len(tdc) <=2:
                                TDC.append(tdc[0])
                                if len(tdc) == 2:
                                    TDC2.append(tdc[1])
                                elif len(tdc) == 1:
                                    TDC2.append(-1)
                                else:
                                    TDC2.append(-1)
    #                                 TDC2.append(tdc[0])
                                    
                                    
                                data = convert_int(adc_line[:-1])
                                AMPL.append(np.asarray(data[2:])[:20])
                                CH.append(data[:2])
                                BX.append(bx_no)
                                ORBIT.append(orbit_no)
                                RUN_NO.append(run_no)
    #                         elif len(tdc) >2:
    #                             print (AMPL[-1])
    #                         TDC2.append(tdc[1])


                    except:
                        print (f"Failed for evt:{evt_no} ",line[:-1])
    #                     print (f"Failed for evt:{evt_no} ",l[i+1][:-1])

        return np.asarray(CH),np.asarray(AMPL),np.asarray(TDC),np.asarray(TDC2),np.asarray(BX),np.asarray(ORBIT, dtype=np.int64),np.asarray(RUN_NO)
    # Note: ORBIT must be kept as a int64, otherwise rate plots may fail from integer overflow, since the default is np.int32

def txt_to_bin(file_name):
    """
    Converts the uHTR.txt format into a much more compact binary format
    that can be read much faster. Saved as uHTR4.uhtr/uHTR11.uhtr

    Binary Format: Big Endian -> MSB ... LSB

    How values are stored (values are unsigned unless stated otherwise):
        version number -> 8 bits / 1 byte (This is in the event that the file format changes)
        total number of events -> 32 bits / 4 bytes
        evt_no -> 32 bits / 4 bytes
        bx_no -> 16 bits / 2 bytes
        orbit_no -> 64 bits / 8 bytes
        run_no -> 32 bits / 4 bytes
        ch -> 16 bits / 2 bytes
            One byte for each value in ch
        ampl -> 20*8 bits / 20 bytes
        tdc -> 16 bits / 2 bytes
            tdc[0:8] -> measured tdc value
            tdc[8:16] -> tdc2 value (signed)
                example: tdc = [5] -> b'00000101 11111111'
                example 2: tdc = [52, 62] -> b'00110100 00111110'

    How values are formatted:
        [version number][total number of events][evt_no array][bx_no array][orbit_no array]
        [run_no array][ch array][ampl array][tdc array] -> all arrays are stored sequentially
        right next to each other, as they have the same length.
    """

    VERSION = bytes([1])

    EVT = bytearray() # Event number, may or may not be useful to keep track of
    TDC = bytearray()  # Time of the pulse in the 40 MHz clock. 0 to 25 ns in steps of 0.5 ns.
    TDC2 = bytearray() # if the threhold was crossed prior to recording
    BX = bytearray()   #  Bunch crossing is ranges from zero to 3564.
    AMPL = bytearray() # Pulse height of signal.
    CH = bytearray()   # channel number 1 to 20
    ORBIT = bytearray()  # Orbit counter which tells you where in the fill (run?) the event occured.
    RUN_NO = bytearray() # Number of the data collection run.

    new_file_name = file_name[:-3] + "uhtr"
    with open(file_name, "r") as fp:
        for line in fp: # reads lines individually
            if ("---------------------------------------------------------------------------" in line):
                continue
            if ("--- START" in line): #parse the event information
                evt_stat = list(filter(None, line.split(" ")))
                #print(evt_stat) #debugging
                # collect evt information
                evt_bytes = (int(evt_stat[3][:-1])).to_bytes(4, "big")
                bx_bytes = (int(evt_stat[5][:-1])).to_bytes(2, "big")
                orbit_bytes = (int(evt_stat[7][:-1])).to_bytes(8, "big")
                run_bytes = (int(evt_stat[9])).to_bytes(4, "big")
                fp.readline() # skips a line
    #           print(evt_no,bx_no,orbit_no,run_no) #debugging
            else:
                try:
                    adc_line = line
                    tdc_line = fp.readline() # read the next line in sequence for tdc values
                    if len(tdc_line.strip()) > 0: #if TDC triggered
                        tdc = convert_int(tdc_line[:-1])
                        if len(tdc) <=2:
                            tdc_bytes = tdc[0].to_bytes(1, "big")
                            if len(tdc) == 2:
                                tdc2_bytes = tdc[1].to_bytes(1, "big", signed=True)
                            elif len(tdc) == 1:
                                tdc2_bytes = (-1).to_bytes(1, "big", signed=True)
                            else:
                                tdc2_bytes = (-1).to_bytes(1, "big", signed=True)
                                
                                
                            data = convert_int(adc_line[:-1])
                            ampl_bytes = bytes(data[2:][:20])
                            ch_bytes = bytes(data[:2])

                            EVT.extend(evt_bytes)
                            TDC.extend(tdc_bytes)
                            TDC2.extend(tdc2_bytes)
                            BX.extend(bx_bytes)
                            AMPL.extend(ampl_bytes)
                            CH.extend(ch_bytes)
                            ORBIT.extend(orbit_bytes)
                            RUN_NO.extend(run_bytes)

                except:
                    print (f"Failed for evt:{int.from_bytes(evt_bytes, 'big')} ",line[:-1])


    with open(new_file_name, "wb") as fp:
        total_evts = len(TDC).to_bytes(4, "big") # Since TDC length is 1 bytes, its length represents all array lengths
        buffer = VERSION + total_evts + bytes(EVT) + bytes(TDC) + bytes(TDC2)\
              + bytes(BX) + bytes(AMPL) + bytes(CH) + bytes(ORBIT) + bytes(RUN_NO)
        # The order in which these are saved is VERY important

        # print(f"Event length: {len(EVT) // 4}") debug
        # print(f"TDC length: {len(TDC)}")
        # print(f"TDC2 length: {len(TDC2)}")
        # print(f"BX length: {len(BX) // 2}")
        # print(f"Ampl length: {len(AMPL) // 20}")
        # print(f"Channel length: {len(CH)}")
        # print(f"Orbit length: {len(ORBIT) // 8}")
        # print(f"Run number: {len(RUN_NO) // 4}")

        if (len(EVT) // 4) == (len(TDC)) == (len(TDC2)) == (len(BX) // 2) == (len(AMPL) // 20)\
            == (len(CH) // 2) == (len(ORBIT) // 8) == (len(RUN_NO) // 4):
            # Really ugly looking sanity check to ensure all arrays are the same length
            fp.write(buffer)
        else:
            raise AssertionError("Array lengths do not match!")

def parse_bin_file(file_name):
    """
    Parses through the custom .uhtr binary file format for the uHTR data.
    See txt_to_bin() for documentation on the file structure of the
    .uhtr file type.
    Returns numpy arrays of TDC, TDC2, AMPL, CH, BX, ORBIT, and RUN
    """
    def v1():
        """
        Parses version 1 of the .uhtr file format
        """
        def get_offsets(data_bytes):
            """
            Returns a list of the byte position of the start of all
            arrays in the file
            [4, 1, 1, 2, 20, 2, 8, 4] represents the order and byte length
            of an individual element in their respective arrays
            """
            offset_list = [5]
            bytes_read = 5
            array_len = int.from_bytes(data_bytes[1:5], "big")
            for byte_len in [4, 1, 1, 2, 20, 2, 8, 4]: # byte lengths of each array, order matters
                offset_list.append(bytes_read + byte_len * array_len)
                bytes_read += byte_len * array_len
            return offset_list, array_len
        
        offset, array_len = get_offsets(file_data)

        uint16 = np.dtype(np.uint16).newbyteorder(">") # Force byte order for multi-byte values
        uint32 = np.dtype(np.uint32).newbyteorder(">")
        uint64 = np.dtype(np.uint64).newbyteorder(">")
        
        #evt = np.ndarray(shape=(array_len,), dtype=np.uint32,    buffer=file_data[offset[0]:offset[1]])
        tdc = np.ndarray(shape=(array_len,), dtype=np.uint8,     buffer=file_data[offset[1]:offset[2]])
        tdc2 = np.ndarray(shape=(array_len,), dtype=np.int8,     buffer=file_data[offset[2]:offset[3]])
        bx = np.ndarray(shape=(array_len,), dtype=uint16,        buffer=file_data[offset[3]:offset[4]])
        ampl = np.ndarray(shape=(array_len, 20), dtype=np.uint8, buffer=file_data[offset[4]:offset[5]])
        ch = np.ndarray(shape=(array_len, 2), dtype=np.uint8,    buffer=file_data[offset[5]:offset[6]])
        orbit = np.ndarray(shape=(array_len,), dtype=uint64,     buffer=file_data[offset[6]:offset[7]])
        run = np.ndarray(shape=(array_len,), dtype=uint32,       buffer=file_data[offset[7]:offset[8]])

        return ch, ampl, tdc, tdc2, bx, orbit, run

    with open(file_name, "rb") as fp:
        file_data = fp.read()
    
    version = file_data[0]

    if version == 1:
        ch, ampl, tdc, tdc2, bx, orbit, run = v1()
    else:
        raise ValueError(f"Version number {version} does not exist.")

    return ch, ampl, tdc, tdc2, bx, orbit, run

    


def parse_text_file_old(file_name, start_event=0, stop_event=-1): #expects a certain type of data, proceed with caution
# funtion to unpack text file data.
# returns np arrays with TDC, AMPL, CH, BX, Orbit, Run
#   
    if (stop_event == -1): stop_flag = False #disable stop event
    else: stop_flag = True #enable stop event
    with open(file_name) as f: #loading file into memory
        lines = f.readlines()  
    evt_status = ""
    data = []
    l = lines # renaming so it is easier to type
    i=0
    TDC = []  # Time of the pulse in the 40 MHz clock. 0 to 25 ns in steps of 0.5 ns.
    TDC2 = [] # if the threhold was crossed prior to recording
    BX = []   #  Bunch crossing is ranges from zero to 3564.
    AMPL = [] # Pulse height of signal.
    CH = []   # channel number 1 to 20
    ORBIT = []  # Orbit counter which tells you where in the fill (run?) the event occured.
    RUN_NO = [] # Number of the data collection run.
    while(i < len(l)):
        if ("---------------------------------------------------------------------------" in l[i]):
            i = i + 1 #skip one line
            continue
        if ("--- START" in l[i]): #parse the event information
            evt_stat = list(filter(None,l[i].split(" ")))
            #print(evt_stat) #debugging
            #collect evt information
            evt_no = int(evt_stat[3][:-1])
            bx_no = int(evt_stat[5][:-1])
            orbit_no = int(evt_stat[7][:-1])
            run_no = int(evt_stat[9])
            # print(run_no,evt_stat[9])
            # break
            i = i+1 #skip one line
#             print(evt_no,bx_no,orbit_no,run_no) #debugging
        else:
            if (evt_no >= start_event): # start from event number 
                if ((evt_no > stop_event)&(stop_flag)): break # break if the events exceed stop event
#                 data = convert_int(l[i]) #convert strings to integer list
                try:
                    if ( len(l[i+1].strip()) > 0): #if TDC triggered
                        tdc = convert_int(l[i+1][:-1])
                        if len(tdc) <=2:
                            TDC.append(tdc[0])
                            if len(tdc) == 2:
                                TDC2.append(tdc[1])
                            elif len(tdc) == 1:
                                TDC2.append(-1)
                            else:
                                TDC2.append(-1)
#                                 TDC2.append(tdc[0])
                                
                                
                            data = convert_int(l[i][:-1])
                            AMPL.append(np.asarray(data[2:])[:20])
                            CH.append(data[:2])
                            BX.append(bx_no)
                            ORBIT.append(orbit_no)
                            RUN_NO.append(run_no)
#                         elif len(tdc) >2:
#                             print (AMPL[-1])
#                         TDC2.append(tdc[1])


                except:
                    print (f"Failed for evt:{evt_no} ",l[i][:-1])
#                     print (f"Failed for evt:{evt_no} ",l[i+1][:-1])


            i = i+2 #skip lines
    return np.asarray(CH),np.asarray(AMPL),np.asarray(TDC),np.asarray(TDC2),np.asarray(BX),np.asarray(ORBIT, dtype=np.int64),np.asarray(RUN_NO)
# Note: ORBIT must be kept as a int64, otherwise rate plots may fail from integer overflow, since the default is np.int32
