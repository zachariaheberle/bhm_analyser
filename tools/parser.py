# Written by Rohith Saradhy rohithsaradhy@gmail.com
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
        if len(bytes_to_write) >= 41:
            bytes_to_read = len(bytes_to_write).to_bytes(2, "big")
            buffer = bytes_to_read + bytes_to_write
            new_fp.write(buffer)

def _parse_bin_sector(array_len, offsets):
    """
    Parses through a section of the file data, used for multiprocessing,
    do not call outside of parse_bin_file.
    """
    start = time.time()
    def get_ch_list(ch_byte):
        """
        Get channel list values from the channel byte
        ch[0] is stored in the first 4 bits of ch_byte (big endian)
        ch[1] is store in the last 4 bits of ch_byte (big endian)
        """
        return bytes([(ch_byte & 0b11110000) >> 4, (ch_byte & 0b1111)])
    
    TDC = SharedMemory(name="TDC")
    TDC2 = SharedMemory(name="TDC2")
    BX = SharedMemory(name="BX")
    AMPL = SharedMemory(name="AMPL")
    CH = SharedMemory(name="CH")
    ORBIT = SharedMemory(name="ORBIT")
    RUN_NO = SharedMemory(name="RUN_NO")
    DATA = SharedMemory(name="DATA")

    # Modifying data types to get correct byte order in np.frombuffer()
    uint16 = np.dtype(np.uint16).newbyteorder(">")
    uint32 = np.dtype(np.uint32).newbyteorder(">")
    uint64 = np.dtype(np.uint64).newbyteorder(">")

    data = DATA.buf

    tdc = np.ndarray(shape=(array_len,), dtype=np.uint8, buffer=TDC.buf)
    tdc2 = np.ndarray(shape=(array_len,), dtype=np.int8, buffer=TDC2.buf)
    bx = np.ndarray(shape=(array_len,), dtype=np.uint16, buffer=BX.buf)
    ampl = np.ndarray(shape=(array_len, 20), dtype=np.uint8, buffer=AMPL.buf)
    ch = np.ndarray(shape=(array_len, 2), dtype=np.uint8, buffer=CH.buf)
    orbit = np.ndarray(shape=(array_len,), dtype=np.uint64, buffer=ORBIT.buf)
    run = np.ndarray(shape=(array_len,), dtype=np.uint32, buffer=RUN_NO.buf)
    
    for array_index, offset in offsets:
        bytes_to_read = int.from_bytes(data[offset:offset+2], "big")
        event_data = data[offset+2:offset+2+bytes_to_read]

        evt_no = event_data[0:4]
        bx_no = event_data[4:6]
        orbit_no = event_data[6:14]
        run_no = event_data[14:18]

        for i, byte_pos in enumerate(range(18, bytes_to_read - 18, 23)):
            ch_array = get_ch_list(event_data[byte_pos])
            adc_array = event_data[byte_pos+1:byte_pos+21]
            tdc_no = event_data[byte_pos+21]
            tdc2_no = event_data[byte_pos+22]

            tdc[array_index+i] = tdc_no
            tdc2[array_index+i] = tdc2_no
            bx[array_index+i] = np.frombuffer(bx_no, dtype=uint16)
            ampl[array_index+i] = np.frombuffer(adc_array, dtype=np.uint8)
            ch[array_index+i] = np.frombuffer(ch_array, dtype=np.uint8)
            orbit[array_index+i] = np.frombuffer(orbit_no, dtype=uint64)
            run[array_index+i] = np.frombuffer(run_no, dtype=uint32)

    del event_data, data, evt_no, bx_no, orbit_no, run_no, ch_array, adc_array, tdc_no, tdc2_no # MUST explicitly delete any reference to 'data'
    del tdc, tdc2, bx, ampl, ch, orbit, run # Deletion for brevity's sake
    TDC.close() # Close access to shared memory
    TDC2.close()
    BX.close()
    AMPL.close()
    CH.close()
    ORBIT.close()
    RUN_NO.close()
    DATA.close()
    end = time.time()
    print(f"Time it took to parse: {end-start:.3f}s")
    return
            


def parse_bin_file(file_name):
    """
    Parses through the custom .uhtr binary file format for the uHTR data.
    See txt_to_bin() for documentation on the file structure of the
    .uhtr file type.
    Returns numpy arrays of TDC, TDC2, AMPL, CH, BX, ORBIT, and RUN
    """
    
    def get_offsets(bytes):
        """
        Returns a list of the byte position of all events in the file, 
        the starting index of those events, and the total length of the
        final tdc/ampl/orbit/etc... arrays
        """
        offset_list = [(0, 0)]
        bytes_read = 0
        array_length = 0
        offset = None
        while offset != 0:
            offset = int.from_bytes(bytes[bytes_read:bytes_read+2], "big")
            array_length += (offset - 18) // 23
            offset_list.append((array_length, bytes_read + offset + 2))
            bytes_read += offset + 2
        return offset_list[:-1], array_length + 1
    
    def split_offsets(offset_list, num_chunks):
        """
        Splits the offset list into equally sized lengths, used
        for multiprocessing
        """
        split_offset_list = []
        last_offset = 0
        chunk_size = len(offset_list) // num_chunks
        for i in range(num_chunks):
            if i != num_chunks-1:
                split_offset_list.append(offset_list[last_offset:last_offset+chunk_size])
                last_offset += chunk_size
            else:
                split_offset_list.append(offset_list[last_offset:])
        return split_offset_list
    
    start = time.time()
    with open(file_name, "rb") as fp:
        file_data = fp.read()
    end = time.time()
    print(f"Time it took to read data: {(end-start)*1000:.0f}ms")

    start = time.time()

    offset_list, array_len = get_offsets(file_data)

    TDC = SharedMemory("TDC", create=True, size=array_len)  # Time of the pulse in the 40 MHz clock. 0 to 25 ns in steps of 0.5 ns.
    TDC2 = SharedMemory("TDC2", create=True, size=array_len) # if the threhold was crossed prior to recording
    BX = SharedMemory("BX", create=True, size=array_len*2)   #  Bunch crossing value: ranges from zero to 3564.
    AMPL = SharedMemory("AMPL", create=True, size=array_len*20) # Pulse height of signal.
    CH = SharedMemory("CH", create=True, size=array_len*2)   # channel number, stored as a list of two numbers, 20 different values
    ORBIT = SharedMemory("ORBIT", create=True, size=array_len*8)  # Orbit counter which tells you when the event occured.
    RUN_NO = SharedMemory("RUN_NO", create=True, size=array_len*4) # Number of the data collection run.
    DATA = SharedMemory("DATA", create=True, size=len(file_data)) # Shared data memory buffer

    data = DATA.buf # Set 'data' to the DATA buffer
    data[0:] = file_data # Fill 'data' with binary from file

    useable_cores = mp.cpu_count() - 2
    offset_sectors = split_offsets(offset_list, useable_cores)
    
    end = time.time()
    print(f"Time it took to setup: {(end-start):.3f}s")

    start = time.time()
    with mp.Pool(useable_cores) as pool:
        pool.starmap(_parse_bin_sector, [(array_len, offset_sectors[i]) for i in range(len(offset_sectors))])
    end = time.time()
    print(f"Time it took to parse all sectors: {end-start:.3f}s")
    
    tdc = np.copy(np.ndarray(shape=(array_len,), dtype=np.uint8, buffer=TDC.buf)) # Make sure to copy from shared memory
    tdc2 = np.copy(np.ndarray(shape=(array_len,), dtype=np.int8, buffer=TDC2.buf))
    bx = np.copy(np.ndarray(shape=(array_len,), dtype=np.uint16, buffer=BX.buf))
    ampl = np.copy(np.ndarray(shape=(array_len, 20), dtype=np.uint8, buffer=AMPL.buf))
    ch = np.copy(np.ndarray(shape=(array_len, 2), dtype=np.uint8, buffer=CH.buf))
    orbit = np.copy(np.ndarray(shape=(array_len,), dtype=np.uint64, buffer=ORBIT.buf))
    run = np.copy(np.ndarray(shape=(array_len,), dtype=np.uint32, buffer=RUN_NO.buf))

    del data
    TDC.close() # Free and release shared memory blocks
    TDC.unlink()
    TDC2.close()
    TDC2.unlink()
    BX.close()
    BX.unlink()
    AMPL.close()
    AMPL.unlink()
    CH.close()
    CH.unlink()
    ORBIT.close()
    ORBIT.unlink()
    RUN_NO.close()
    RUN_NO.unlink()
    DATA.close()
    DATA.unlink()

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
