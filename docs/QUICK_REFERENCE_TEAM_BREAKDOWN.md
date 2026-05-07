# Quick Reference: Team Presentation Breakdown
## Who Presents What?

```
YOUR NETWORK IDS PROJECT
═════════════════════════════════════════════════════════════════

                    3 MAIN COMPONENTS
                    
PERSON 1            PERSON 2            PERSON 3
BACKEND             FRONTEND            ML MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"How we capture      "How users see      "How we detect
 & process data"     the results"        attacks"
```

---

## PERSON 1: Backend/Data Pipeline & Architecture
### 35 minutes

**What you explain:**

1. **Packet Capture & Flow Aggregation** (10 min)
   - How Scapy captures 10,000+ packets/sec
   - How we group packets into flows (conversations)
   - Example: SSH brute force attack = multiple failed login flows

2. **Multi-Threaded Pipeline** (10 min)
   - 3 threads: Sniffer → Flusher → Classifier
   - Why we need parallel processing
   - Thread-safe data structures
   - Performance: 16,000 flows/second

3. **Database & Alert Storage** (5 min)
   - SQLite database for persistent storage
   - What data gets saved
   - How to query historical alerts

4. **Flow Aggregation** (5 min)
   - Multi-flow attacks (brute force, port scanning)
   - 60-second aggregation windows
   - Detecting coordinated attacks

5. **CLI & Configuration** (5 min)
   - How operators use: `ids-cli setup`, `ids-cli start`
   - Configuration file structure
   - Cross-platform support

**Key Files:**
- `src/ids_core/pipeline.py` - Main pipeline logic
- `src/ids_cli/cli.py` - CLI commands
- `src/ids_core/flow_aggregator.py` - Flow aggregation
- `src/ids_core/store/db.py` - Database operations

**Key Points to Emphasize:**
- ✅ "Real-time processing"
- ✅ "Multi-threaded for scalability"
- ✅ "Handles thousands of flows"
- ✅ "Persistent alert storage"

---

## PERSON 2: Frontend/Dashboard & Visualization
### 35-40 minutes (+ optional 5-10 min live demo)

**What you explain:**

1. **Dashboard Architecture** (8 min)
   - Three-column layout
   - HTML5 + CSS3 + JavaScript (no framework)
   - AJAX polling every 2 seconds
   - Real-time updates

2. **Statistics Display** (8 min)
   - Total flows, normal/attack ratio
   - Breakdown by attack type (DoS, DDoS, Brute Force, Web, Bot, Infiltration)
   - Real-time pie/bar charts

3. **Active Flows Monitor** (8 min)
   - Live list of current network conversations
   - Source/dest IP, ports, packet counts, confidence
   - Sorting and filtering by IP
   - 2-second refresh rate

4. **Alert History & Filtering** (10 min)
   - Alert table with all details
   - Advanced filtering (date, attack type, IP, severity, confidence)
   - User actions: Acknowledge, Block, Whitelist, Export
   - Color coding: 🔴 Red (attack), 🟡 Yellow (suspicious), 🟢 Green (normal)

5. **Suspicious Traffic Detection** (8 min)
   - Yellow alerts for normal traffic with low confidence
   - Indicates potential new/unknown attacks
   - Flags for SOC team manual review

**Key Files:**
- `src/web/index.html` - Dashboard HTML
- `src/web/style.css` - CSS styling
- `src/web/script.js` - JavaScript/AJAX logic
- `src/ids_api/routes.py` - Backend API endpoints

**Key Points to Emphasize:**
- ✅ "User-friendly for SOC teams"
- ✅ "Real-time without manual refresh"
- ✅ "Actionable alerts"
- ✅ "Easy to investigate specific IPs"

**Preparation:**
- 📸 Have screenshots of all dashboard sections
- 🎥 Practice live demo (if possible)
- 📝 Show example alert workflows

---

## PERSON 3: Machine Learning & Model Training
### 40 minutes

**What you explain:**

1. **Dataset** (5 min)
   - CICIDS2017: 100,000 network flows
   - 7 classes: Normal + 6 attack types
   - Class distribution: 80% Normal, 20% attacks
   - Imbalanced data handling

2. **52 Network Features** (10 min)
   - Flow statistics (duration, packet count, bytes)
   - Inter-arrival time patterns (critical for attack detection)
   - Directional differences (forward vs backward)
   - TCP flags (FIN, PSH, ACK)
   - Active/Idle periods
   - Example: "Regular timing = human, irregular timing = bot"

3. **Random Forest Algorithm** (8 min)
   - Why: Accuracy + Speed + Interpretable
   - 100 decision trees
   - Each tree votes, majority wins
   - Feature importance analysis

4. **Training Process** (8 min)
   - 80-20 train/test split
   - 5-fold cross-validation
   - Training on 80,000 samples
   - Takes ~5 minutes

5. **Results & Metrics** (9 min)
   - **98.51% overall accuracy**
   - Per-class performance (DoS: 98%, DDoS: 95%, Rare: 78-85%)
   - Confusion matrix
   - Precision, Recall, F1-Score
   - Real-world interpretation

**Key Files:**
- `notebooks/random_forest_cicids2017_v2.ipynb` - Training notebook
- `src/ids_core/model_loader.py` - Model loading
- `scripts/flow.py` - Feature extraction
- `fyp/docs/MODEL_TRAINING_COMPREHENSIVE_GUIDE.md` - Detailed guide

**Key Points to Emphasize:**
- ✅ "98.51% accuracy"
- ✅ "Fast inference (2.5ms per flow)"
- ✅ "Handles imbalanced data"
- ✅ "Interpretable results"

---

## RECOMMENDED PRESENTATION ORDER

### ✅ Optimal Sequence:

1. **PERSON 1 First** (Data Pipeline)
   - Lays foundation: "Here's how data flows"
   
2. **PERSON 3 Second** (ML Model)
   - "Using that data, here's how we detect attacks"
   
3. **PERSON 2 Last** (Dashboard)
   - "And here's how operators see it all"

**Why this order?**
- Logical flow: Data → Intelligence → Display
- Each builds on previous
- Ends with visual/interactive (holds attention)

---

## TIME BREAKDOWN

```
Person 1:  35 minutes (Backend)
Person 3:  40 minutes (ML)
Person 2:  35 minutes (Frontend)
────────────────────────────────
Subtotal:  110 minutes

Plus: Q&A (20-30 min)
Plus: Optional Live Demo (10-15 min)

TOTAL:     ~150 minutes (2.5 hours)
```

---

## KEY INTEGRATION POINTS

**Connection between Person 1 & 3:**
- "The 52 features extracted by our pipeline are exactly what the ML model trains on"

**Connection between Person 3 & 2:**
- "The predictions from the model (attack type + confidence) are displayed on the dashboard"
- "Color coding is based on confidence thresholds: >65% red, 35-65% yellow, <35% green"

**Connection between Person 1 & 2:**
- "API endpoints feed live data to the dashboard every 2 seconds"

---

## PREPARATION CHECKLIST

### ALL MEMBERS
- [ ] Create detailed slides/visuals
- [ ] Prepare code snippets to show
- [ ] Practice transitions between speakers
- [ ] Mock viva session (full run-through)

### PERSON 1 (Backend)
- [ ] Diagram: 3-thread architecture
- [ ] Flowchart: Packet → Flow → Feature
- [ ] CLI commands demo ready
- [ ] Performance numbers memorized

### PERSON 2 (Frontend)
- [ ] Dashboard screenshots (all sections)
- [ ] Optional: Live demo setup
- [ ] User workflow examples
- [ ] Color legend & alert types

### PERSON 3 (ML)
- [ ] Feature importance visualization
- [ ] Confusion matrix
- [ ] Accuracy metrics table
- [ ] ROC curve

---

## COMMON VIVA QUESTIONS

**Q: "How many flows per second?"**
- Person 1: "16,000 flows/sec on 8-core server"

**Q: "Why Random Forest?"**
- Person 3: "98% accuracy, 2.5ms inference, interpretable"

**Q: "What's the yellow alert?"**
- Person 2: "Normal traffic, low confidence - needs review"

**Q: "Can it detect unknown attacks?"**
- Person 3: "No, only trained classes. But 'suspicious' alerts flag odd patterns"

**Q: "How long to train?"**
- Person 3: "~5 minutes, can retrain monthly with new data"

**Q: "Is it production-ready?"**
- All: "Yes, deployed and tested"

---

## SUCCESS CRITERIA

Panel should understand:

1. ✅ **Data Pipeline** - How network traffic is captured and processed (Person 1)
2. ✅ **ML Model** - How attacks are detected and classified (Person 3)
3. ✅ **Dashboard** - How operators use the system (Person 2)
4. ✅ **Integration** - How all three parts work together
5. ✅ **Value** - Why this is a real, useful security tool

---

## VIVA TALKING POINTS

### Overall Project:
*"We built a production-ready Network Intrusion Detection System that captures network traffic in real-time, extracts intelligent features, classifies traffic with a machine learning model at 98.51% accuracy, and presents results to security analysts through an intuitive dashboard."*

### Technical Excellence:
*"The system processes 16,000 flows per second using multi-threaded architecture, trains to 98.51% accuracy on 100,000 flows, and makes predictions in 2.5 milliseconds - suitable for real-time deployment."*

### Real-World Ready:
*"We designed it for actual SOC teams to use: persistent storage for compliance, advanced filtering, confidence scores, and manual review capabilities."*

---

**Document created:** April 2026  
**Status:** Ready for Viva Presentation  
**Team:** 3 Members (Backend, ML, Frontend)
