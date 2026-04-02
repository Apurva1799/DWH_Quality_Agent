## Section 1: Forging Process (Manufacturing Domain)

### Process List:
- **Forging_Process** → End-to-end manufacturing flow for forged components. Covers requirement analysis, design, procurement, billet preparation, forging stages, inspection, and routing to processing/heat treatment.  
- **Customer_Requirement** → Inputs: Drawings, specs, material grade. Foundation of all downstream planning.  
- **Routing_Forging_Type** → Decision gateway (CDFD vs. HFD).  
- **Forging_Type** → Top-level forging type selector.  
- **Type_CDFD** → Closed Die Forging path → routes back into Forging_Process.  
- **Type_HFD** → Heavy Forging Division path → routes into HFD branch.  
- **Design_Engineering** → Feasibility, die design, dimensional analysis.  
- **Material_Procurement** → Secures raw material with traceability (heat numbers, test certificates).  
- **MQC_Clearance** → Metallurgical QC: chemical, microstructure, mechanical validation.  
- **Production_Planning (PPC)** → Scheduling, feasibility confirmation, alignment with die shop.  
- **Die_Manufacturing** → Die machining, CCPR inspection.  
- **Billet_Cutting** → Length and weight control of billets.  
- **Billet_Heating** → Induction/furnace heating to forging temperature.  
- **Forging_Stages** → Preform 1 → Preform 2 (blocker) → Finisher.  
- **Trimming_And_Padding** → Flash trimming and correction.  
- **Customer_Specified_Routing** → Cooling method decision (CCC → Processing, NCC → Heat Treatment).  
- **Cooling_Process** → Executes CCC/NCC routing.  
- **Yard_Inspection** → Final segregation (OK Yard vs. Non-Conformance Yard).

### Facts coverage / Trigger Words:
- **Keywords:** `forging`, `billet`, `die`, `trimming`, `padding`, `yard inspection`, `CCC`, `NCC`, `heat number`, `customer requirement`  
- **When to use this section:**  
  - Questions about *forging stages, billet preparation, die manufacturing, trimming/padding, or cooling process*.  
  - Queries mentioning *Closed Die Forging (CDFD)* or *Heavy Forging (HFD)*.  
  - Triggers like:  
    - “How does forging work?”  
    - “Explain billet heating”  
    - “What happens after trimming?”  
    - “What is CCC vs NCC cooling?”  
    - “Where does yard inspection fit in the forging process?”

## Section 2: Heat Treatment Process (Manufacturing Domain)

### Process List:
- **Heat_Treatment_Process** → End-to-end overview of controlled heating and cooling cycles to improve hardness, toughness, and relieve stress in forged/machined components. Starts after forging or machining and includes planning, trial runs, heating, quenching, tempering, inspection, and dispatch.  
- **HT_Simulation_And_Planning** → Virtual simulation of the heat treatment cycle. Defines parameters like temperature, time, and cooling method. Outputs: cycle plan, trial sheet.  
- **HT_Trial_Run** → Small-batch validation of simulated cycle. Checks microstructure, hardness, and distortion to refine process.  
- **HT_Furnace_Preparation** → Selection of furnace type (batch, continuous, gas/electric) and preparation of fixtures, baskets, and racks.  
- **HT_Heating** → Controlled heating to enable structural transformation (e.g., austenite formation). Parameters: ramp rate, holding temperature, duration.  
- **HT_Soaking** → Holding at target temperature for uniform transformation. Risk: grain growth if overheated.  
- **HT_Quenching** → Rapid cooling using oil, water, or polymer to increase hardness and strength. Risks: cracking, distortion.  
- **HT_Tempering** → Reheating quenched parts at lower temperature to relieve brittleness and improve ductility. Range: 100–700°C.  
- **HT_Testing_And_Inspection** → Final inspection for hardness, microstructure, and dimensional accuracy using Rockwell/Brinell and metallography.  
- **HT_Final_Approval_And_Dispatch** → Documentation, tagging, and traceability approval before routing parts to the Processing Department.

### Facts coverage / Trigger Words:
- **Keywords:** `heat treatment`, `quenching`, `tempering`, `soaking`, `hardness test`, `microstructure`, `distortion`, `furnace`, `dispatch approval`  
- **When to use this section:**  
  - Questions about *why and how metals are heat treated*.  
  - Queries mentioning *hardness, toughness, brittleness, stress relief, quenching media, tempering temperatures*.  
  - Triggers like:  
    - “What happens in heat treatment?”  
    - “Explain quenching vs tempering.”  
    - “What is soaking in heat treatment?”  
    - “Which furnaces are used in HT?”  
    - “How is a part approved before dispatch after heat treatment?”


## Section 3: Processing Department (Manufacturing Domain)

### Process List:
- **Processing_Department_Overview** → Final gate between Heat Treatment and Customer dispatch. Handles corrections (grinding, straightening), cleaning (shot blasting), comprehensive VDM inspection (Visual, Dimensional, MPI), additional NDT/DT, and applies surface protection (painting/oiling) before packing. Ensures zero-defect delivery and production continuity.  
- **Processing_Part_Family** → Catalog of different part families like Front Axle Beams, Crankshafts, Connecting Rods, Steering Knuckles, Aluminum parts, and Oil-Filled parts. Each family has tailored process flows based on geometry, finish, and inspection needs.  
- **Part_Family_Process_Flow** → Process sequences by family:  
  - **Front Axle Beam**: Linishing → Shot Blasting → Cold Straightening → MPI → VDM → Re-blasting → Painting → Packing  
  - **Crankshaft/Connecting Rod/Small Parts**: Shot Blasting → TIR → MPI → Visual → Re-blasting → Oiling → Packing  
  - **HHP Connecting Rod**: Shot Blasting → Linishing → HT → Peening → MPI I/II → Oiling → Packing  
  - **Aluminum Parts**: FPI Inspection → Pickling → Visual → Packing  
  - **Oil-Filled Parts**: Visual → MPI → Cleaning → Packing  
- **Processing_Operations** → Master catalog of all shop-floor operations: Grinding, Shot Blasting, Inspections (Visual, Dimensional, MPI), Cold Straightening, Shot Peening, Painting, Oiling, and Packing.  
- **Grinding_Operation** → Manual, SPM, and Robotic grinding methods. Removes defects like flash and trim lines. Includes safety precautions, setup checks, and rejection criteria.  
- **Shot_Blasting_Process** → Steel shots blasted at high velocity for cleaning. Parameters: shot grade, hardness, dust collection, shot mix control, and hot spot testing. Different machine types (Tumblast, Spinner Hanger, Table Type) used by part size.  
- **Shot_Peening_Operation** → Strengthening process for fatigue-loaded parts (e.g., HHP Connecting Rods). Induces compressive stress, validated by Alemen and Residual Stress tests.  
- **VDM_Inspection_Control** → Core QC framework: Visual, Dimensional, and MPI. Defines VDM Index (A+B+C/3) with thresholds (Excellent ≥80%). Poor index leads to rejections, delays, and penalties.  
- **Visual_Inspection_Procedure** → Surface inspection under 800–1000 Lux light. Detects cracks, flash, under-fill, dents. Feeds into VDM or corrective operations.  
- **Cold_Straightening_Operation** → Specific to axle beams. Corrects KP height, pad rocking, and twists using hydraulic fixtures. Includes calculations for pad shift and twist correction.  
- **Testing_Methods_Overview** → Differentiates Destructive Testing (DT) and Non-Destructive Testing (NDT). DT = hardness/tensile; NDT = MPI, FPI, UT, Eddy Current, Radiography.  
- **MPI_Inspection_Procedure** → Stepwise process for magnetic inspection of ferrous parts. Covers setup, magnetization, bath concentration, UV inspection, demagnetization, and safety.  
- **Painting_Process** → Dip or Spray painting for corrosion protection. Parameters: paint-to-thinner ratio, viscosity, oven temperature, DFT ≥40 microns. Includes viscosity checks, DFT measurement, adhesion tests, and MSDS documentation.  
- **Oiling_Process** → Dip/spray rust-preventive oil on crankshafts, steering knuckles, or connecting rods after MPI. Temporary film until packing.  
- **MSDS_Requirement** → Documentation requirement for paints, thinners, and chemicals. Ensures operator safety and compliance.  

### Facts coverage / Trigger Words:
- **Keywords:** `processing`, `grinding`, `shot blasting`, `VDM`, `MPI`, `cold straightening`, `shot peening`, `painting`, `oiling`, `packing`, `MSDS`  
- **When to use this section:**  
  - Questions about *final operations before customer dispatch*.  
  - Queries mentioning *surface cleaning, painting, corrosion protection, MPI, cold straightening, VDM index*.  
  - Triggers like:  
    - “What happens in processing department?”  
    - “Explain VDM inspection and its index.”  
    - “What is the difference between shot blasting and shot peening?”  
    - “How is painting done before shipment?”  
    - “What role does oiling play in processing?”  
    - “What tests are done before dispatch?”  


## Section 4: Machining Department (Manufacturing Domain)

### Process List:
- **Machining_Department_Overview** → Department responsible for precision machining of forged or heat-treated parts. Covers turning, milling, grinding, inspection, washing, balancing, and rust prevention. Supported by Production, Engineering, QA, Maintenance, and PPC.  
- **Machining_Process_Flow** → General process flow applicable across machining lines (CL2, CL3, CL4, etc.). Ensures sequential machining with full traceability.  
- **Mass_Centering** → Aligns forged part’s mass symmetrically on the rotational axis to prevent imbalance and vibration in turning/grinding.  
- **Turning_Operation_1** → Rough turning for bulk material removal and establishing preliminary geometry.  
- **Turning_Operation_2** → Refines geometry and improves dimensional accuracy before milling or drilling.  
- **Milling_Operation** → Creates slots, pins, and complex features with milling cutters.  
- **Intermediate_Washing** → Cleans chips and coolant to ensure part cleanliness before precision operations.  
- **Drilling_Washing** → Drilling combined with washing for maintaining cleanliness.  
- **Induction_Hardening_Tempering** → Localized hardening followed by tempering to strengthen surfaces and relieve stress.  
- **Recentring** → Realigns part before precision grinding.  
- **Grinding_Operations** → Includes steady grinding, pins grinding, journal grinding, FOD (Face of Disc), and GOD (Groove Outer Diameter) grinding. Ensures precision finishes and tolerances.  
- **Gauging_Stations** → Dimensional verification post-grinding to ensure tolerance compliance.  
- **Balancing** → Dynamic balancing to ensure stable rotation in service, prevents vibration.  
- **NonDestructive_Testing (NDT)** → Crack/defect detection using MPI and UT before release.  
- **SuperFinishing** → Fine abrasive finishing to enhance surface quality and reduce friction.  
- **Final_Washing** → Multi-stage washing, including demineralized water, for complete cleanliness before protection.  
- **Rust_Prevention** → Applies rust-preventive coating before shipment.  
- **Machined_Shipment** → Final dispatch stage: packaging, documentation, traceability ensured.  

### Improvement / Lean Tools:
- **Value_Stream_Mapping (VSM)** → Identifies wastes in machining workflows (overproduction, excess movement, high inventory, rejections).  
- **Kaizen_Improvements** → Continuous improvement initiatives: automation, layout optimization, machine upgrades, real-time monitoring.  
- **Takt_Time_Calculation** → Formula to balance production speed with customer demand. Applied mainly to non-grinding operations.  

### Facts coverage / Trigger Words:
- **Keywords:** `machining`, `turning`, `milling`, `grinding`, `gauging`, `washing`, `balancing`, `rust prevention`, `shipment`, `VSM`, `Kaizen`, `Takt Time`  
- **When to use this section:**  
  - Questions about *machining processes or operations after forging/heat treatment*.  
  - Queries mentioning *grinding, balancing, gauging stations, superfinishing, rust prevention, or dispatch*.  
  - Lean/process improvement triggers like *Kaizen, VSM, TAKT time*.  
  - Example triggers:  
    - “What are the steps in machining after forging?”  
    - “How do you ensure dimensional accuracy in machining?”  
    - “Explain grinding operations in machining.”  
    - “What is Takt Time and how is it applied in machining?”  
    - “How is rust prevention done before dispatch?”  


## Section 5: Material Quality Control (MQC) Department

### Process List:
- **Material_Quality_Control_Department** → Department responsible for all quality control activities, ensuring compliance with MQP, customer specs, and international standards. Full traceability from raw material to shipment.  
- **MQC_Process_Flow** → Sequential flow from enquiry review to shipment release. Provides end-to-end quality traceability.  
- **Preliminary_Metallurgical_and_Technical_Review** → Reviews enquiry drawings, specs, codes, and standards (ASTM, ASME, DIN, IS, API). Checks material feasibility, heat treatment, equipment capability, forging limitations, and compliance.  
- **Detail_Contract_Review_and_JCC_Comments** → Reviews customer contracts and Job Control Cards (JCC). Confirms feasibility and aligns with enquiry review. Provides comments/approvals.  
- **Manufacture_Quality_Plan_MQP_Preparation** → Prepares MQP defining inspection stages, hold points, test requirements, and checkpoints. Baseline for production quality control.  
- **Raw_Material_Receipt_GRR_SAP_QE51** → Goods receipt logging in SAP (QE51). Captures supplier, grade, quantity, and starts heat number traceability.  
- **Raw_Material_Visual_Inspection** → Checks raw material for surface defects, markings, and dimensional compliance. Defects reported via NCR.  
- **Raw_Material_Metallurgical_Inspection** → Chemical analysis, mechanical property testing, and microstructure evaluation as per MQP.  
- **Heat_Code_Allotment (SAP MSC2N)** → Assigns heat code for full traceability linking raw material to customer orders.  
- **Heat_Code_Verification (SAP ZQ011A)** → Verifies correctness of heat code assignment in SAP. Prevents errors in traceability.  
- **Material_Quality_Clearance (SAP QA32)** → Material clearance in SAP post-inspections and verification. Allows release for production.  
- **Released_For_Production** → Formal authorization by MQC ensuring only tested & cleared material proceeds to forging.  
- **Forging_Production** → Actual forging stage using cleared material, maintaining heat code traceability.  
- **Heat_Treatment_as_per_MQP** → Performs quenching, tempering, annealing, or normalizing as per MQP.  
- **Metallurgical_Testing** → Performs tensile, impact, hardness, ultrasonic, MPI, and microstructure testing.  
- **Test_Certificate_Preparation** → Generates final test certificate with results, compliance check, and approvals. Linked to heat code and order.  
- **Shipment_Release** → Final stage where certified material is released for shipment. Requires test certificate, SAP clearance, and MQC approval.  

### Facts coverage / Trigger Words:
- **Keywords:** `MQC`, `quality control`, `inspection`, `heat code`, `SAP QE51`, `SAP MSC2N`, `SAP ZQ011A`, `SAP QA32`, `raw material`, `forging clearance`, `test certificate`, `shipment release`  
- **When to use this section:**  
  - Questions about *raw material inspections, SAP-based quality checks, and clearances*.  
  - Queries mentioning *heat code, GRR, QA32, MSC2N, metallurgical testing, or MQP*.  
  - End-to-end traceability and certificate generation.  
  - Example triggers:  
    - “What is the process for raw material inspection in MQC?”  
    - “How is heat code assigned and verified?”  
    - “What steps are in SAP QA32 clearance?”  
    - “How does MQC prepare the test certificate?”  
    - “What is required before shipment release?”  


## Section 6: Heavy Forging Division (HFD)

### Process List:
- **HeavyForgingDivision** → Covers HFD-1 (1600T) and HFD-2 (4000T) hydraulic press lines. Integrated heat treatment capability, SAP-based tracking (ZP148B, ZP147B), tunnel hydraulics, and optional external machining.  
- **HFD1_Department** → 1600-ton hydraulic press line with in-house heat treatment bay.  
- **HFD2_Department** → 4000-ton hydraulic press line for large/complex forgings.  
- **UndergroundTunnelHydraulics** → Central hydraulic power system with 5 underground cylinders supporting HFD presses.  
- **HeatTreatmentDivision (for HFD)** → Supports HFD with multiple furnace capacities (2×15T, 2×30T, 1 slow cooling furnace) and quenching options (standard quenching & water quenching).  
- **SAP_ZP148B_ViewVerify** → SAP transaction for viewing/verifying production and QC data.  
- **SAP_ZP147B_DataEntry** → SAP transaction for entering production parameters and quantities in real time. Captures heavy forged quantity and heat-treated quantity.  
- **ExternalMachiningVendors** → Certified external vendors perform customer-specific machining before final QC and shipment.  
- **ProductionWorkflow_HFD** → Sequential process flow:  
  - **WF_Raw_Input** → Receipt of ingots/raw materials.  
  - **WF_Forging** → Forging operations in HFD-1 (1600T) or HFD-2 (4000T). Logs heavy forged quantity.  
  - **WF_Heat_Treatment** → Heat treatment via central HT Division. Options: quenching, water quenching, slow cooling. Logs heat-treated quantity.  
  - **WF_External_Machining** → Optional external machining if specified.  
  - **WF_QC_Final** → Final QC using SAP ZP148B verification.  
  - **WF_Shipment** → Final shipment to customer with traceability.  
- **HFD_Process** → Detailed forging steps (from ingot unload to clapper die final forging):  
  - HFD_Unload_Ingot_F1 → Remove soaked ingots from furnace.  
  - HFD_Feed_Ingot_Manipulator → Load into manipulator for positioning.  
  - HFD_Drawing_R60 → Drawing operation with 60 mm radius die.  
  - HFD_Cogged_To_F1 → Return cogged ingot to furnace for reheating.  
  - HFD_Recharge_Intermediate → Recharge into Furnace 1 for next cycle.  
  - HFD_Soak_Intermediate → Intermediate soak for uniform heating.  
  - HFD_Unload_After_Soak_F1 → Remove for next forging step.  
  - HFD_Feed_Cogged_Manipulator → Position for next drawing.  
  - HFD_Drawing_To_HotCut_Size → Drawing to hot cutting dimensions.  
  - HFD_Hot_Cut_Auto_Multicut → Auto hot cutter splits ingot into billets.  
  - HFD_Recharge_Cut_Pieces_F1 → Reheat billets in Furnace 1.  
  - HFD_Soak_Cut_Pieces → Soak billets before forging.  
  - HFD_Unload_Cut_To_Press → Feed billets to press.  
  - HFD_Semifinish_Octagon_Dango1_5T → Semifinish to octagonal shape using Dango hammer.  
  - HFD_Semifinished_To_F1_Recharge → Reheat semifinished workpieces.  
  - HFD_Soak_Intermediate_2 → Final soak pre-finishing.  
  - HFD_Semifinished_To_Press_Final → Load into press for finishing.  
  - HFD_Final_Forging_Clapper_Die → Final forging in clapper die.  

### Facts coverage / Trigger Words:
- **Keywords:** `HFD`, `Heavy Forging`, `1600T`, `4000T`, `ZP148B`, `ZP147B`, `forging press`, `heat treatment`, `water quench`, `external machining`, `billet`, `clapper die`, `manipulator`, `hydraulics`, `traceability`.  
- **When to use this section:**  
  - Queries related to *heavy forging presses, billet handling, furnace recharging, hot cutting, semifinish, and clapper die forging*.  
  - Questions about *SAP transaction codes ZP147B (entry) and ZP148B (verification)* for HFD.  
  - Traceability of *forged quantities and heat-treated output*.  
  - Enquiries about *external machining vendors and QC integration*.  
  - Example triggers:  
    - “Explain HFD forging process.”  
    - “What is the difference between HFD-1 and HFD-2?”  
    - “How are SAP ZP147B and ZP148B used in HFD?”  
    - “What steps are included in HFD forging before shipment?”  
    - “Which furnace capacities are available in HFD heat treatment?”  
