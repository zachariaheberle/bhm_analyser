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
    if (stop_event == -1): stop_flag = False #disable stop event
    else: stop_flag = True #enable stop event
    with open(file_name) as f: #loading file into memory
        lines = f.readlines()  
    evt_status = ""
    data = []
    l = lines # renaming so it is easier to type
    i=0
    TDC = []
    TDC2 = [] # if the threhold was crossed prior to recording
    BX = []
    AMPL = []
    CH = []
    ORBIT = []
    RUN_NO = []
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
            if (evt_no > start_event): # start from event number 
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
    return np.asarray(CH),np.asarray(AMPL),np.asarray(TDC),np.asarray(TDC2),np.asarray(BX),np.asarray(ORBIT),np.asarray(RUN_NO)
