# Configuration Management - API Endpoints

## Overview

The IDS system now supports **dynamic configuration management** without requiring server restart. Configuration parameters can be:
1. Retrieved via REST API
2. Updated via REST API (from the dashboard)
3. Persisted to the config file (`~/.ids/config.json`)
4. Set via environment variables on startup

---

## Configuration Parameters

The system manages the following timeout-related parameters:

| Parameter | Type | Min Value | Default | Description |
|-----------|------|-----------|---------|-------------|
| `flusher_interval` | int | 1 | 20 | Seconds between flusher thread checks for idle flows |
| `idle_timeout` | int | 1 | 30 | Seconds before an inactive flow is considered expired |
| `max_history` | int | 1 | 100 | Maximum number of predictions stored in history |

---

## GET /api/config

**Retrieve current configuration**

### Request
```bash
curl http://localhost:5000/api/config
```

### Response (200 OK)
```json
{
  "network_interface": "wlp3s0",
  "flusher_interval": 20,
  "idle_timeout": 30,
  "max_history": 100,
  "features_count": 52,
  "model_type": "RandomForestClassifier"
}
```

---

## POST /api/config

**Update configuration parameters**

### Request
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "flusher_interval": 15,
    "idle_timeout": 25,
    "max_history": 150
  }'
```

### Response (200 OK - Success)
```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "config": {
    "flusher_interval": 15,
    "idle_timeout": 25,
    "max_history": 150
  }
}
```

### Response (400 Bad Request - Invalid Value)
```json
{
  "error": "flusher_interval must be > 0"
}
```

### Response (400 Bad Request - Invalid Type)
```json
{
  "status": "error",
  "message": "Invalid parameter format: invalid literal for int() with base 10: 'abc'"
}
```

### Response (500 Server Error)
```json
{
  "status": "error",
  "message": "Failed to save configuration"
}
```

---

## Configuration Precedence (on startup)

When the server starts, configuration is loaded in this order:

1. **Config File** (`~/.ids/config.json`) - **Highest Priority**
2. **Environment Variables**:
   - `IDS_FLUSHER_INTERVAL`
   - `IDS_IDLE_TIMEOUT`
   - `IDS_MAX_HISTORY`
3. **Code Defaults** - **Lowest Priority**
   - flusher_interval: 20
   - idle_timeout: 30
   - max_history: 100

---

## Usage Examples

### Example 1: Make flows expire faster (for aggressive detection)
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "flusher_interval": 10,
    "idle_timeout": 15
  }'
```

### Example 2: Make flows expire slower (reduce CPU load)
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "flusher_interval": 30,
    "idle_timeout": 60
  }'
```

### Example 3: Increase prediction history for better analytics
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"max_history": 500}'
```

### Example 4: Set via environment variables (on startup)
```bash
export IDS_FLUSHER_INTERVAL=10
export IDS_IDLE_TIMEOUT=20
export IDS_MAX_HISTORY=200
python -m ids_cli.cli start
```

### Example 5: Set in config file

Edit `~/.ids/config.json`:
```json
{
  "interface": "wlp3s0",
  "port": 5000,
  "model_dir": "/home/sajid/.ids/model",
  "debug": false,
  "host": "0.0.0.0",
  "flusher_interval": 10,
  "idle_timeout": 20,
  "max_history": 200
}
```

Then restart the server:
```bash
python -m ids_cli.cli stop
python -m ids_cli.cli start
```

---

## Impact of Configuration Changes

### Reducing `flusher_interval`
- **Effect**: Flows are checked for expiry more frequently
- **Use When**: You need aggressive flow cleanup (higher CPU use)
- **Example**: 20s → 10s (checks twice as often)

### Reducing `idle_timeout`
- **Effect**: Inactive flows expire sooner, fewer flows in memory
- **Use When**: Dealing with low-memory systems or high-traffic networks
- **Example**: 30s → 15s (flows timeout faster)

### Increasing `max_history`
- **Effect**: More predictions stored for dashboard analytics
- **Use When**: You want longer historical data
- **Example**: 100 → 500 (5x more predictions in memory)

---

## Best Practices

1. **For Production**: Use config file, restart via `ids_cli.cli stop/start`
2. **For Testing**: Use environment variables with direct Python execution
3. **For Dashboard Tuning**: Use POST /api/config API endpoint
4. **Validation**: Always check GET /api/config after updating to confirm changes took effect

---

## How It Works (Technical)

1. **Persistence**: Changes via POST /api/config are saved to `~/.ids/config.json`
2. **Dynamic Update**: Pipeline attributes (`pipeline.flusher_interval`, etc.) are updated immediately
3. **No Restart Needed**: Changes take effect on the next flusher thread cycle or prediction
4. **Thread Safety**: Updates are safe - flusher thread reads from these attributes dynamically

---

## Troubleshooting

### Configuration changes not persisting?
```bash
# Check if config file is readable/writable
ls -la ~/.ids/config.json
chmod 644 ~/.ids/config.json
```

### Want to reset to defaults?
```bash
python -m ids_cli.cli reset-config
# Or manually edit ~/.ids/config.json to match DEFAULTS
```

### Dashboard doesn't reflect changes?
```bash
# Verify API endpoint
curl http://localhost:5000/api/config | jq .

# Check if server is running
ps aux | grep run_server
```

---

## Integration with Dashboard

The dashboard can now:

1. **Display current settings** - Call GET /api/config
2. **Provide UI controls** - Input fields for each parameter
3. **Update settings** - POST to /api/config with new values
4. **Validate inputs** - Check that values are > 0
5. **Show confirmation** - Display success/error messages

Example React component:
```javascript
const updateConfig = async (config) => {
  const response = await fetch('http://localhost:5000/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  return response.json();
};
```

