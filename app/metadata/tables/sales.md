# Schema: sales
 
## Table: dim_Customer
 
- **Column**: CustomerKey
  - **Example Values**: A11049BFLDOCD, A90599BFLDOCD
- **Column**: CustomerID
  - **Example Values**: 11593, 31373
 
- **Column**: CustomerName
  - **Example Values**: SH/SP, SPARE MARK, DANA CORP
 
- **Column**: CustomerGroup
  - **Example Values**: GM, SPARE MARKET, CUMMINS
 
- **Column**: CustomerCountry
  - **Example Value**: India, USA
 
- **Column**: CustomerRegion
  - **Unique Values**: AFRICA, AMERICA, ASIA, EUROPE
 
## Table: fact_SalesAmount
 
- **Column**: CustomerKey
  - **Example Values**: 30057BFIL0000, 30061BFIL0000
 
- **Column**: CompanyCode
  - **Unique Values**: BFIL, BFL
 
- **Column**: InvoiceNumber
  - **Example Values**: 0087036402
 
  ## DATE IS AN INT COLUMN BE CAREFUL WITH THE CONVERSION.
- **Column**: DateID
  - **Example Values**: 20241113, 20230830, 20180406
 
- **Column**: InvoiceItemNumber
  - **Example  Values**: 000010, 000011
 
- **Column**: CustomerID
  - **Example  Values**: 30057, 30061
 
- **Column**: ProductID
  - **Example  Values**: P11627044394, P11627044932
 
- **Column**: PlantID
  - **Example  Values**: 2000, 7100
 
- **Column**: DivisionID
  - **Unique Values**: 00, CD, HF, MM
 
- **Column**: DistributionChannel
  - **Unique Values**: 00, DO, EX, SP
 
- **Column**: Division
  - **Unique Values**: Close Die, Open Die, Ring Rolling
 
- **Column**: BusinessDivision
  - **Unique Values**: Aerospace, Component Business, Defence, Defence Shells, Industrial Business
 
- **Column**: InvoiceQuantity
  - **Example  Values**: 6.000, 1.000
 
- **Column**: BasicInvoiceValueINR
  - **Example  Values**: 211116.8178000, 246604.8960000
 
## Table: fact_SalesContribution
 
- **Column**: InvoiceNumber
  - **Example  Values**: 0087036402, 0087016466
 
- **Column**: DateID
  - **Example  Values**: 20241113, 20230830
 
- **Column**: InvoiceItemNumber
  - **Example  Values**: 000010, 000011
 
- **Column**: CustomerID
  - **Example  Values**: 30057, 30061
 
- **Column**: ProductID
  - **Example  Values**: P11627044394, P11627044932, P11627044901
 
- **Column**: PlantID
  - **Example  Values**: 2000, 7100, 7200
 
- **Column**: DistributionChannel
  - **Unique Values**: DO, EX
 
- **Column**: InvoiceQuantity
  - **Example  Values**: 6.000, 1.000
 
- **Column**: MachiningContribution
  - **Example  Values**: 0.00, 5181.03, 9425.71
 
- **Column**: ForgingContribution
  - **Example  Values**: 0.00, 444.35, 2712.49
 
- **Column**: ForgingNetWeight
  - **Example  Values**: 0.000, 10.700
 
- **Column**: Division
  - **Unique Values**: Close Die, Open Die, Ring Rolling
 
- **Column**: BusinessDivision
  - **Unique Values**: Aerospace, Component Business, Defence, Defence Shells, Industrial Business
 
- **Column**: Tonnage
  - **Example  Values**: 0E-11, 3.48000000000, 1.70400000000, 2.14000000000
 
## Table: fact_SalesPlan
 
- **Column**: PlantID
  - **Unique Values**: 6100
 
- **Column**: ProductID
  - **Example  Values**: P31161035211
 
- **Column**: CustomerID
  - **Example  Values**: 10003, 30463

- **Column**: DistributionChannel
  - **Unique Values**: DO, EX
 
- **Column**: Division
  - **Unique Values**: Close Die, Open Die, Ring Rolling
 
- **Column**: BusinessDivision
  - **Unique Values**: Aerospace, Component Business, Defence, Industrial Business
 
- **Column**: PlannedQuantity
  - **Example  Values**: 500.000, 50.000, 300.000
 
- **Column**: SellingPrice
  - **Example  Values**: 0.00, 14820.14, 13736.84
 
- **Column**: InputWeight
  - **Example  Values**: 0.000, 87.645
 
- **Column**: Tonnage
  - **Example  Values**: 0E-11, 4.08000000000, 5.10000000000
 
- **Column**: PlannedSalesAmountINR
  - **Example  Values**: 4.1867000, 2.9438500
 
## Table: dim_Product (NOTE: THERES NO PRODUCTKEY HERE)
 
- **Column**: ProductID
  - **Example  Values**: X09301007052, P5600400014, X12212001438
 
- **Column**: DieNo
  - **Example  Values**: , 20092, 02510
 
- **Column**: ProductSegment
  - **Unique Values**: Aerospace, Agri / Const / industrial, Defence, Earthmovers, Emobility, Engine, HDEP, HHP, LCV, LOCO, M & HCV, MDEP, Mining, Misc, O&G, Others, PassCars, Power Plant, Steel mill, Tractor, Truck, Utility
 
- **Column**: ProductSector
  - **Unique Values**: Aerospace, Agri / Const / industrial, Defence, Earthmovers, Emobility, Engine, HHP, INDUSTRIAL, LCV, LOCO, M & HCV, Mining, Misc, Others, PassCars, Power Plant, Steel mill, Tractor, Truck, Utility
 
- **Column**: ProductCategory
  - **Example  Values**: CRANKSHAFT, STEERING KNUCKLE, AXLE BEAM, MISC, W. H. ASSEMBLIES, CON ROD, GEAR & PINION, GEARS, HOUSING HALF, FLUID END, TRANSMISSION, RING, TRANSMISSION SHAFT, CROWN WHEEL,  AXLE BEAM, ROCKER ARM ASSEMBLY, SHELLS, SHAFT, SPINDLE, AXLE TUBES, TRACK LINK, P/M PLAIN SHAFT, P/M STEPPED SHAFT, ADJUSTING SPINDLE
 
- **Column**: BusinessCategory
  - **Unique Values**: A, B, C-Awarded, C-Pipeline, D
 
- **Column**: DistributionChannel
  - **Unique Values**: 00, DO, EX, MT, SP