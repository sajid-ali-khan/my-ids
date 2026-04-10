# Suspicious Classification - Implementation Summary

## Quick Reference

### What Changed
✅ **Detected:** Normal/Benign traffic with confidence < 65% is now marked as "Suspicious"  
✅ **Stored:** Automatically saved to database with LOW severity  
✅ **Displayed:** Alert History tab shows Suspicious filter option  
✅ **Styled:** Yellow highlighting with ⚠️  emoji badge  

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK PACKET CAPTURE                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   CLASSIFIER THREAD          │
        │   Extract Features & Predict │
        └──────────────┬───────────────┘
                       │
              ┌────────┴────────┐
              │                 │
         ┌────▼────┐       ┌────▼────┐
         │Prediction│      │Confidence│
         └────┬────┘       └────┬────┘
              │                 │
              └────────┬────────┘
                       │
         ┌─────────────▼──────────────┐
         │ _is_suspicious_traffic()   │
         │                            │
         │ IF (normal/benign AND      │
         │     confidence < 0.65)     │
         │   THEN suspicious = TRUE   │
         └─────────────┬──────────────┘
                       │
           ┌───────────┴───────────┐
   ┌───────▼────────┐    ┌────────▼────────┐
   │   SUSPICIOUS   │    │   ATTACK OR     │
   │   TRAFFIC      │    │   CONFIDENT     │
   │  confidence    │    │   BENIGN        │
   │   < 0.65%      │    │                 │
   └───────┬────────┘    └────────┬────────┘
           │                      │
      ┌────▼───────┐         ┌────▼──────┐
      │ severity:  │         │ severity: │
      │ "low"      │         │ based on  │
      │ type:      │         │ conf %    │
      │ "Suspicious"         │ type:     │
      └────┬───────┘         │ original  │
           │                 └────┬──────┘
           │                      │
           └──────────┬───────────┘
                      │
         ┌────────────▼─────────────┐
         │  _save_alert_if_attack() │
         │   (Save to Database)     │
         └────────────┬─────────────┘
                      │
         ┌────────────▼──────────────┐
         │   ALERTS TABLE            │
         │   ├─ timestamp            │
         │   ├─ src_ip/dst_ip        │
         │   ├─ attack_type: *       │
         │   │   "Suspicious" ← NEW  │
         │   ├─ confidence: < 0.65   │
         │   ├─ severity: "low"      │
         │   └─ ...                  │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │  FRONTEND DASHBOARD       │
         │  Alert History Tab        │
         │                           │
         │  Filter: ⚠️  Suspicious   │
         │  Row Style: Yellow        │
         │  Visual: ⚠️  Badge        │
         └──────────────────────────┘
```

---

## Code Changes Summary

### File: `ids_core/pipeline.py`

**New Method (Line 273-283):**
```python
def _is_suspicious_traffic(self, prediction: str, confidence: float) -> bool:
    """Check if traffic is suspicious (normal/benign with low confidence)."""
    is_benign = prediction == 'Benign' or prediction == 'Normal Traffic'
    is_low_confidence = confidence < 0.65
    return is_benign and is_low_confidence
```

**Modified Method (Line 290-362):**
```python
def _save_alert_if_attack(self, pred_record, flow, prediction, confidence):
    # Check for suspicious traffic
    is_suspicious = self._is_suspicious_traffic(prediction, confidence)
    
    # If suspicious, save with special handling
    if is_suspicious:
        attack_type = 'Suspicious'
        severity = 'low'
    else:
        # Regular attack handling
        attack_type = prediction
        severity = determine_severity(confidence)
    
    # Save to database
    save_alert(alert_dict)
```

**Classifier Output (Line 579-590):**
```python
# Check for suspicious traffic
is_suspicious = self._is_suspicious_traffic(prediction, confidence_val)

# Console output with warning
if is_suspicious:
    print(f"⚠️  SUSPICIOUS TRAFFIC (normal/benign with low confidence)")

print(f"Prediction: {prediction}")
print(f"Confidence: {confidence_val:.4f}")

# Save to database (now includes suspicious)
self._save_alert_if_attack(pred_record, flow, prediction, confidence_val)
```

---

### File: `web/index.html`

**Added Filter Option (Line 229-231):**
```html
<option value="Suspicious">⚠️  Suspicious</option>
```

---

### File: `web/style.css`

**New Styles (Line 808-827):**
```css
.table-alerts .attack-type-suspicious {
    background-color: #fff3cd;
    color: #856404;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    border-left: 3px solid #ffc107;
}

.table-alerts tbody tr.suspicious-row {
    background-color: #fffbf0;
}

.table-alerts tbody tr.suspicious-row:hover {
    background-color: #fff8e6;
}
```

---

### File: `web/script.js`

**Updated Rendering (Line 477-519):**
```javascript
// Check if this is a suspicious alert
const isSuspicious = alert.attack_type === 'Suspicious';
const rowClass = isSuspicious ? 'suspicious-row' : '';
const attackTypeClass = isSuspicious ? 'attack-type-suspicious' : '';
const attackTypeDisplay = isSuspicious ? '⚠️  ' + escapeHtml(alert.attack_type) : escapeHtml(alert.attack_type);

// Render with appropriate styling
return `
    <tr class="${rowClass}">
        <td>${escapeHtml(timestamp.split(' ')[1])}</td>
        <td><span class="${severityClass}">${escapeHtml(alert.severity.toUpperCase())}</span></td>
        <td><span class="${attackTypeClass}">${attackTypeDisplay}</span></td>
        ...
    </tr>
`;
```

---

## Configuration

### Confidence Threshold
**Current:** 65% (0.65)  
**Location:** `ids_core/pipeline.py` line 280  
**Adjust for:**
- More Aggressive: Lower to 0.50 (more suspicious alerts)
- More Conservative: Raise to 0.75 (fewer suspicious alerts)

### Severity Level
**Current:** "low"  
**Location:** `ids_core/pipeline.py` line 324  
**Options:** "critical", "high", "medium", "low"

---

## Visual Example

### Dashboard Display

```
Alert History Tab - Suspicious Alerts Highlighted

┌─────────────────────────────────────────────────────────────────┐
│ Filter: Attack Type [⚠️  Suspicious ▼]                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Time    │Severity│Attack Type      │Source        │Dest    │ % │
├─────────────────────────────────────────────────────────────────┤
│22:45:31 │ LOW    │⚠️  Suspicious   │192.168.1.1  │8.8.8.8 │62%│ ←← Yellow bg
│         │        │                │:5432        │:443    │   │
├─────────────────────────────────────────────────────────────────┤
│22:43:15 │ LOW    │⚠️  Suspicious   │192.168.1.2  │1.1.1.1 │58%│ ←← Yellow bg
│         │        │                │:51234       │:443    │   │
├─────────────────────────────────────────────────────────────────┤
│22:40:22 │CRITICAL│SSH Brute Force  │192.168.1.3  │10.0.0.1│94%│
│         │        │                │:22211       │:22     │   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Testing

### Run Test Suite
```bash
cd /home/sajid/Desktop/fyp
python3 test_suspicious_classification.py
```

### Expected Output
```
✓ ALL TESTS PASSED - Suspicious classification feature ready!

FEATURE SUMMARY:
1. DETECTION LOGIC
   - Normal/Benign traffic with confidence < 65% → marked as 'Suspicious'
   
2. FRONTEND DISPLAY
   - Alert History tab shows 'Suspicious' filter option
   - Suspicious rows highlighted with warning styling
   - ⚠️  emoji prefix in attack type column
   
3. FILTERING & EXPORT
   - Filter suspicious alerts by attack type
   - CSV export includes suspicious classifications
```

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `ids_core/pipeline.py` | Added `_is_suspicious_traffic()` method; Modified `_save_alert_if_attack()` to handle suspicious traffic; Updated classifier console output | +90 lines |
| `web/index.html` | Added "Suspicious" filter option | +1 option |
| `web/style.css` | Added `.attack-type-suspicious` and `.suspicious-row` styles | +20 lines |
| `web/script.js` | Updated `updateAlertTable()` for suspicious rendering | +5 lines |

---

## Verification Checklist

- [x] Suspicious detection logic implemented
- [x] Database storage confirmed
- [x] Frontend filter added
- [x] CSS styling created
- [x] JavaScript rendering updated
- [x] Test suite passes
- [x] Documentation created
- [x] Console output shows suspicious warnings
- [x] HTML structure valid
- [x] No JavaScript errors

---

## Deployment Notes

1. **No Database Migration Needed** - Uses existing alerts table
2. **No Frontend Rebuild** - Just static files
3. **No Configuration Change Required** - Works with defaults
4. **Backward Compatible** - Existing alerts unaffected
5. **Can Be Deployed Immediately** - No dependencies added

---

## Monitoring the Feature

### Console Logs
Watch for this output when suspicious traffic detected:
```
⚠️  SUSPICIOUS TRAFFIC (normal/benign with low confidence)
[DB] ⚠️  Saved SUSPICIOUS alert: 192.168.1.1:5432 -> 8.8.8.8:443 (confidence: 62.34%)
```

### Database Query
Check how many suspicious alerts stored:
```sql
sqlite3 /opt/nids/alerts.db \
  "SELECT attack_type, COUNT(*) as count FROM alerts GROUP BY attack_type;"
```

### Alert Statistics
Suspicious alerts are included in all alert counts and filters.

---

**Status:** ✅ Production Ready  
**Date:** April 2026  
**All Tests:** ✅ Passing
