# IDS Deployment Checklist

Use this checklist to verify your IDS installation is complete and working correctly.

## Pre-Installation ✓

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Git installed (if cloning repository)
- [ ] 200MB+ disk space available
- [ ] Network interface identified
- [ ] Port 5000 (or chosen port) is available
- [ ] Administrator/root access for packet capture (Linux/macOS)

## Installation

### Option 1: pip Installation

- [ ] Repository cloned/downloaded
- [ ] Virtual environment created (recommended)
- [ ] Virtual environment activated
- [ ] `pip install .` completed successfully
- [ ] No dependency conflicts reported
- [ ] `ids-cli --help` shows help menu
- [ ] `which ids-cli` shows correct path

### Option 2: Bash Script Installation

- [ ] Repository cloned/downloaded
- [ ] `chmod +x install.sh` executed
- [ ] `./install.sh` completed without errors
- [ ] Script reported all steps successful
- [ ] `~/.ids/` directory created
- [ ] `/usr/local/bin/ids-cli` symlink exists (or `~/.local/bin/ids-cli`)
- [ ] Shell configuration updated (.bashrc/.zshrc)
- [ ] Shell reloaded (`source ~/.bashrc`)
- [ ] `ids-cli --help` shows help menu

### Option 3: Manual Installation

- [ ] Repository cloned/downloaded
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] `~/.ids/` directory created
- [ ] `python3 ids_cli.py --help` shows help menu

## Configuration ✓

- [ ] `ids-cli setup` executed (or manual config)
- [ ] `~/.ids/config.json` created
- [ ] Network interface selected and valid
- [ ] Port configured (default 5000)
- [ ] Model directory path verified
- [ ] `./model/random_forest_model.pkl` exists
- [ ] `./model/model_columns.joblib` exists
- [ ] Config readable: `ids-cli config`

## First Startup ✓

- [ ] `ids-cli start` executed successfully
- [ ] No permission errors reported
- [ ] `ids-cli status` shows "Running"
- [ ] `~/.ids/server.pid` file created
- [ ] Process visible: `ps aux | grep ids` or `pid` command
- [ ] `~/.ids/server.log` file created with entries

## Dashboard Access ✓

- [ ] Browser open to `http://localhost:5000`
- [ ] Dashboard loads without 404 errors
- [ ] Header visible with "IDS Dashboard"
- [ ] Left panel shows: Status, Stats, Config sections
- [ ] Middle panel shows: "Active Flows" table (may be empty)
- [ ] Right panel shows: "Recent Predictions" table
- [ ] Refresh button works

## Network Monitoring ✓

- [ ] Generate network traffic (e.g., `ping 8.8.8.8`)
- [ ] Dashboard shows flows appearing
- [ ] Flows have source/destination IPs
- [ ] Prediction scores display with confidence
- [ ] Benign traffic shows green indicator
- [ ] Statistics update in real-time
- [ ] Attack class breakdown updates

## CLI Commands Verification ✓

Test each command:

```bash
# Information
ids-cli info                    # [ ] Shows welcome/help
ids-cli config                  # [ ] Shows current config
ids-cli status                  # [ ] Shows running status

# Logs
ids-cli logs -n 10             # [ ] Shows recent log entries
ids-cli logs -n 100            # [ ] Shows more entries

# Control
ids-cli stop                    # [ ] Server stops
ids-cli status                  # [ ] Shows stopped status
ids-cli start                   # [ ] Server starts again

# Configuration
ids-cli reset                   # [ ] Resets to defaults
ids-cli config                  # [ ] Shows reset config
ids-cli setup                   # [ ] Reconfigures system
```

Mark each command:
- [ ] ids-cli info
- [ ] ids-cli setup
- [ ] ids-cli start
- [ ] ids-cli status
- [ ] ids-cli stop
- [ ] ids-cli logs
- [ ] ids-cli config
- [ ] ids-cli reset

## API Endpoints ✓ (Optional)

Test REST API directly (while server running):

```bash
# Health check
curl http://localhost:5000/health
- [ ] Returns 200 OK

# Get status
curl http://localhost:5000/api/status
- [ ] Returns JSON with status

# Get summary
curl http://localhost:5000/api/summary
- [ ] Returns statistics and predictions

# Get flows
curl http://localhost:5000/api/flows
- [ ] Returns active flows JSON

# Get stats
curl http://localhost:5000/api/stats
- [ ] Returns stats JSON
```

## Data Persistence ✓

- [ ] Stop server: `ids-cli stop`
- [ ] Restart server: `ids-cli start`
- [ ] Configuration preserved
- [ ] Logs still exist
- [ ] Dashboard accessible

## Persistence After Reboot (Optional)

- [ ] Reboot machine
- [ ] Start IDS: `ids-cli start`
- [ ] Configuration still correct
- [ ] Server starts successfully
- [ ] Dashboard accessible
- [ ] Old logs preserved

## Troubleshooting Verification ✓

Before marking complete, verify you can:

- [ ] View logs when server crashes
- [ ] Recover from port conflicts
- [ ] Check config in case of issues
- [ ] Reset to defaults if needed
- [ ] Stop process cleanly
- [ ] Restart cleanly

## Performance Baseline ✓

- [ ] Dashboard loads in < 2 seconds
- [ ] Refresh updates in < 2 seconds
- [ ] No memory leaks (monitor with `top`)
- [ ] CPU usage reasonable during idle
- [ ] CPU spikes during active traffic
- [ ] Logs not growing excessively

## Security Verification ✓

- [ ] Server only listens on configured interface
- [ ] Port not exposed to internet (if local-only)
- [ ] Logs contain no sensitive data
- [ ] Model file permissions secure
- [ ] Config file permissions secure
- [ ] PID file cleaned up after stop

## Documentation ✓

- [ ] README.md read and understood
- [ ] INSTALL.md matched chosen method
- [ ] CLI help understood
- [ ] Dashboard features explored
- [ ] API endpoints documented
- [ ] Troubleshooting steps identified

## Production Readiness ✓

- [ ] [ ] Chose appropriate network interface
- [ ] [ ] Configured for your environment
- [ ] [ ] Tested with representative traffic
- [ ] [ ] Logs configured appropriately
- [ ] [ ] Port configured for your network
- [ ] [ ] Monitoring dashboard tested
- [ ] [ ] Restart procedure documented
- [ ] [ ] Backup strategy in place
- [ ] [ ] User training completed

## Sign-Off

**Installation Date:** _______________

**Installer Name:** _______________

**System:** _______________

**Python Version:** _______________

**Installation Method:** 
- [ ] pip
- [ ] Bash Script
- [ ] Manual

**Notes:**

```
_________________________________________________

_________________________________________________

_________________________________________________
```

---

## Next Steps

1. **Monitor regularly:** Check dashboard daily
2. **Review logs:** Monitor for errors
3. **Tune configuration:** Adjust based on performance
4. **Plan backups:** Backup trained model
5. **Document changes:** Track any modifications
6. **Schedule maintenance:** Plan regular updates

## Support Resources

- **README.md** - Feature overview and usage
- **INSTALL.md** - Detailed installation steps
- **CLI help:** `ids-cli info`
- **Logs:** `ids-cli logs`
- **Config:** `~/.ids/config.json`

---

**Congratulations! Your IDS is operational.** 🎉

Once all items above are checked, your IDS installation is complete and production-ready.

For ongoing operation, refer to the [README.md](README.md) and [INSTALL.md](INSTALL.md) documentation.
