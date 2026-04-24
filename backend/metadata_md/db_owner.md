# Schema: db_owner

## Table: dim_line

- **Column**: LineId
  - **Unique Values**: 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 2, 20, 21, 22, 23, 24, 25, 3, 4, 5, 6, 7, 8, 9
- **Column**: LineName
  - **Unique Values**: 75INUPSE, BH400KJ, BH80MTON, BWP125MN, COLDFL1, COLDFL2, EUMUPRES, FAJX6000, FEUM5000, FJAEWO5K, FLKM2500, FLKM4000, FLMZ2500, FMAX2000, FMAX2500, FPSH4560, FPZS9001, FPZS9002, FQRI5500, FTMP1250, FTMP8000, FWP10K, HAM10TON, HAM25001, HAM25002
- **Column**: LineSBU
  - **Unique Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer
- **Column**: LinePlantName
  - **Unique Values**: Baramati, Mundhwa
- **Column**: LineAltName
  - **Unique Values**: 12500T, AJAX 6000, EUMUCO 5000, JAEWOO, KURIMOTO, LCM, LKM-2500, LKM-4000, LMZ-2500, MAXI 2000, MAXI 2500, None, PSH, PZS-1, PZS-2, SCHULER, T-12500, T-8000, WEDGE PRESS

## Table: dim_Date

- **Column**: DateId
  - **Example Mode Values**: 170401, 170402, 170403, 170404, 170405, 170406, 170407, 170408, 170409, 170410, 170411, 170412, 170413, 170414, 170415, 170416, 170417, 170418, 170419, 170420, 170421, 170422, 170423, 170424, 170425
- **Column**: Date
  - **Example Mode Values**: 2017-04-01, 2017-04-02, 2017-04-03, 2017-04-04, 2017-04-05, 2017-04-06, 2017-04-07, 2017-04-08, 2017-04-09, 2017-04-10, 2017-04-11, 2017-04-12, 2017-04-13, 2017-04-14, 2017-04-15, 2017-04-16, 2017-04-17, 2017-04-18, 2017-04-19, 2017-04-20, 2017-04-21, 2017-04-22, 2017-04-23, 2017-04-24, 2017-04-25
- **Column**: DateWeekNumber
  - **Example Mode Values**: 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37
- **Column**: DateMonthNumber
  - **Unique Values**: 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9
- **Column**: DateQuaterNumber
  - **Unique Values**: 1, 2, 3, 4
- **Column**: DateYearNumber
  - **Unique Values**: 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025

## Table: MVKE

- **Column**: MATNR_KEY
  - **Example Mode Values**: BFLDOP3621802369, BFLDOP3621802697, BFLDOP36218026971, BFLDOP3621803220, BFLDOP3621803281, BFLDOP36218D9016, BFLDOP36218D9017, BFLDOP36218D9018, BFLDOP36218D9019, BFLDOP3711902047, BFLDOP3711902437, BFLDOP3711902446, BFLDOP3711902446E, BFLDOP3711902446H, BFLDOP3711902446S, BFLDOP3711902461, BFLDOP3711902461S, BFLDOP3711902488, BFLDOP37119024881, BFLDOP3711902488S, BFLDOP3711902618, BFLDOP3711902618S, BFLDOP3711902628, BFLDOP3711902628S, BFLDOP3711902647
- **Column**: MATNR
  - **Example Mode Values**: P5610400025, P5610400026, P3116702670, P31167026701, P31167026704, P3116702672, P31167026721, P31167026725, P311670267340, P311670267341, P31167026736, P31167026737, P31167026738, P3116702674, P311670267410, P311670267411, P31167026745, P31167026748, P31167026749, P31167027202, P31167027213, P31167027214, P31167028192, P3116702859, P31167028591
- **Column**: VKORG
  - **Unique Values**: BFIL, BFL
- **Column**: VTWEG
  - **Unique Values**: 00, DO, EX, MT, SP
- **Column**: DWERK
  - **Example Mode Values**: 7300, 6100, 7100, None, 7200, 8200, 6200, 7205, 5100, 7400, 2012, 9005, 7203, 2001, 2026, 2006, 9002, 1000, 2002, 2016, 1100, 2021, 2000, 9004, 9003
- **Column**: PRODH
  - **Example Mode Values**: 0000500050, 00100001043, 00100001001, None, 0060000103, 00100001032, 0000500057, 00300001012, 00003000311, 00100001022, 00003000321, 00300001013, 00001000116, 00100001033, 00200001031, 00200001052, 00100001012, 00200001032, 00100001031, 00200001033, 00200001042, 00100001021, 00200001043, 00700001012, 00001000114
- **Column**: KTGRM
  - **Example Mode Values**: 02, 01, 27, 04, 03, 09, 07, 31, 23, 05, 37, 28, 06, 16, None, 30, 26, 08, 49, 25, 17, 35, 38, 14, 34
- **Column**: MVGR1
  - **Example Mode Values**: 38, 30, 35, None, 67, 16, 31, 10, 27, 21, 61, 507, 11, 19, 32, 37, 50, 17, 91, 503, 18, 12, 501, 710, 68
- **Column**: MVGR2
  - **Example Mode Values**: GEA, SUG, MIS, AUH, OFE, STE, TUR, CEM, FAN, PCO, MHL, DEF, DIE, HYD, WIN, NUC, AER, AUL, AUC, None, GEN, HPV, THE, HSP, IND
- **Column**: MVGR3
  - **Example Mode Values**: None, 20, 01, 17, 11, 04, 21, 26, 12, 02, 03, 23, 19, 24, 06, 13, 10, 16, 18, 08, 05, 22, 07, 09, 25
- **Column**: MVGR4
  - **Unique Values**: 01, D05, DO1, DO2, DO3, DO4, DO5, DO6, EX1, EX2, EX3, EX4, EX5, EX6, EX7, HF, HOS, None, SAT
- **Column**: MVGR5
  - **Example Mode Values**: None, 046, 041, 043, 023, 049, 008, 048, 044, 012, 006, 047, 004, 018, 016, 040, 025, 067, 062, 039, 065, 010, 061, 027, 045
- **Column**: SALES_PERSON
  - **Example Mode Values**: 251, None, 413, 011, 100, 012, 018, 003, 906, 415, 008, 006, 013, 903, 005, 019, 002, 001, 020, 010, 004, 402, 014, 101, 416
- **Column**: MTART
  - **Unique Values**: ZFIN, ZSCR, ZSEM, ZSER, ZTRD
- **Column**: MATKL
  - **Example Mode Values**: HFD, None, CRANK, FAB, OTH, STK, VALVEBODY, MISCDIES, GEDFN, SKP, CNR, GEAR, CROWN, 12509, 01, CR6, HALFAXLE, CAM, OFL, 05106, CONROD, FOR, 12508, 03004, MAC
- **Column**: BISMT
  - **Example Mode Values**: None, 02510, 03857, 04099, 02304, 09015, 02595, 09014, 02513, 02844, 03140, 03222, 04100, 03616, 03254, 20092, 03840, 02824, 03858, 02514, 04148, 02673, 02299, 04064, 03870
- **Column**: PRODH_10_ID
  - **Example Mode Values**: 0010000103, 0030000101, 0010000104, 0020000103, 0010000102, 0020000104, 0000100011, 0020000105, 0000500050, 0010000100, 0070000101, 0010000101, 0020000102, None, 0000300031, 0060000103, 0000500057, 0000300032, 0070000102, 0000500054, 0030000100, 0040000100, 0040000101, 0030000102, 0010000105
- **Column**: PARENT_ID
  - **Unique Values**: 00001, 00002, 00003, 00004, 00005, 00006, 00007, 00008, 00009, 00100, 00200, 00300, 00400, 00500, 00600, 00700, None
- **Column**: PRODH_10_ID_BEZEI
  - **Example Mode Values**: 401 < DIA < 500, 501 < DIA < 630, 301 < DIA < 400, 751 < OD < 1250, DIA > 630, Others, 210 < DIA < 300, Crankshaft Inposition, DIA < 200, OD < 750, None, OD: 501 - 1000, Axle Beam, OTHERS, Miscellaneous, Steering Knuckle, OD: 1001 - 1500, Well Head Assemblies, 1251 < OD < 1500, 751 < OD <1250, SECTION>400X400, Connecting Rod, OD: 1501 - 2000, OD > 1900, Crankshaft Twisted
- **Column**: KTGRM_VTEXT
  - **Example Mode Values**: Open Forging, Forging, Ring rolling, Machined Frt Axle Be, Machined Crankshaft, Sundry Scrap, Jobwork HF Forging, Gen Egg Job work, Asset Sales, Jobwork Dom Forging, Defense Sale, Ring Roll SEZ Sale, Jobwork C/S M/C, Transmission Parts, None, Gen Egg Sales, Open Forge SEZ Sale, Manufacturing Scrap, KCMI-SALES-AUTO SPAR, Tooling Charges, Seal Ring,Clamp, Hub, HFD-POWER ELECTRONIC, Service Sale, Road Wheel, CDFD SEZ Sale
- **Column**: MVGR1_BEZEI
  - **Example Mode Values**: Open Forge - OEM Semi Machined, Open Forge - BFL Non Machined, Open Forge - Export Semi Machined, None, Other Machined - Export, Closed Die - Export Non Machined, Open Forge - BFL Machined, Closed Die - BFL Non Machined, Crankshaft Machined - Export, Crankshaft Machined, Other Machined BFL Machined, GED:Domestic Cust mat-Machined, Closed Die - BFL Machined, Closed Die - Customer Material Semi M/C, Open Forge - Customer Material Non M/C, Open Forge - Export Machined, Defence BFL Non Machined, Closed Die - Export Machined, Miscellaneous BFL Machined, GED:Domestic BFL mat- Fab & Machined, Closed Die - OEM Semi Machined, Closed Die - Customer Material Non M/C, GED:Domestic BFL mat-Machined, Aerospace-Forging-BFL RM-Export, Other Machined OEM Semi Machined
- **Column**: MVGR2_BEZEI
  - **Example Mode Values**: Gear Industry, Sugar Industry, Miscellaneous, Automobile-HCV, Oil & Gas Equipments, Steel Industry, Turbines, Cement Industry, Ind Fans, Pumps & Compressors, Material Handling, Defence, Diesel Engines, Hydro, Wind Mill, Nuclear, Aerospace, Automobile-LCV, Automobile-Car, None, General Engineering, High Pressure Valves, Thermal, Hammer Spares, Industrial
- **Column**: MVGR3_BEZEI
  - **Example Mode Values**: None, 40C8/45C8/EN8 EQ, 17CRNIMO6 EQ, OTHER ALLOY, EN 19 EQ, EN 24 EQ, C55/C60/EN9 EQ, OTHER CARBON, AISI 4130/4140 EQ, 30CRNIMO8 EQ, 34CRNIMO6 EQ, ST50.2/STE500/SA105 EQ, 30C8/35C8 EQ, 20MN5 EQ, DIE STEEL EQ, 21CRMOV5 EQ, SS 410 EQ, FH 11 EQ, 20C8/25C8 EQ, AISI 8630 EQ, EN 29 EQ, BHEL SPECN, TOOL STEEL EQ, SS 304 EQ, 30MN5 EQ
- **Column**: MVGR4_BEZEI
  - **Unique Values**: Akshay Labhsetwar, Defense group, Domestic CLWT, Domestic KCMI, Domestic others, Domsetic HFD sales, Export CLWT, Export KCMI, Mandar Gadekar, Manish Sonawane, None, Saroj Mishra, Satara Sales, Shital Upadhye, Tarun Goel, Yogesh Agrawal
- **Column**: MVGR5_BEZEI
  - **Example Mode Values**: None, FAB non Alloy steel/other motor vehicle, All Alloy forgings products, Machined Crankshaft Alloy steel, Others, Press parts, Alloy St Forg Rough, Parts of Reciprocating Pumps, Machined C/S Non Alloy steel/O&G 8483itm, Fully M/c Crank - A, Steering knuckle, FGNX Assembly /Steering Knuckle Machined, FAB M/c alloy, Forging alloy steel(machined), FAB M/c non alloy, All Non alloy forgings products, OTHERS(PARTS OF RECIPROCATING PUMPS), Boeing 777X leading edge forging, Turbo-jets, turbo-propellers and other g, Aerospace parts, VALVE BLOCK, MACHINED, Forg Crank Alloy, Machined aluminium, OTHERS-PRESS PARTS, FAB Alloy steel
- **Column**: ZIND_CATEGORY
  - **Unique Values**: AUTO, NON AUTO, None
- **Column**: SEGMENT_VALUE
  - **Unique Values**: Aerospace, Agri/Const/Indust, Defence, Earthmovers, Emobility / Electrical vehicle, Engine, HDEP, HHP, LCV, LOCO, M & HCV, MDEP, Mining, Misc, None, O&G, POWER PLANT, Pass Car, Steel Mill, TRACTOR, Truck, Utility
- **Column**: BUSINESS_CAT_VALUE
  - **Unique Values**: A, B, C-Awarded, C-Pipeline, D, None
- **Column**: SUPLY_CONDITION
  - **Example Mode Values**: HFD, Machining, Forging, None, 507, 50, 91, 503, 501, 710, 93, 97, 51, 750, 57, 72, 54, 56, 509, 55, 502, 66, 53, 720, 63
- **Column**: Segment
  - **Unique Values**: Aerospace, Agri / Const / industrial, Defence, Earthmovers, Emobility, Engine, HDEP, HHP, LCV, LOCO, M & HCV, MDEP, Mining, Misc, O&G, Others, PassCars, Power Plant, Steel mill, Tractor, Truck, Utility
- **Column**: SRL_NO
  - **Unique Values**: 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 50, 99
- **Column**: BUSI_CAT
  - **Unique Values**: A, B, Blank, C-Awarded, C-Pipeline, D
- **Column**: ITD_PRODUCT
  - **Example Mode Values**: Blank, CRANKSHAFT, AXLE BEAM, STEERING KNUCKLE, MISC, CON ROD, W. H. ASSEMBLIES, GEARS, HOUSING HALF, GEAR & PINION, TRANSMISSION SHAFT, CROWN WHEEL, VALVE BODIES, TRANSMISSION, FLUID END, RING, HOUSING, AXLE TUBES, PIPE COUPLINGS, SPINDLE, PLANET CARRIER, GEAR ASSY, PINION, SHELLS, CRUSHER HAMMER
- **Column**: SALES_PERSON_NAME
  - **Example Mode Values**: SANJAY PATIL, Blank, SHRIKRISHANA TANDALE, ANANDRAJ, SAROJ S MISHRA, S JAGTAP, SANDEEP CHAVAN, SHRIKANT CHOUDHARY, DANISH MULLA, RAHUL LONDHE, NILESH BELSARE, PANKAJ KUKADKAR, UMESH BAND, PARMESHWAR THAKARE, SHEKHAR PATIL, SAGAR SHAH, AMIT MUDDANNAWAR, SHITAL UPADHYE, SAURABH GULIA, MANGESH SARODE, Y YOHANNAN, ATUL MORE, VIKRAM PATIL, SHUBHAM PATIL, INDERJEET SINGH
- **Column**: Broad_Sector
  - **Unique Values**: Aerospace, Agri / Const / industrial, Defence, Earthmovers, Emobility, Engine, HHP, INDUSTRIAL, LCV, LOCO, M & HCV, Mining, Misc, Others, PassCars, Power Plant, Steel mill, Tractor, Truck, Utility
- **Column**: Final_BUSI_CAT
  - **Unique Values**: Blank, C-Awarded, C-Pipeline, D-Pipeline, Existing
- **Column**: TRANS_LINE
  - **Unique Values**: Others, Transmission Driveline
- **Column**: SORT_GL
  - **Unique Values**: 1, 2, 3, 4, 5, 6
- **Column**: SORT_F_BROAD_CATG
  - **Unique Values**: 1, 2, 3, 4, 5, 6, 7, 8, 9
- **Column**: SORT_F_BUSI_CAT
  - **Unique Values**: 1, 2, 3, 4, 5

## Table: temp_production_quantity

- **Column**: shift_id
  - **Unique Values**: 1, 2, 3
- **Column**: shift_duration
  - **Example Mode Values**: 08:30:00, 07:00:00, 07:45:00, 06:30:00, 08:00:00, 06:15:00, 02:00:00, 03:00:00, 04:00:00, 05:00:00, 01:00:00, 06:00:00, 04:30:00, 05:30:00, 02:30:00, 01:30:00, 03:30:00, 07:30:00, 00:00:01, 00:30:00, 00:45:00, 01:15:00, 04:15:00, 03:45:00, 02:15:00
- **Column**: die_no
  - **Example Mode Values**: 03737, 30006, 30007, 04247, 04062, 08027, 03944, 03587, 02650, 03355, 04082, 02470, 03254, 04654, 03495, 03943, 03840, 04106, 04151, 04181, 30016, 04439, 04193, 09002, 04688
- **Column**: production_quantity
  - **Example Mode Values**: 0.00000, 1.00000, 2.00000, 4.00000, 10.00000, 5.00000, 8.00000, 400.00000, 3.00000, 300.00000, 6.00000, 500.00000, 50.00000, 12.00000, 30.00000, 200.00000, 20.00000, 40.00000, 100.00000, 7.00000, 250.00000, 24.00000, 15.00000, 600.00000, 450.00000
- **Column**: line_id
  - **Unique Values**: 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 2, 20, 21, 22, 23, 24, 25, 3, 4, 5, 6, 7, 8, 9
- **Column**: date_id
  - **Example Mode Values**: 231006, 230824, 190315, 231016, 230830, 230807, 230901, 210714, 240309, 210908, 230606, 230831, 190322, 211021, 230804, 230821, 231109, 180531, 180514, 230516, 231010, 230525, 230616, 230731, 230607

## Table: temp_production_contribution

- **Column**: shift_id
  - **Unique Values**: 1, 2, 3
- **Column**: shift_duration
  - **Example Mode Values**: 08:30:00, 07:00:00, 07:45:00, 06:30:00, 08:00:00, 06:15:00, 02:00:00, 03:00:00, 04:00:00, 05:00:00, 01:00:00, 06:00:00, 04:30:00, 05:30:00, 02:30:00, 01:30:00, 03:30:00, 07:30:00, 00:00:01, 00:30:00, 00:45:00, 01:15:00, 04:15:00, 03:45:00, 02:15:00
- **Column**: die_no
  - **Example Mode Values**: 03737, 30006, 30007, 04247, 04062, 08027, 03944, 03587, 02650, 03355, 04082, 02470, 03254, 04654, 03495, 03943, 03840, 04106, 04151, 04181, 30016, 04439, 04193, 09002, 04688
- **Column**: base_mcontri
  - **Unique Values**: 0.00000, 10000.01000, 382.00000, 6000.00000, 7657.76000, 90.79000, 9000.00000, 98.57000
- **Column**: base_focontri
  - **Example Mode Values**: 123.91000, 224.92000, 575.68000, 131.00000, 695.69000, 82.08000, 1680.33000, 444.00000, 967.94000, 1721.33000, 160.17000, 308.58000, 3947.63000, 5149.63000, 0.00000, 1606.11000, 945.41000, 1234.32000, 8000.00000, 1188.63000, 381.06000, 2712.49000, 278.94000, 6247.00000, 158.91000
- **Column**: base_zoknga_okquantity
  - **Example Mode Values**: 0, 1, 2, 4, 10, 5, 8, 400, 3, 300, 6, 500, 50, 12, 30, 200, 20, 40, 100, 7, 250, 24, 15, 600, 450
- **Column**: machining_contribution
  - **Example Mode Values**: 0.00000, 0.08625, 0.07763, 0.09079, 0.04313, 0.08171, 0.05175, 0.11213, 0.10350, 0.09488, 0.07263, 0.10441, 0.06900, 0.08216, 0.09987, 0.06355, 0.10532, 0.09533, 0.04540, 0.11460, 0.09364, 0.07354, 0.10804, 0.02588, 0.07808
- **Column**: forging_contribution
  - **Example Mode Values**: 0.00000, 1.47426, 2.94853, 0.35912, 0.00097, 0.00121, 2.00000, 0.00111, 2.16000, 0.00395, 0.10547, 0.00103, 0.00100, 0.18515, 0.23543, 2.40000, 0.00096, 0.00090, 4.13716, 0.21094, 2.20000, 0.27074, 0.00128, 2.08000, 2.46461
- **Column**: line_id
  - **Unique Values**: 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 2, 20, 21, 22, 23, 24, 25, 3, 4, 5, 6, 7, 8, 9
- **Column**: date_id
  - **Example Mode Values**: 231006, 230824, 190315, 231016, 230830, 230807, 230901, 210714, 240309, 210908, 230606, 230831, 190322, 211021, 230804, 230821, 231109, 180531, 180514, 230516, 231010, 230525, 230616, 230731, 230607

## Table: dim_PlannedCycleTime

- **Column**: LineName
  - **Example Mode Values**: FPZS9001, FPZS9002, FTMP1250, FTMP8000, FPSH4560, HAM25002, FLKM4000, HAM25001, FAJX6000, FWP10K, BH80MTON, FEUM5000, FQRI5500, HAM10TON, FMAX2500, SIEKAMPL, BWP125MN, COLDFL1, EUMUPRES, FLKM2500, FMAX2000, COINMIB, FJAEWO5K, BH400KJ, FLMZ2500
- **Column**: DieNo
  - **Example Mode Values**: 09015, 03587, 02650, 03222, 02130, 02470, 03207, 02267, 03266, 03218, 03000, 02890, 02690, 02304, 02421, 03255, 02510, 02170, 09014, 03645, 02750, 03383, 02169, 03616, 02720
- **Column**: MaterialCode
  - **Example Mode Values**: WFFOR03587, WFFOR02650, WFFOR03222, WFFOR02470, WFFOR03207, WFFOR02267, WFFOR03218, WOFOR03000, WFFOR02890, WFFOR02690, WFFOR02304, WFFOR02130, WOFOR03266, WFFOR02421, WFFOR03255, WFFOR02510, WFFOR03645, WFFOR03383, WFFOR02169, WFFOR03616, WFFOR02720, WFFOR02721, WFFOR03478, WFFOR04062, WFFOR02859
- **Column**: FromDate
  - **Example Mode Values**: 2022-04-01, 2013-04-01, 2009-08-01, 2012-07-01, 2007-04-01, 2004-08-01, 2019-07-01, 2008-05-01, 2020-07-01, 2023-06-01, 2021-03-01, 2008-07-01, 2023-04-01, 2007-01-01, 2021-05-01, 2022-12-01, 2024-09-01, 2022-01-01, 2024-05-01, 2021-12-01, 2012-01-01, 2022-09-01, 2024-01-01, 2011-01-01, 2017-11-01
- **Column**: ToDate
  - **Example Mode Values**: 9999-12-31, 2022-03-31, 2013-03-31, 2009-07-31, 2012-06-30, 2007-03-31, 2008-04-30, 2019-06-30, 2023-05-31, 2020-06-30, 2023-03-31, 2006-12-31, 2008-06-30, 2022-11-30, 2021-04-30, 2021-12-31, 2024-08-31, 2011-12-31, 2022-08-31, 2010-12-31, 2014-03-31, 2023-12-31, 2024-04-30, 2018-04-30, 2023-11-30
- **Column**: PlannedCycleTimeInSec
  - **Example Mode Values**: 40, 45, 30, 52, 60, 50, 55, 38, 25, 36, 600, 12, 65, 180, 20, 450, 32, 42, 22, 18, 48, 480, 24, 360, 9

## Table: dim_temp_date

- **Column**: date_id
  - **Example Mode Values**: 20230401, 20230402, 20230403, 20230404, 20230405, 20230406, 20230407, 20230408, 20230409, 20230410, 20230411, 20230412, 20230413, 20230414, 20230415, 20230416, 20230417, 20230418, 20230419, 20230420, 20230421, 20230422, 20230423, 20230424, 20230425
- **Column**: date
  - **Example Mode Values**: 2023-04-01, 2023-04-02, 2023-04-03, 2023-04-04, 2023-04-05, 2023-04-06, 2023-04-07, 2023-04-08, 2023-04-09, 2023-04-10, 2023-04-11, 2023-04-12, 2023-04-13, 2023-04-14, 2023-04-15, 2023-04-16, 2023-04-17, 2023-04-18, 2023-04-19, 2023-04-20, 2023-04-21, 2023-04-22, 2023-04-23, 2023-04-24, 2023-04-25
- **Column**: week_no
  - **Unique Values**: 13, 14, 15, 16, 17, 18
- **Column**: month_no
  - **Unique Values**: 4, 5
- **Column**: quarter_no
  - **Unique Values**: 2
- **Column**: year_no
  - **Unique Values**: 2023

## Table: fact_DowntimeLossReasons

- **Column**: LineID
  - **Example Mode Values**: 5, 1, 13, 9, 3, 12, 2, 4, 11, 22, 14, 6, 7, 15, 8, 16, 17, 24, 10, 18, 26, 20, 19, 36, 25
- **Column**: ShiftID
  - **Unique Values**: 01, 02, 03
- **Column**: DowntimeCategory
  - **Unique Values**: PLANNED, UNPLANNED
- **Column**: DowntimeInHours
  - **Example Mode Values**: 0.500000, 0.166666, 0.333333, 0.250000, 1.000000, 0.083333, 0.750000, 0.666666, 0.416666, 8.500000, 0.133333, 0.100000, 0.583333, 0.833333, 1.500000, 0.116666, 0.066666, 0.200000, 7.000000, 0.050000, 2.000000, 0.150000, 0.033333, 1.166666, 1.083333
- **Column**: TpmLossCode
  - **Example Mode Values**: , M, 02, 07, 08, 13, NORMAL, 09, 05, E, 03, 06, 04, H, 01, 12, 11, ABNORMAL, DIES, 10, 17, PROD, N, 16, PPC
- **Column**: TpmLossDescription
  - **Unique Values**: DEFECT LOSS, Die / Jig / Tool Loss, ELECTRICAL, ELECTRONICS, EQUIPMENT FAILURE LOSS, Energy Loss, HYDRAULIC, LINE ORGANIZATION LOSS, LOGISTIC LOSS, MANAGEMENT LOSS, MEASURE & ADJUSTMENT LOSS, MECHANICAL, MINOR STOPPAGES, MOTION LOSS, None, Planned Loss, SET UP & ADJUSTMENT LOSS, SHUTDOWN LOSS, SPEED LOSS, START UP LOSS, TOOL CHANGE LOSS, Yield Loss
- **Column**: Description
  - **Example Mode Values**: PLANNED SHUTDOWN, QUALITY CHECKING, LUNCH / DINNER BREAK, Planned Shutdown, SETUP ACTUAL, LUNCH /DINNER / TEA BREAK, Snacks Lunch Dinner Break, SET UP ACTUAL, Heat symbol change, HEAT SYMBOL CHANGE, Strategic die grinding, LUNCH / DINNER BREAKS, Heat Symbol change, MISMATCH CORRECTION, Job sticking, Heat Symbol Change, HEAT / SHIFT SYMBOL CHANGE, PZS die cooling, PZS die grinding, Others, Insert shim adjustment, SPEED LOSS, 10000T  planned shutdown, Job establishment after die change, DIE HEATING
- **Column**: DateID
  - **Example Mode Values**: 20180606, 20180524, 20180809, 20180514, 20180531, 20180115, 20180607, 20180612, 20180319, 20180308, 20180615, 20170830, 20180116, 20180614, 20180823, 20171123, 20180205, 20180328, 20180525, 20180517, 20180605, 20180521, 20180419, 20180530, 20180716

## Table: fact_Downtime

- **Column**: LineID
  - **Example Mode Values**: 5, 1, 22, 4, 7, 12, 13, 8, 16, 3, 6, 9, 14, 2, 20, 18, 19, 17, 11, 26, 24, 10, 15, 21, 36
- **Column**: ShiftID
  - **Unique Values**: 01, 02, 03
- **Column**: DateID
  - **Example Mode Values**: 20240507, 20240715, 20240508, 20240823, 20240510, 20240413, 20240914, 20240716, 20240509, 20240516, 20240726, 20240717, 20240418, 20240909, 20240807, 20240822, 20240918, 20240605, 20240528, 20240903, 20240606, 20240614, 20240517, 20240819, 20240821
- **Column**: ShiftDuration
  - **Unique Values**: 7.000000, 8.500000
- **Column**: PlannedDowntime
  - **Example Mode Values**: 0.000000, 8.500000, 7.000000, 1.000000, 0.500000, 0.750000, 0.666666, 1.083333, 2.000000, 1.500000, 7.750000, 0.333333, 0.250000, 3.000000, 2.500000, 0.833333, 1.166666, 6.250000, 8.000000, 1.250000, 4.000000, 1.666666, 1.333333, 3.500000, 1.750000
- **Column**: UnplannedDowntime
  - **Example Mode Values**: 0.000000, 0.500000, 1.000000, 8.000000, 1.500000, 2.000000, 1.166666, 6.500000, 0.666666, 1.666666, 0.750000, 0.833333, 1.250000, 1.333333, 1.750000, 2.166666, 3.000000, 2.500000, 0.916666, 2.666666, 1.916666, 0.333333, 2.250000, 2.499999, 1.416666
- **Column**: Uptime
  - **Example Mode Values**: 0.000000, 0.500000, 0.750000, 6.500000, 7.000000, 8.500000, 6.000000, 6.750000, 5.500000, 4.500001, 4.500000, 5.000001, 5.333334, 5.833334, 3.833334, 5.000000, 5.750000, 4.833334, 6.250000, 3.500000, 4.333334, 4.000000, 4.750001, 4.750000, 4.000001

## Table: temp_table

- **Column**: shift_id
  - **Unique Values**: 1, 2, 3
- **Column**: shift_duration
  - **Example Mode Values**: 08:30:00, 07:00:00, 06:30:00, 08:00:00, 02:00:00, 06:00:00, 03:00:00, 01:00:00, 05:00:00, 04:00:00, 02:30:00, 05:30:00, 03:30:00, 04:30:00, 07:30:00, 01:30:00, 00:30:00, 00:00:01, 00:45:00, 01:15:00, 03:45:00, 04:45:00, 02:15:00, 06:15:00, 01:45:00
- **Column**: die_no
  - **Example Mode Values**: 03737, 04062, 04688, 04654, 04807, 04753, 30007, 03943, 30006, 04493, 08027, 04490, 04479, 03355, 09055, 04590, 04070, 04066, 04247, 02650, 04439, 03643, 03254, 30003, 04759
- **Column**: production_tons
  - **Example Mode Values**: 0.00000, 14.50000, 15.66000, 15.08000, 1.83400, 12.00000, 15.95000, 17.40000, 12.32000, 1.77900, 19.72000, 8.47200, 3.55800, 20.88000, 18.56000, 20.30000, 18.85000, 17.98000, 11.84400, 11.60000, 19.14000, 15.37000, 16.94400, 16.24000, 11.00000
- **Column**: line_id
  - **Unique Values**: 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 2, 20, 21, 22, 23, 24, 3, 4, 5, 6, 7, 8, 9
- **Column**: date_id
  - **Example Mode Values**: 231006, 230824, 230830, 231016, 230807, 240309, 230831, 231109, 230821, 230804, 240516, 231010, 230902, 230901, 230829, 230811, 230825, 230916, 230803, 231022, 240321, 230908, 231018, 240415, 231206
- **Column**: production_quantity
  - **Example Mode Values**: 0.00000, 1.00000, 10.00000, 5.00000, 500.00000, 2.00000, 400.00000, 300.00000, 8.00000, 6.00000, 200.00000, 4.00000, 250.00000, 50.00000, 600.00000, 7.00000, 3.00000, 20.00000, 100.00000, 40.00000, 18.00000, 450.00000, 36.00000, 270.00000, 12.00000
- **Column**: machining_contribution
  - **Example Mode Values**: 0.00000, 0.43930, 0.28334, 0.45840, 0.60000, 0.31286, 3.30000, 0.37207, 0.38697, 0.36290, 0.12415, 4.82000, 0.23569, 0.46757, 0.49736, 1.15800, 0.39652, 0.19482, 0.46375, 0.45916, 0.28153, 0.45802, 0.43204, 2.87000, 3.85000
- **Column**: forging_contribution
  - **Example Mode Values**: 0.00000, 2.00000, 2.16000, 2.08000, 0.35912, 2.20000, 2.72000, 2.88000, 2.40000, 0.10547, 0.21094, 1.47426, 2.80000, 4.27062, 2.60000, 2.48000, 1.92000, 1.17911, 2.64000, 2.12000, 2.94853, 2.56000, 2.24000, 0.14622, 2.46461

## Table: fact_MgrComplainceOverdue

- **Column**: DateID
  - **Example Mode Values**: None, 20240323, 20210813, 20231216, 20231231, 20231202, 20231223, 20211028, 20210313, 20210220, 20210401, 20220110, 20210617, 20211220, 20230701, 20240204, 20231124, 20210709, 20240317, 20240309, 20201125, 20240106, 20230930, 20231224, 20230708
- **Column**: MgrCategory
  - **Unique Values**: Electrical%, Mechanical%
- **Column**: LineID
  - **Unique Values**: 1, 10, 11, 12, 13, 14, 16, 17, 19, 2, 20, 22, 3, 4, 5, 6, 7, 8, 9
- **Column**: MgrTotal
  - **Example Mode Values**: 1, 3, 2, 4, 5, 6, 8, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 20, 22, 23, 24, 25
- **Column**: MgrCompleted
  - **Example Mode Values**: 1, 3, 2, 4, 5, 6, 8, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 20, 22, 23, 24, 25
- **Column**: MonthlyMgrTotal
  - **Example Mode Values**: 9, 1, 8, 3, 7, 5, 16, 10, 12, 14, 18, 17, 4, 13, 6, 15, 27, 22, 24, 32, 19, 21, 48, 34, 42
- **Column**: MonthlyMgrCompleted
  - **Example Mode Values**: 1, 9, 3, 8, 7, 5, 16, 10, 12, 14, 17, 18, 4, 13, 15, 6, 22, 32, 27, 24, 19, 51, 48, 34, 21
- **Column**: MgrDaysOverdue
  - **Example Mode Values**: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 15, 14, 18, 19, 21, 24, 37, 22, 29

## Table: fact_GM2

- **Column**: GM2LineName
  - **Example Mode Values**: V_5101 FMD BMT, V_FMD1 V_FMD1, V_FMD2 V_FMD2, V_FMD3 V_FMD3, V_COLD_FORGE V_COLD_FORGE, V_11020 Forge Shop, V_1201 MCD 1, V_1501 MCD 2, V_2201 MCDC, V_5501 FMD 4, V_7001 KCPTL, V_MCD_BARA MCD_BARA, W_FPZS9001 FPZS9001, W_FPSH4560 FPSH4560, W_FLKM4000 FLKM4000, W_FLKM2500 FLKM2500, W_FLMZ2500 FLMZ2500, W_FPZS9002 FPZS9002, W_FEUM5000 FEUM5000, W_FAJX6000 FAJX6000, W_FMAX2500 FMAX2500, W_FWP10K Wedge Press, W_FMAX2000 FMAX2000, W_FQRI5500 FQRI5500, W_FTMP8000 FTMP8000
- **Column**: ShipBase
  - **Example Mode Values**: None, 0.0, 5.0, -0.001, -0.003, -3.211, -31.748, 7.74, -0.356, -10.106, -0.467, -0.195, -1.143, 0.089, 5.576, 4.197, -0.519, -3.386, -7.471, 5.201, 5.693, -3.359, -1.956, 3.395, 4.5
- **Column**: ProdBase
  - **Example Mode Values**: None, 0.0, -1.32, -1.5, -0.52, -0.54, -0.72, -0.31, -0.81, -0.89, -0.47, -1.61, -0.5, -0.59, -0.36, -0.49, -0.45, -0.14, -0.29, -0.77, -0.01, -0.53, -0.04, -0.6, -0.48
- **Column**: MachiningProdBase
  - **Example Mode Values**: None, 0.0, -0.93, -0.59, -0.53, -0.61, -0.45, -0.5, -0.14, -0.89, -0.54, -0.52, -0.77, -0.36, -0.65, -0.63, -0.6, -0.87, -0.31, -0.81, -0.98, -0.1, -1.5, -0.04, -0.01
- **Column**: LineName
  - **Example Mode Values**: None, BH80MTON, Crank shaft, FAB, FMD1, FMD2, FMD3, Cold Forge, Hammer - Mundhwa, MCD1, MCD2, MCD Chakan, 12500T, MCD Indapur, MCD B, FPZS9001, FPSH4560, FLKM4000, FLKM2500, FLMZ2500, FPZS9002, FEUM5000, FAJX6000, FMAX2500, FWP10K
- **Column**: Month
  - **Unique Values**: 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9, None
- **Column**: Quarter
  - **Unique Values**: 1, 2, 3, 4, None
- **Column**: Year
  - **Unique Values**: 2023, 2024

## Table: dim_Sbu

- **Column**: SbuID
  - **Unique Values**: 1, 10, 11, 2, 3, 4, 5, 6, 7, 8, 9
- **Column**: SbuName
  - **Unique Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer Baramati, Hammer Mundhwa, MCD1, MCD2, MCD3, MCD4
- **Column**: SbuPlantName
  - **Unique Values**: Baramati, Chakan, Mundhwa

## Table: dim_DowntimeType

- **Column**: DowntimeTypeId
  - **Unique Values**: 
- **Column**: DowntimeTypeName
  - **Unique Values**: 
- **Column**: DowntimeReason
  - **Unique Values**: 
- **Column**: Downtime
  - **Unique Values**: 

## Table: dim_Product

- **Column**: ProductId
  - **Unique Values**: 
- **Column**: ProductName
  - **Unique Values**: 
- **Column**: ProductCategoryId
  - **Unique Values**: 
- **Column**: ProductCategoryName
  - **Unique Values**: 
- **Column**: ProductNetWeight
  - **Unique Values**: 
- **Column**: ProductCode
  - **Unique Values**: 

## Table: dim_Shift

- **Column**: ShiftId
  - **Unique Values**: 1, 2, 3
- **Column**: ShiftStartTime
  - **Unique Values**: 00:00:00, 07:00:00, 15:30:00
- **Column**: ShiftEndTime
  - **Unique Values**: 00:00:00, 07:00:00, 15:30:00
- **Column**: ShiftDuration
  - **Unique Values**: 07:00:00, 08:30:00

## Table: dim_Line

- **Column**: LineID
  - **Unique Values**: 75INUPSE, BH400KJ, BH80MTON, BWP125MN, COLDFL1, COLDFL2, EUMUPRES, FAJX6000, FEUM5000, FJAEWO5K, FLKM2500, FLKM4000, FLMZ2500, FMAX2000, FMAX2500, FPSH4560, FPZS9001, FPZS9002, FQRI5500, FTMP1250, FTMP8000, FWP10K, HAM10TON, HAM25001, HAM25002
- **Column**: LineSBU
  - **Unique Values**: COLD FORGE, FMD1, FMD2, FMD3, FMD4, Hammer Baramati, Hammer Mundhwa
- **Column**: LinePlantName
  - **Unique Values**: Baramati, Mundhwa

