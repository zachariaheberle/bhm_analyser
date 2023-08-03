# Written by Rohith Saradhy rohithsaradhy@gmail.com
import numpy as np

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

def txt_to_bin(file_name, start_event=0, stop_event=-1):
    """
    Converts the uHTR.txt format into a much more compact binary format
    that can be read much faster. Saved as uHTR4.uhtr/uHTR11.uhtr

    Binary Format: Big Endian -> MSB ... LSB

    How values are stored (values are unsigned unless stated otherwise):
        number of bytes in event -> 16 bits / 2 bytes
        evt_no -> 32 bits / 4 bytes
        bx_no -> 16 bits / 2 bytes
        orbit_no -> 64 bits / 8 bytes
        run_no -> 32 bits / 4 bytes
        ch -> 8 bits / 1 byte
            ch[0:4] -> first ch value ie [3, 1] -> 3
            ch[4:8] -> second ch value ie [3, 1] -> 1
                example: ch = [3, 1] -> b'00110001'
        ampl -> 20*8 bits / 20 bytes (Can be multiple in one event)
        tdc -> 16 bits / 2 bytes (Can be multiple in one event)
            tdc[0:8] -> measured tdc value
            tdc[8:16] -> tdc2 value (signed)
                example: tdc = [5] -> b'00000101 11111111'
                example 2: tdc = [52, 62] -> b'00110100 00111110'

    How values are formatted:
        [number of bytes in event][evt_no][bx_no][orbit_no][run_no]
        [ch][ampl][tdc]...[ch][ampl][tdc] -> repeat for next event 

    """

    def get_ch_byte(ch):
        """
        Converts channel list values into a single byte
        ch[0] is stored in the first 4 bits (big endian)
        ch[1] is store in the last 4 bits (big endian)
        """
        output = (ch[0] << 4) | ch[1]
        return bytes([output])

    new_file_name = file_name[:-3] + "uhtr"
    with open(file_name, "r") as fp, open(new_file_name, "wb") as new_fp:
        for line in fp: # reads lines individually
            if ("---------------------------------------------------------------------------" in line):
                try:
                    evt_no
                except NameError:
                    pass
                else:
                    bytes_to_read = len(bytes_to_write).to_bytes(2, "big")
                    buffer = bytes_to_read + bytes_to_write
                    new_fp.write(buffer)
                finally:
                    continue
            if ("--- START" in line): #parse the event information
                bytes_to_write = bytes()
                evt_stat = list(filter(None, line.split(" ")))
                #print(evt_stat) #debugging
                # collect evt information
                evt_no = (int(evt_stat[3][:-1])).to_bytes(4, "big")
                bx_no = (int(evt_stat[5][:-1])).to_bytes(2, "big")
                orbit_no = (int(evt_stat[7][:-1])).to_bytes(8, "big")
                run_no = (int(evt_stat[9])).to_bytes(4, "big")
                bytes_to_write += evt_no + bx_no + orbit_no + run_no
                fp.readline() # skips a line
    #           print(evt_no,bx_no,orbit_no,run_no) #debugging
            else:
                try:
                    adc_line = line
                    tdc_line = fp.readline() # read the next line in sequence for tdc values
                    if len(tdc_line.strip()) > 0: #if TDC triggered
                        tdc = convert_int(tdc_line[:-1])
                        tdc_bytes = bytes()
                        if len(tdc) <=2:
                            tdc_bytes += tdc[0].to_bytes(1, "big")
                            if len(tdc) == 2:
                                tdc_bytes += tdc[1].to_bytes(1, "big", signed=True)
                            elif len(tdc) == 1:
                                tdc_bytes += (-1).to_bytes(1, "big", signed=True)
                            else:
                                tdc_bytes += (-1).to_bytes(1, "big", signed=True)
                                
                                
                            data = convert_int(adc_line[:-1])
                            ampl = bytes(data[2:][:20])
                            ch = get_ch_byte(data[:2])
                            bytes_to_write += ch + ampl + tdc_bytes


                except:
                    print (f"Failed for evt:{evt_no} ",line[:-1])

        # Make sure to write last event once we hit EOF, since (if "----") event is not guaranteed to be True
        bytes_to_read = len(bytes_to_write).to_bytes(2, "big")
        buffer = bytes_to_read + bytes_to_write
        new_fp.write(buffer)


def parse_bin_file(file_name, start_event=0, stop_event=float("inf")):
    """
    Parses through the custom .uhtr binary file format for the uHTR data.
    See txt_to_bin() for documentation on the file structure of the
    .uhtr file type.
    Returns numpy arrays of TDC, TDC2, AMPL, CH, BX, ORBIT, and RUN
    """

    def get_ch_list(ch_byte):
        """
        Get channel list values from the channel byte
        ch[0] is stored in the first 4 bits of ch_byte (big endian)
        ch[1] is store in the last 4 bits of ch_byte (big endian)
        """
        return [(ch_byte & 0b11110000) >> 4, (ch_byte & 0b1111)]

    TDC = []  # Time of the pulse in the 40 MHz clock. 0 to 25 ns in steps of 0.5 ns.
    TDC2 = [] # if the threhold was crossed prior to recording
    BX = []   #  Bunch crossing value: ranges from zero to 3564.
    AMPL = [] # Pulse height of signal.
    CH = []   # channel number, stored as a list of two numbers, 20 different values
    ORBIT = []  # Orbit counter which tells you when the event occured.
    RUN_NO = [] # Number of the data collection run.
    with open(file_name, "rb") as fp:
        eof = False
        while eof == False:
            bytes_to_read = int.from_bytes(fp.read(2), "big")
            if not bytes_to_read:
                eof = True
                break
            event_data = fp.read(bytes_to_read)

            evt_no = int.from_bytes(event_data[0:4], 'big')
            bx_no = int.from_bytes(event_data[4:6], 'big')
            orbit_no = int.from_bytes(event_data[6:14], 'big')
            run_no = int.from_bytes(event_data[14:18], 'big')

            if evt_no >= start_event:
                if evt_no <= stop_event:
                    for byte_pos in range(18, bytes_to_read - 18, 23):
                        ch = get_ch_list(event_data[byte_pos])
                        adc = np.asarray(bytearray(event_data[byte_pos+1:byte_pos+21]))
                        tdc = event_data[byte_pos+21]
                        tdc2 = event_data[byte_pos+22]
                        tdc2 = -(tdc2 & 0b10000000) + (tdc2 & 0b01111111) # Convert unsigned int to a signed int

                        CH.append(ch)
                        AMPL.append(adc)
                        TDC.append(tdc)
                        TDC2.append(tdc2)
                        BX.append(bx_no)
                        ORBIT.append(orbit_no)
                        RUN_NO.append(run_no)
                else:
                    eof = True
                    break

        

    return np.asarray(CH, dtype=np.int32),np.asarray(AMPL, dtype=np.int32),np.asarray(TDC, dtype=np.int32),np.asarray(TDC2, dtype=np.int32),np.asarray(BX, dtype=np.int32),np.asarray(ORBIT, dtype=np.int64),np.asarray(RUN_NO, dtype=np.int32)
    # Note: ORBIT must be kept as a int64, otherwise rate plots may fail from integer overflow

    


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
