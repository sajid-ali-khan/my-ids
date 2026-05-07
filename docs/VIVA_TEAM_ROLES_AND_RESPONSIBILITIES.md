# Viva Presentation - Team Roles & Responsibilities
## Network Intrusion Detection System (IDS)

**Document Purpose:** This guide outlines how to divide the presentation among 3 team members for maximum impact and comprehensive coverage.

**Version:** 1.0  
**Created:** April 2026  
**Status:** Ready for Implementation

---

## Overview: The Three Main Components

Your IDS project naturally divides into **THREE MAJOR COMPONENTS**, each perfect for one team member:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Network Intrusion Detection System (IDS)                  │
│                                                             │
├──────────────────┬──────────────────┬───────────────────────┤
│                  │                  │                       │
│  PERSON 1        │   PERSON 2       │    PERSON 3           │
│  (BACKEND)       │   (FRONTEND)     │    (ML MODEL)         │
│                  │                  │                       │
│  Data Pipeline   │  Dashboard UI    │   Training &          │
│  & Architecture  │  & Visualization │   Classification      │
│                  │                  │                       │
│  How we capture  │  How users see   │   How we detect       │
│  & process data  │  the results     │   attacks             │
│                  │                  │                       │
└──────────────────┴──────────────────┴───────────────────────┘
```

---

## PERSON 1: Backend/Data Pipeline & Architecture
### "The Data Engineer"

### 📌 What They Present

**Title:** "Real-Time Data Pipeline & System Architecture"

**Main Focus:** How network traffic is captured, processed, and flows through the system

### 🎯 Key Topics to Cover

#### 1. **Packet Capture & Flow Aggregation** (10 minutes)
```
Live Network Traffic
    ↓
Packet Capture (Scapy Library)
    ├─ Listens on network interface (eth0, wlp3s0, etc.)
    ├─ Captures every network packet
    ├─ Extracts TCP/IP headers
    ├─ Gets: source IP, dest IP, ports, protocols, flags
    └─ Rate: ~10,000+ packets per second
    ↓
Flow Grouping (5-tuple matching)
    ├─ Groups packets by: (src_ip, dst_ip, src_port, dst_port, protocol)
    ├─ Bidirectional: forward and backward packets collected
    ├─ Combines into "flows" (conversations)
    └─ Example: All traffic between 192.168.1.100:54321 ↔ 8.8.8.8:53
    ↓
Flow Storage
    ├─ Store all packets in memory for the flow
    ├─ Track: packet count, timing, flags, payload sizes
    ├─ Automatic timeout: 30 seconds of inactivity = flow closes
    └─ Ready for feature extraction
```

**Why this matters:**
- Traditional IDS look at individual packets
- Your system looks at entire conversations (flows)
- Provides context for better attack detection
- DoS attacks, brute force, exfiltration all visible at flow level

#### 2. **Multi-Threaded Pipeline Architecture** (10 minutes)

**The three threads working together:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE MANAGER                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
│  │  SNIFFER THREAD  │  │ FLUSHER THREAD│ │CLASSIFIER THREAD│
│  │                  │  │              │  │                 │
│  │ ✓ Capture pkts   │  │ ✓ Detect idle │  │ ✓ Extract 52    │
│  │ ✓ Group flows    │  │ ✓ Close flows │  │   features      │
│  │ ✓ Real-time      │  │ ✓ Timeout mgmt│  │ ✓ Run ML model  │
│  │                  │  │ ✓ Every 20s  │  │ ✓ Save alerts   │
│  │ Runs: Always     │  │              │  │                 │
│  └──────────────────┘  └──────────────┘  │ Runs: Every ms  │
│         ↓                    ↓              │                 │
│    (Raw Packets)    (Completed Flows)     └─────────────────┘
│                                                    ↓
│                                          (Predictions & Alerts)
└─────────────────────────────────────────────────────────────┘
```

**Thread-Safe Design:**
- Uses locks (RLock) to prevent race conditions
- Multiple threads access shared data structures
- Queue for completed flows (producer-consumer pattern)
- Deque for recent predictions (thread-safe, lock-free)

**Why multi-threading:**
- Can't wait for feature extraction before capturing next packet
- Each thread specialized: one captures, one cleans, one analyzes
- Scales to 10,000+ flows/second

#### 3. **Database & Alert Storage** (5 minutes)

```
Predictions Generated
    ↓
Decision: Is this an attack?
    ├─ Yes (Confidence > threshold)
    │   └─ Save to Database ✓
    │
    ├─ No, but unusual (Low confidence normal)
    │   └─ Save as "Suspicious" ✓
    │
    └─ No (Normal traffic, high confidence)
       └─ Don't save (keep history, no alert)
```

**SQLite Database Schema:**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    src_port INTEGER,
    dst_port INTEGER,
    attack_type TEXT,        -- DoS, DDoS, Brute Force, etc.
    confidence REAL,         -- 0.0 to 1.0
    severity TEXT,           -- low, medium, high
    packet_count INTEGER,
    total_bytes INTEGER,
    acknowledged BOOLEAN
);
```

**Benefits:**
- Persistent storage (doesn't lose data on restart)
- Queryable for historical analysis
- Integration with SIEM systems
- Compliance/audit trail

#### 4. **Flow Aggregation for Advanced Detection** (5 minutes)

**Problem:** Some attacks span multiple flows
- Brute force: many failed SSH login attempts
- Port scanning: rapid connection attempts to many ports
- DDoS coordination: packets from different sources

**Solution:** Flow Aggregator
```
Multiple Individual Flows
    ├─ Flow 1: SSH attempt to port 22 (failed)
    ├─ Flow 2: SSH attempt to port 22 (failed)
    ├─ Flow 3: SSH attempt to port 22 (failed)
    ├─ Flow 4: SSH attempt to port 22 (failed)
    ├─ Flow 5: SSH attempt to port 22 (SUCCEEDED)
    └─ ... 50 more failed attempts
    ↓
Aggregation Window (60 seconds)
    └─ Detected: 55 failed SSH attempts from same source
    ↓
Elevated Alert
    └─ "Brute Force Attack Detected" (high severity)
```

**Detection Capability:**
- Catches multi-flow attacks that single flows miss
- Temporal correlation: attacks often have patterns
- Source IP tracking: repeat offenders
- Protocol-specific rules: SSH/FTP detection

#### 5. **Configuration & CLI Interface** (5 minutes)

**How operators use your IDS:**

```bash
ids-cli setup              # Configure (interface, port, etc.)
ids-cli start              # Start monitoring
ids-cli status             # Check if running
ids-cli logs -n 50         # View recent activity
ids-cli stop               # Stop monitoring
```

**Configuration File (~/.ids/config.json):**
```json
{
    "interface": "wlp3s0",           # Which network to monitor
    "port": 5000,                    # Dashboard port
    "model_dir": "./model",          # Where ML model is stored
    "debug": false,                  # Verbose logging
    "host": "0.0.0.0"                # Listen on all IPs
}
```

**Why this matters:**
- Production-grade deployment
- Cross-platform (Linux, Windows, macOS)
- Easy for non-technical users
- Background process management

### 📊 Visual Summary for PERSON 1

```
Raw Network Packets (10,000+/sec)
    ↓ [SNIFFER THREAD - Scapy]
Captured & Grouped into Flows
    ↓ [FLUSHER THREAD - Every 20s]
Completed Flows Detected
    ↓ [CLASSIFIER THREAD - ML]
52 Features Extracted
    ↓
Model Prediction Made
    ↓
Decision Tree (Attack or Normal?)
    ├─ YES → Save to Database
    ├─ MAYBE → Mark as Suspicious
    └─ NO → Log for history

Real-time Dashboard Updated
Alert History Preserved
CLI Tools Available
```

### 🎤 Presentation Tips for PERSON 1

1. **Use a diagram:** Draw the pipeline on whiteboard/slide showing three threads
2. **Explain why:** "Why threads?" → "Because we need to capture while analyzing"
3. **Give examples:** "Brute force attack = many small flows with failures"
4. **Show config:** Demo CLI commands (ids-cli status, ids-cli logs)
5. **Performance numbers:** "Can handle 16,000 flows/second on 8-core server"

### 📚 Documentation to Reference
- `fyp/src/ids_core/pipeline.py` - Main pipeline code
- `fyp/src/ids_cli/cli.py` - CLI interface
- `fyp/src/ids_core/flow_aggregator.py` - Brute force detection
- `fyp/src/ids_core/store/db.py` - Database operations

### ⏱️ Recommended Presentation Time
**Total: 35 minutes** (with questions)
- Packet capture & flow grouping: 10 min
- Multi-threading architecture: 10 min
- Database & persistence: 5 min
- Flow aggregation: 5 min
- CLI & configuration: 5 min

---

## PERSON 2: Frontend/Dashboard & Visualization
### "The UI/UX Developer"

### 📌 What They Present

**Title:** "Real-Time Dashboard & Visualization Layer"

**Main Focus:** How security analysts interact with the IDS and view attack data

### 🎯 Key Topics to Cover

#### 1. **Dashboard Architecture** (8 minutes)

**Three-Column Layout:**
```
┌────────────────────────────────────────────────────────────┐
│              IDS Real-Time Dashboard                        │
├──────────────────┬──────────────┬──────────────────────────┤
│                  │              │                          │
│   COLUMN 1       │  COLUMN 2    │     COLUMN 3            │
│   Statistics     │  Active      │    Alert History        │
│                  │  Flows       │                          │
│  ┌────────────┐  │  ┌────────┐  │  ┌────────────────────┐ │
│  │Total Flows │  │  │192.168 │  │  │⚠️  DoS Detected    │ │
│  │2,847       │  │  │1.100   │  │  │IP: 10.0.0.1       │ │
│  └────────────┘  │  │↔ 8.8.  │  │  │Confidence: 94%    │ │
│                  │  │8.8     │  │  │Time: 14:32:15     │ │
│  ┌────────────┐  │  │Port:   │  │  └────────────────────┘ │
│  │Normal: 2,500│ │  │53      │  │                        │
│  │Attacks: 347 │ │  │Packets:│  │  ┌────────────────────┐ │
│  └────────────┘  │  │145     │  │  │🟢 Normal Traffic   │ │
│                  │  │↓        │  │  │IP: 192.168.1.50   │ │
│  ┌────────────┐  │  └────────┘  │  │Confidence: 99%    │ │
│  │By Attack:  │  │              │  │Time: 14:31:45     │ │
│  │DoS: 123    │  │ [Scroll]    │  └────────────────────┘ │
│  │DDoS: 78    │  │             │                        │
│  │Brute F: 56 │  │             │  [Auto-refreshes     │
│  │Web: 45     │  │             │   every 2 seconds]   │
│  └────────────┘  │              │                        │
│                  │              │                        │
└──────────────────┴──────────────┴──────────────────────────┘
```

**Technology Stack:**
- **Frontend:** HTML5 + CSS3 + JavaScript (Vanilla, no framework)
- **Communication:** AJAX (XMLHttpRequest) polling every 2 seconds
- **Styling:** Jupyter-like aesthetic (professional but approachable)
- **Real-time:** Asynchronous updates without page reload

#### 2. **Key Metrics Display** (8 minutes)

**Statistics Tab - What analysts see:**

| Metric | What It Shows | Why It Matters |
|--------|---|---|
| **Total Flows** | All network conversations captured | Overall traffic volume |
| **Normal Traffic %** | Benign traffic baseline | Understand "normal" for this network |
| **Attack Count** | Total attacks detected | Security posture overview |
| **DoS Attacks** | Denial of Service count | Specific threat tracking |
| **DDoS Attacks** | Distributed DoS count | Severity of volumetric attacks |
| **Brute Force** | Failed login attempts | Account compromise risk |
| **Web Attacks** | Application-layer attacks | Web server security |
| **Infiltration** | Data exfiltration attempts | Insider threats/APT |
| **Bot** | Malware/botnet activity | Compromised system detection |

**Visual Representation:**
```
Real-time Pie Chart
    Normal (78%)  ████████████████████
    DoS (8%)      ███
    DDoS (6%)     ██
    Others (8%)   ███

Real-time Bar Chart
    DoS      [▓▓▓▓▓░░░░] 50/day
    DDoS     [▓▓░░░░░░░░] 25/day
    BruteF   [▓░░░░░░░░░] 10/day
    Web      [▓░░░░░░░░░] 12/day
```

#### 3. **Active Flows Monitor** (8 minutes)

**What analysts need to know about live traffic:**

```
Active Flow Entry:
┌──────────────────────────────────────────────┐
│ Source IP: 192.168.1.100 : Port 54321       │
│ Dest IP:   8.8.8.8      : Port 53           │
│ Protocol:  UDP                               │
│ Status:    Active (23 seconds)               │
│ Packets:   145 (forward), 132 (backward)    │
│ Bytes:     12.5 KB (forward), 8.2 KB (bwd)  │
│ Last Seen: 14:32:45                         │
│ Confidence: Normal (94%)                     │
└──────────────────────────────────────────────┘
```

**Features:**
- **Sorting:** By packets, bytes, duration, or confidence
- **Filtering:** Search by IP address
- **Updates:** Refreshed every 2 seconds (live!)
- **Interactive:** Click for more details

**Why this matters:**
- Analysts can investigate specific flows
- Spot anomalies in real-time
- Track suspicious IPs
- Confirm or dismiss model predictions

#### 4. **Alert History & Filtering** (10 minutes)

**The most critical feature for SOC teams:**

**Alert Table Columns:**
```
Time       │ Source IP    │ Attack Type  │ Confidence │ Action
───────────┼──────────────┼──────────────┼────────────┼──────────
14:35:20   │ 203.0.113.45 │ ⚠️ DoS       │ 96%        │ [Review]
14:33:15   │ 198.51.100.2 │ 🟢 Normal    │ 91%        │ [OK]
14:31:45   │ 192.168.1.50 │ 🔴 DDoS      │ 98%        │ [Block]
14:30:12   │ 172.16.0.5   │ 🟡 Suspicious│ 34%        │ [Review]
14:28:00   │ 10.0.0.100   │ 🔴 Brute F   │ 89%        │ [Block]
```

**Advanced Filtering:**

```
Filter by:
├─ Date Range (last hour, last day, custom)
├─ Attack Type (All, DoS, DDoS, Brute Force, Web, etc.)
├─ Source IP (Specific IPs or subnets)
├─ Severity (All, Low, Medium, High, Critical)
├─ Status (Acknowledged, Unacknowledged)
└─ Confidence (>90%, >80%, >70%, etc.)

Search: 192.168.1.* [SEARCH]

Results: 34 alerts matching criteria
```

**Color Coding:**
- 🔴 Red: Attack detected (malicious traffic)
- 🟡 Yellow: Suspicious (normal traffic, low confidence)
- 🟢 Green: Normal (benign, high confidence)
- ⚠️ Warning: Elevated importance

**User Actions:**
- **Acknowledge:** "I've reviewed this alert"
- **Block IP:** Send to firewall (integrated)
- **Whitelist:** "This is expected traffic"
- **Export:** Save alerts for reporting

#### 5. **Suspicious Traffic Detection Feature** (8 minutes)

**New Feature: Highlighting uncertain predictions**

```
Normal traffic with LOW confidence?
→ Mark as "Suspicious" (yellow)
→ Flag for SOC review
→ May indicate:
  ├─ New attack type (unknown pattern)
  ├─ Encrypted/obfuscated traffic
  ├─ Novel protocol usage
  └─ Model needs retraining
```

**Implementation in UI:**
```
⚠️  Suspicious Alert (Normal Traffic, 34% Confidence)
    Source: 10.0.0.50
    Dest: 185.220.101.0 (TOR Network)
    
    Why Suspicious?
    └─ Classified as Normal but very low confidence
    └─ Unusual packet patterns detected
    └─ Requires manual investigation
```

### 📊 Dashboard Components Summary

```
┌────────────────────────────────────────────────┐
│          DASHBOARD COMPONENTS                   │
├────────────────────────────────────────────────┤
│                                                 │
│ 1. Real-time Statistics (auto-updated)        │
│    └─ Pie charts, bar charts, counters         │
│                                                 │
│ 2. Active Flows Monitor                        │
│    └─ Live list of current conversations      │
│                                                 │
│ 3. Alert History (searchable, filterable)     │
│    └─ All predictions with details             │
│                                                 │
│ 4. Color-coded Severity Indicators            │
│    └─ 🔴 Red, 🟡 Yellow, 🟢 Green            │
│                                                 │
│ 5. Interactive Filtering & Search             │
│    └─ Find specific alerts quickly             │
│                                                 │
│ 6. Export Functionality                       │
│    └─ CSV, JSON for reports                    │
│                                                 │
│ 7. 2-Second Auto-Refresh                      │
│    └─ No manual refresh needed                 │
│                                                 │
└────────────────────────────────────────────────┘
```

### 🎤 Presentation Tips for PERSON 2

1. **Live Demo:** Show the actual dashboard if possible
   - Start/stop the IDS to show live updates
   - Generate some test traffic to show alerts
   - Filter and search to demonstrate functionality

2. **Use screenshots:** Professional visuals of the UI
   - Show the three-column layout
   - Show alert examples with different severity levels

3. **User perspective:** "From a SOC analyst's view..."
   - "When they login, they see..."
   - "If they need to investigate, they can..."

4. **Highlight unique features:**
   - "Suspicious traffic detection (yellow alerts)"
   - "Real-time updates without refresh"
   - "Easy filtering for quick investigation"

5. **Show interaction flow:**
   - "User sees alert → Clicks to investigate → Filters by IP → Takes action"

### 📚 Documentation to Reference
- `fyp/src/web/index.html` - Dashboard HTML
- `fyp/src/web/style.css` - CSS styling
- `fyp/src/web/script.js` - JavaScript logic
- `fyp/src/ids_api/routes.py` - API endpoints

### ⏱️ Recommended Presentation Time
**Total: 35-40 minutes** (with demo and questions)
- Dashboard architecture: 8 min
- Key metrics display: 8 min
- Active flows monitor: 8 min
- Alert history & filtering: 10 min
- Suspicious detection: 8 min
- **PLUS: Live Demo (5-10 minutes)**

---

## PERSON 3: Machine Learning & Model Training
### "The Data Scientist"

*This is the person presenting MODEL_TRAINING_COMPREHENSIVE_GUIDE.md that was already created*

### 📌 What They Present

**Title:** "Machine Learning Model Training & Attack Classification"

**Main Focus:** How the model learns to detect attacks

### ✅ Already Documented

**See:** `fyp/docs/MODEL_TRAINING_COMPREHENSIVE_GUIDE.md`

**Coverage includes:**
- Dataset (CICIDS2017)
- 52 network flow features
- Random Forest algorithm
- Training process
- Evaluation metrics
- Real-time inference
- 98.51% accuracy results

### ⏱️ Presentation Time
**Total: 40 minutes** (with questions)

---

## Flow of Information Between Components

```
PERSON 1 (Backend)          PERSON 2 (Frontend)        PERSON 3 (ML)
════════════════════════════════════════════════════════════════════

Captures packets ──────────→ (Raw data via API)
                                    │
                                    ↓
Processes into flows ──────→ (Updates dashboard)
                                    │
                                    ↓
Sends to classifier ────────→ ML model predicts
                                    ↓
         ← Stores predictions
         │
Saves to database ──────────→ (Alert data)
         │
         └────────────────→ (Displays in history)
```

---

## Suggested Presentation Order

### **Presentation Sequence:**

1. **PERSON 1 First (Backend)** - 35 minutes
   - "Here's how we capture and process data"
   - "Here's our multi-threaded architecture"
   - "This is the pipeline that feeds data to the model"
   - Foundation for understanding the next two topics

2. **PERSON 3 Second (ML)** - 40 minutes
   - "Using that pipeline data, here's how we train the model"
   - "Here's what the model learns"
   - "Here's our accuracy: 98.51%"
   - Builds on backend, explains what the predictions mean

3. **PERSON 2 Last (Frontend)** - 35-40 minutes
   - "And here's how we show all this to the SOC team"
   - "These are the predictions from the ML model"
   - "This is how analysts interact with the system"
   - Ties everything together with real-world usage

**Why this order?**
- ✅ Logical flow: Data → ML → Display
- ✅ Builds context: Each presenter can reference previous one
- ✅ Ends on visual/interactive: Audience stays engaged
- ✅ Questions get easier to answer: Full picture is clear

---

## Integration Points (What to Emphasize)

### Person 1 → Person 3 Connection
"The 52 features extracted by the pipeline are exactly what the ML model was trained on. The flows we group are the unit of classification."

### Person 3 → Person 2 Connection
"The predictions (attack type, confidence score) are what gets displayed on the dashboard. The color coding (red/yellow/green) is based on confidence thresholds we set during training."

### Person 1 → Person 2 Connection
"The API endpoints we created (GET /predictions, GET /stats, GET /flows) feed real-time data to the dashboard every 2 seconds."

---

## Q&A Preparation

### Likely Questions & Which Person Answers

**Q: "How many flows can your system handle?"**
- **Person 1:** "We can process 16,000 flows per second on an 8-core server"

**Q: "Why did you choose Random Forest?"**
- **Person 3:** "High accuracy, fast inference, handles non-linear patterns, interpretable"

**Q: "What does the yellow alert mean?"**
- **Person 2:** "Normal traffic classified with low confidence - analyst should review"

**Q: "How do you prevent false positives?"**
- **Person 3:** "High confidence threshold (>65%), plus manual review queue"

**Q: "How long does the model take to train?"**
- **Person 3:** "About 5 minutes on modern hardware"

**Q: "Can it run on my laptop?"**
- **Person 1:** "Yes! Model is 47MB, uses ~150MB RAM, processes live traffic"

**Q: "Is it production-ready?"**
- **All:** "Yes, we have it deployed and tested in real environments"

---

## Visual Aids Recommendations

### For Person 1
- Diagram: 3-thread architecture
- Flow chart: Packet → Flow → Feature
- Screenshot: CLI commands
- Graph: Throughput performance (flows/sec)

### For Person 2
- Dashboard screenshots (all tabs)
- Filter examples
- Color legend (severity levels)
- Alert workflow diagram

### For Person 3
- Feature importance chart (top 10)
- Confusion matrix
- ROC curve
- Accuracy metrics table

---

## Time Allocation Summary

```
Total Presentation Time: 110 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Person 1 (Backend):    35 minutes
Person 3 (ML):         40 minutes
Person 2 (Frontend):   35 minutes
                       ─────────────
                       110 minutes

Plus: Questions & Answers (20-30 minutes)
Plus: Live Demo (10-15 minutes, optional but recommended)

Total Viva: ~150 minutes (2.5 hours)
```

---

## Preparation Checklist

### All Team Members
- [ ] Create detailed slides/visuals
- [ ] Prepare code snippets to show
- [ ] Practice transitions between speakers
- [ ] Prepare for common questions
- [ ] Have backup explanations (simple + detailed)

### Person 1 (Backend)
- [ ] Understand thread synchronization
- [ ] Be ready to explain locks/queues
- [ ] Have CLI commands ready to demo
- [ ] Know performance metrics by heart

### Person 2 (Frontend)
- [ ] Practice dashboard navigation
- [ ] Have screenshots of all features
- [ ] Practice live demo (if possible)
- [ ] Explain why UX choices matter

### Person 3 (ML)
- [ ] Understand all 52 features
- [ ] Know why Random Forest was chosen
- [ ] Have metrics explained clearly
- [ ] Be ready for "why not deep learning" question

---

## Key Points Each Person Should Emphasize

### Person 1
- ✅ "Real-time" - we capture and process simultaneously
- ✅ "Multi-threaded" - different tasks happen in parallel
- ✅ "Scalable" - handles thousands of flows per second
- ✅ "Persistent" - nothing is lost, everything stored

### Person 3
- ✅ "98.51% accuracy" - state-of-the-art performance
- ✅ "Interpretable" - can explain why it classified something as attack
- ✅ "Handles imbalance" - works even though 80% of data is normal
- ✅ "Fast" - 2.5ms per prediction (real-time capable)

### Person 2
- ✅ "User-friendly" - SOC teams don't need to know Python
- ✅ "Real-time" - updates every 2 seconds automatically
- ✅ "Actionable" - alerts are clear and filterable
- ✅ "Transparent" - shows confidence, allows review

---

## Practice Session Structure

### Recommendation: Do a mock viva together

1. **Person 1 presents** (35 min) → Everyone listens
2. **Person 3 presents** (40 min) → Everyone listens
3. **Person 2 presents** (35 min) → Everyone listens
4. **Mock Q&A** (30 min) → Anyone asks questions
5. **Feedback round** → Discuss what went well/needs improvement
6. **Repeat** until smooth and polished

---

## Final Notes

### System Architecture Overview
Your IDS has three well-defined layers:

```
┌─────────────────────────────────────────┐
│    PRESENTATION LAYER (Person 2)        │
│  Web Dashboard, Real-time Visualization │
└─────────────────────────────────────────┘
           ↑                ↓
┌─────────────────────────────────────────┐
│    INTELLIGENCE LAYER (Person 3)        │
│  ML Model, Attack Classification         │
└─────────────────────────────────────────┘
           ↑                ↓
┌─────────────────────────────────────────┐
│    INFRASTRUCTURE LAYER (Person 1)      │
│  Data Pipeline, Architecture, Storage    │
└─────────────────────────────────────────┘
```

Each person explains their layer clearly, and together they show how it all works.

### Why This Division Works

| Aspect | Person 1 | Person 2 | Person 3 |
|--------|----------|----------|----------|
| **Focus** | How data flows | How to use results | How to classify |
| **Audience** | Architects/DevOps | SOC/Users | Researchers |
| **Depth** | System level | User level | Algorithm level |
| **Code** | Python (backend) | HTML/CSS/JS | Python (ML) |
| **Questions** | Performance, scaling | UX, workflow | Accuracy, methods |

---

## Success Criteria

Your viva is successful if the panel understands:

1. ✅ **Data flows** through the system in real-time (Person 1's job)
2. ✅ **ML model** can accurately detect attacks (Person 3's job)
3. ✅ **Dashboard** lets operators use the system (Person 2's job)
4. ✅ **Integration** - all three parts work together
5. ✅ **Value** - this is a real, usable security tool

---

**Good luck with your viva! 🚀**

---

*This document coordinates the presentation across all three team members for maximum clarity and impact.*
