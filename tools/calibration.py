# Written by Rohith Saradhy rohithsaradhy@gmail.com

'''
Place where we keep user derived variables

Calibration
ADC Cuts 
TDC Peaks
TDC Correction MAP
'''

ADC_CUTS_v1 ={
'PN01': 142,
'PN02': 144,
'PN03': 143,
'PN04': 148,
'PN05': 144,
'PN06': 144,
'PN07': 137,
'PN08': 144,
'PN09': 144,
'PN10': 145,


'PF01': 150,
'PF02': 147,
'PF03': 153,
'PF04': 145,
'PF05': 142,
'PF06': 147,
'PF07': 144,
'PF08': 143,
'PF09': 140,
'PF10': 145,


'MN01': 144,
'MN02': 143,
'MN03': 146,
'MN04': 146,
'MN05': 142,
'MN06': 142,
'MN07': 147,
'MN08': 153,
'MN09': 147,
'MN10': 150,

'MF01': 144,
'MF02': 160,
'MF03': 143,
'MF04': 144,
'MF05': 143,
'MF06': 150,
'MF07': 143,
'MF08': 150,
'MF09': 151,
'MF10': 148
}

TDC_PEAKS_v1 = {
 'PN01': 18,
 'PN02': 19,
 'PN03': 19,
 'PN04': 18,
 'PN05': 19,
 'PN06': 19,
 'PN07': 20,
 'PN08': 19,
 'PN09': 19,
 'PN10': 18,

 'PF01': 18,
 'PF02': 18,
 'PF03': 18,
 'PF04': 19,
 'PF05': 18,
 'PF06': 18,
 'PF07': 19,
 'PF08': 19,
 'PF09': 20,
 'PF10': 18,

 'MN01': 19,
 'MN02': 20,
 'MN03': 18,
 'MN04': 19,
 'MN05': 10,
 'MN06': 19,
 'MN07': 20,
 'MN08': 18,
 'MN09': 19,
 'MN10': 18,

 'MF01': 20,
 'MF02': 17,
 'MF03': 20,
 'MF04': 19,
 'MF05': 20,
 'MF06': 18,
 'MF07': 19,
 'MF08': 18,
 'MF09': 17,
 'MF10': 19
 }


TDC_PEAKS_v2 ={
 
 'PN01': 6,
 'PN02': 6,
 'PN03': 6,
 'PN04': 6,
 'PN05': 6,
 'PN06': 6,
 'PN07': 5,
 'PN08': 6,
 'PN09': 6,
 'PN10': 6,
 
 'PF01': 6,
 'PF02': 7,
 'PF03': 6,
 'PF04': 6,
 'PF05': 6,
 'PF06': 6,
 'PF07': 6,
 'PF08': 6,
 'PF09': 6,
 'PF10': 6,
 
 'MN01': 6,
 'MN02': 5,
 'MN03': 7,
 'MN04': 6,
 'MN05': 0,
 'MN06': 7,
 'MN07': 6,
 'MN08': 6,
 'MN09': 6,
 'MN10': 6,
 
 'MF01': 4,
 'MF02': 6,
 'MF03': 5,
 'MF04': 6,
 'MF05': 5,
 'MF06': 6,
 'MF07': 5,
 'MF08': 6,
 'MF09': 7,
 'MF10': 5
 }


#uHTR4 configurations
#put BHM-3-QIE[1-24]_PhaseDelay 64 49 64 64 65 48 49 49 67 66 0 0 45 48 45 49 49 48 45 47 48 47 0 0 
uHTR4_config_v4 = "64 49 64 64 65 48 49 49 67 66 0 0 45 48 45 49 49 48 45 47 48 47 0 0"#.split(" ")
uHTR4_config_v5 = "75 75 76 75 77 74 76 75 79 77 0 0 70 73 70 75 74 73 71 73 75 72 0 0"
uHTR4_current_config = uHTR4_config_v5

#In the process of testing



# put BHM-10-QIE[1-24]_PhaseDelay 64 64 48 49 49 64 66 49 49 49 0 0 47 42 46 49 49 45 44 45 40 43 0 0 
uHTR11_config_v2 = "64 64 48 49 49 64 66 49 49 49 0 0 47 42 46 49 49 45 44 45 40 43 0 0"#.split(" ")
uHTR11_config_v3 = "76 77 73 75 75 76 79 74 75 74 0 0 74 66 73 75 76 70 70 70 64 69 0 0" 
uHTR11_current_config = uHTR11_config_v3

#In the process of testing



#Skeleton Code
# uHTR4_current_config.remove("0")
# uHTR4_current_config.remove("0")
# uHTR4_current_config.remove("0")
# uHTR4_current_config.remove("0")
# uHTR4_current_config.insert(10,'0')
# uHTR4_current_config.insert(10,'0')
# uHTR4_current_config.insert(22,'0')
# uHTR4_current_config.insert(23,'0')


