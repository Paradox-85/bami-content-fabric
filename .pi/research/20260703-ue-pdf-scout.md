# AVEVA Unified Engineering — Default Configuration Package Installation (Rev 2.0, Nov 2025)
## Research Summary for Principle Architecture / Project Scheme Slide

**Source:** `AVEVAUnifiedEngineeringDefaultConfiguration2.0_Default Configuration Package Installation.pdf`
**Doc Author:** veeresha.baligara@aveva.com  
**Pages:** 74  
**Keywords:** CONNECT, NAM, SPECTRUM

---

## 1. Document Structure Overview

| Section | Pages | Content |
|---|---|---|
| Introduction | 5–6 | 3-project default config (MLP, UERP, ESP) |
| UE – CONNECT Configuration | 7–12 | User Mgmt, NAM, Spectrum, LaaS |
| UE – Project Configuration | 13–14 | MLP/UERP/ESP setup, auth, cross-discipline notifications |
| UE – Scope Configuration | 15–16 | NAM scope mapping, name context, type mappings, NAM DB update |
| Spectrum Services Setup | 17–20 | Edge Connectors, installation, upload, end-user apps, sample env |
| Appendix — NAM Config Import | 21 | Import pre-defined .zip naming rules |
| Appendix — Naming Rules | 22–39 | Detailed naming rule definitions (15+ rule types) |
| Appendix — MLP Deployment | 40–42 | MLP as "Corporate Template Project", MDBs |
| Appendix — UERP Deployment | 43–46 | Reference project with sample data |
| Appendix — ESP Deployment | 47–50 | Empty starter project |
| Appendix — NAM Key Removal | 51–52 | Lexicon module procedure |
| Appendix — NAM Scope/Context Mapping | 53–57 | UERP & ESP scope + context setup |
| Appendix — Type Mappings | 58–64 | Full class/attribute/naming-rule mapping tables |
| Appendix — Execute Naming Rules | 65–66 | Populate NAM DB with existing tags |
| Appendix — Sample Tag Creation | 66–67 | e.g., Reciprocating Pump → 701-P-011 |
| Appendix — Spectrum Operating Env | 68 | Architecture diagram (cloud + Edge Connector + client) |
| Appendix — Edge Connector HW Reqs | 68 | Win 10/11/Server 2019/2022, 64-bit |
| Appendix — Spectrum Security | 69 | TLS 1.2+, encrypted at rest/in transit, CONNECT auth |
| Appendix — Network Security | 70–71 | gRPC, firewall ports, URLs, SMB port 445 |
| Appendix — PMLLIB Folder | 72–74 | Custom PML functions, forms, pseudos |

---

## 2. Core Architecture: Three-Project Hierarchy

```
Default Configuration 2.0
├── Master Library Project [MLP]          ← Corporate template (class library, data model, symbols, MDBs)
├── Unified Engineering Reference [UERP]  ← Contains sample 1D/2D/3D data for demo/training
│   ├── references MLP
│   ├── references ACP (AVEVA Catalogue Project v4.2.0.0)
│   └── references APS (AVEVA Plant Sample v4.2.0.0)
└── Engineering Starter Project [ESP]     ← Empty project with 3D data, no engineering instances
    ├── references MLP
    ├── references ACP
    └── references APS
```

**Key points:**
- MLP is the foundation — contains class library data model, symbols (E&I, PFD, PID in 2.5mm/3.0mm), AIM configuration, datasheet/dbview/template definitions, project breakdown structure, and workflow definitions
- UERP has 13 MDBs per discipline (Process/PFDs, Process/P&IDs, Mechanical, Instrumentation, Electrical, Simulation, All-in-one, E3D, AIM, Performance, Hydrogen)
- ESP mirrors UERP's MDB structure but has zero engineering instance data
- ACP (Catalogue) and APS (Sample) are referenced projects from AVEVA version 4.2.0.0

---

## 3. CONNECT Platform Services (Cloud)

### 3.1 Required CONNECT Services
1. **User Management** — email-based users, groups, roles filtered by service/folder/group
2. **Name Allocation Manager (NAM)** — standardized tag naming service
3. **Unified Engineering – Spectrum** — cloud project data sharing
4. **License as a Service (LaaS)** — cloud licensing

### 3.2 Name Allocation Manager (NAM)
**3-part structure:**
1. **Naming Rules** — templates composed of named parts (e.g., System-EquipCode-PrimarySequence-Suffix)
2. **Rule Sets** — groups of naming rules for simplified management
3. **Scope** — represents an asset/project (e.g., oil rig, factory); a NAM tenancy can have multiple scopes

**Configuration methods:**
- Web Dashboard Import (zip file with naming rules, types, rulesets, scopes, name contexts, sequence reservations)
- Manual creation via CONNECT UI

**NAM roles:** Config Administrator, Scope Administrator, NAM User

**Sample naming rule previews:**
| Rule | Pattern | Example |
|---|---|---|
| Physical Equipment | (TTT)-(TTTT)-(NNN)(*) | 701-P-011 |
| Functional Equipment | (TTT).(TTTT)-(NNN)(*) | 999.PMP-001 |
| Instrumentation | (TTT)-(TT)(TTT)(*)-(NNN) | 701-FV1001-001 |
| Cable | (TTT)-(TTT)-(NNN) | 701-POW-001 |
| Plant Area | (T*)-(T*) | A1-100 |
| Piping Network | (TTT)-(TTTTT)-(NNNN) | 701-WATER-0001 |

### 3.3 Spectrum Service (Cloud + On-Prem Edge)
**Purpose:** Share project data between AVEVA authoring components, centralize in CONNECT, connect teams globally

**Key components:**
- **Spectrum Cloud** — runs on CONNECT platform (Azure); persists all Dabacon project data + non-Dabacon files in secure cloud storage
- **Edge Connector** — on-prem Windows service on LAN, caches & syncs project data
- **Client Product Components** — AVEVA E3D Design, AVEVA Engineering, AVEVA Administration (on-prem, same LAN as Edge Connector)

**Spectrum Cloud Roles:** Owner, Edge Connectors Admin, Projects Admin, Project Manager, Project Subscriptions Manager, Project Writer, Project Reader, Edge Connector Service, Storage Writer

### 3.4 LaaS (License as a Service)
- Environment variable: `AVEVA_LICENSE_SERVER_LIST=https://license.connect.aveva.com`
- No on-prem license server needed

---

## 4. Communication & Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONNECT CLOUD (Azure)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ NAM Service  │  │ Spectrum     │  │ LaaS                   │ │
│  │ (naming mgmt)│  │ Cloud Service│  │ license.connect.aveva  │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────────────────┘ │
│         │                 │                                      │
│    HTTPS :443        HTTPS :443 (TLS 1.2+)                       │
└─────────┼─────────────────┼──────────────────────────────────────┘
          │                 │
          │       HTTPS :443│
          │                 │
┌─────────┼─────────────────┼──────────────────────────────────────┐
│         │                 │   CUSTOMER LAN                        │
│  ┌──────┴─────────────────┴──────────────────────────────┐      │
│  │              Edge Connector (File Server)               │      │
│  │  C:\ProgramData\AVEVA\Spectrum Edge Connector\          │      │
│  │  ├── claims (exclude from AV)                          │      │
│  │  ├── db     (exclude from AV)                          │      │
│  │  ├── service(exclude from AV)                          │      │
│  │  └── cloudstore (include in AV, sync from other locs)  │      │
│  │                                                        │      │
│  │  Services: File Sync, gRPC endpoints on :5005, :5006   │      │
│  │  SMB file share on :445                                │      │
│  └──────────────┬───────────────────────────────────────────┘      │
│                 │                                                  │
│      TCP :5005/:5006 (gRPC, TLS encrypted, configurable)          │
│                 │                                                  │
│  ┌──────────────┴───────────────────────────────────────────┐      │
│  │         AVEVA UE Client Machines (LAN)                    │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │      │
│  │  │ E3D      │ │ AVEVA    │ │ AVEVA    │ │ AVEVA    │   │      │
│  │  │ Design   │ │ Engineer │ │ Admin    │ │ Config   │   │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │      │
│  │                                                        │      │
│  │  Each user: AVEVA_LICENSE_SERVER_LIST env var           │      │
│  │  Projects stored in C:\Users\Public\Documents\AVEVA\   │      │
│  └────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

### Firewall / Network Rules

| Direction | Protocol | Port | Destination | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 5005 (default) | Edge Connector | gRPC from UE clients |
| Inbound | TCP | 5006 (default) | Edge Connector | gRPC from UE clients |
| Inbound | SMB | 445 | Edge Connector | File share (cloudstore) |
| Outbound | HTTPS | 443 | spectrum.connect.aveva.com | Spectrum cloud API |
| Outbound | HTTPS | 443 | central-claims-iothub-prod.azure-devices.net | IoT Hub |
| Outbound | HTTPS | 443 | storeblobprod0a01211a.blob.core.windows.net | Blob storage |
| Outbound | HTTPS | 443 | instalblobprod1ee8451e.blob.core.windows.net | Install blobs |
| Outbound | HTTP | 80 | Certificate validation URLs | CRL/OCSP |

### gRPC & TLS
- All client ↔ Edge Connector communication uses **gRPC** (open-source RPC framework)
- All communication encrypted with **TLS 1.2+**
- All authentication via **CONNECT** credentials

---

## 5. Project Deployment Workflow

### Step-by-step for a new UE environment:

```
1. CONNECT Account Activation
   ├── Create users/groups/roles in CONNECT
   ├── Configure NAM (naming rules, rule sets, scopes)
   └── Assign Spectrum roles

2. On-Premise Project Setup
   ├── Extract MLP, ACP, APS project files from DefaultConfiguration2.0
   ├── Add project paths to custom_evars.bat
   ├── Set PMLLIB path
   └── Launch project → configure MDBs

3. Spectrum Enablement
   ├── Create Edge Connector in CONNECT web dashboard
   ├── Install Edge Connector on file server (LAN)
   ├── Upload project to Spectrum (must pass dice check, no global satellites, multi-write)
   └── Subscribe project to Edge Connector

4. NAM Integration
   ├── Map NAM scope to project (Engineering Config → Settings)
   ├── Map Name Context (Rules → Name Context Mappings)
   ├── Configure Type Mappings (class ↔ attribute ↔ naming rule part)
   └── Execute Naming Rules to populate NAM DB (for existing tags)

5. End-User Access
   └── Install UE application → authenticate via CONNECT → access spectrumised project
```

---

## 6. Key Disciplines & MDBs

| MDB | Discipline / Purpose |
|---|---|
| 01-PROCESS_AND_PFDs_DRAWINGS | Process Engineering (PFD, 3.0mm symbols) |
| 02-PROCESS_AND_PIDs_DRAWINGS | P&ID Engineering (3.0mm symbols) |
| 03-MECHANICAL | Mechanical Engineering |
| 04-INSTRUMENTATION | Instrumentation Engineering |
| 05-ELECTRICAL | Electrical Engineering |
| 06-SIMULATION-IMPORT | Simulation data import |
| 07-ALL | All disciplines combined |
| 08-E3D | 3D modeling (Model, Draw, Schematic, Engineering) |
| AIM-CONFIGURATION | AIM Configuration Data |
| PIDs_2.5MM_SYMBOL | P&IDs with 2.5mm symbols |
| PFDs_2.5MM_SYMBOL | PFDs with 2.5mm symbols |
| ZZ-HYDROGEN | H₂ plant data |

MLP-specific MDBs: ADMIN, ALL-DATASHEETs-DBVIEWs, ALL-GRIDs, E&I-SYMBOL, EI-DATAMODEL-CLASS-MAPPING, EI-LIBRARY-ITEMS, PFDs-DATAMODEL-CLASS-MAPPING, PFDs-LIBRARY-ITEMS, PROJECT-BREAKDOWN-STRUCTURE, PROJECT-WORKFLOW

---

## 7. Naming Rule Categories (Complete)

| # | Rule | Element Types |
|---|---|---|
| 1 | Physical Equipment | Transformer, Switchgear, Cabinet, Panel, Junction Box, Motor, Generator, Heater, MCC, Skid, Equipment |
| 2 | Functional Equipment | Pump, Blower, Fan, Conveyor, Motor, Mixer, Reboiler, Mill, Flame Arrestor, Heater, Expander, Separator, Dryer, Compressor, Vessel, Heat Exchanger |
| 3 | Electrical Sub-Equipment | Electric Motor, Variable Speed Drive Converter |
| 4 | Component / Sub-Equipment | Tube Bundle, Packed Bed, Tray, Terminal Strip, Relay, Contactor, Busbar, I/O Card, Heat Exchanger Shell, Luminaire, Fieldbus Device, Pump Casing... |
| 5 | Plant Area | Plant Area |
| 6 | Instrumentation | Orifice Plate, Instrument, In-Line Instrument, Actuator |
| 7 | Control Item | Alarm Function |
| 8 | Cable | Cable |
| 9 | Signal | Signal |
| 10 | Instrumentation Diagram | Hook Up, Installation Detail, Diagram |
| 11 | Instrumentation Control Loop | Control Loop |
| 12 | Piping Network System | Piping Network System |
| 13 | Functional Stream | FUN Stream |
| 14 | Piping Component [Fitting] | Fitting |
| 15 | Nozzle | Nozzle |
| 16 | Process Material Data | Material Flow Bulk, Hazardous Conditions |
| 17 | Civil Items | Building, Room |
| 18 | Cable Support | Cable Conduit, Cable Tray |
| 19 | Actuator | Actuator |
| 20 | Process Instrument Connection Lines | Process Instrument Connection |
| 21 | Signal Line | Signal Line |
| 22 | Tie-In Point | Tie-In Point |

---

## 8. PMLLIB Customizations

**Location:** `DefaultConfiguration2.0 > PMLLIB`

| File | Functionality |
|---|---|
| `history.pmlfnc` | Change history on any CE (dates, user info) |
| `renameInstSPCO.pmlfnc` | Rename instrument SPCO for spec identification |
| `dbesorthierarchy.pmlfrm` | Custom hierarchy sort form (E3D) |
| `isdpreviewmessages.pmlfrm` | Isometric message preview |
| Pseudos (various .pmlfnc) | Get/set pseudo attributes in Lexicon |
| `SortMembers.pmlfrm` | Advanced hierarchy sorting for E3D elements |
| Ontology functions | ClassPrefLabel, ClassProperties, ClassRoot, ClassSubClasses, ClassSubClassOf, ClassSubPropertyOf, ClassType |

---

## 9. Constraints & Risks

1. **Project reset** requires removing NAM keys from Lexicon (CFGGRP NameAllocation → AVEVAConnectSolutionID)
2. **Edge Connector** must be on **same LAN** as client machines — critical topology constraint
3. **Dice check** required before uploading projects to Spectrum; global satellites must be removed; update databases must be multi-write
4. **Safari browser** has known UI/UX limitations for Spectrum Admin dashboard
5. **Clock synchronization** (Windows Time Service) required for Edge Connector server
6. **Pagefile.sys** must be enabled on Edge Connector server
7. **Antivirus exclusions** needed for Edge Connector subfolders (claims, db, service) but NOT cloudstore
8. UERP/ESP **require** MLP, ACP, and APS all present and referenced

---

## 10. Slide Content Recommendations

For a **Principle Architecture / Project Scheme** slide, suggest including:

1. **Three-project hierarchy** (MLP → UERP/ESP, both referencing ACP+APS) as a pyramid or nested-box diagram
2. **Cloud vs On-Prem boundary** — CONNECT (NAM + Spectrum + LaaS) in cloud; Edge Connector + Client apps on customer LAN
3. **Data flow arrows** — gRPC (TLS) on ports 5005/5006 between client and Edge Connector; HTTPS 443 from Edge Connector to cloud
4. **Key roles** — Config Administrator, NAM Scope Administrator, Project Manager, Project Writer (Spectrum)
5. **NAM components** — Naming Rules → Rule Sets → Scopes → Name Contexts → Type Mappings
6. **Project lifecycle** — Project Setup → Spectrum Upload → Scope Mapping → Name Context → Type Mapping → Execute Naming Rules → End-User Access
7. **Discipline MDBs** — Process, Mechanical, Instrumentation, Electrical, E3D (color-coded)
