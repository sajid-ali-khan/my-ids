"""IDS CLI - Command Line Interface for managing the IDS server"""

import click
from pathlib import Path
from .config import ConfigManager
from .daemon import DaemonManager


@click.group()
@click.version_option(version='1.0.0', prog_name='ids-cli')
def cli():
    """IDS CLI - Network Intrusion Detection System Manager"""
    pass


@cli.command()
@click.option('--interface', '-i', default=None, help='Network interface (e.g., eth0, wlp3s0, en0)')
@click.option('--port', '-p', type=int, default=None, help='Server port (default: 5000)')
@click.option('--model-dir', '-m', default=None, help='Path to model directory')
@click.option('--debug/--no-debug', default=False, help='Enable debug mode')
def setup(interface, port, model_dir, debug):
    """Initialize IDS configuration"""
    
    click.echo("🔧 IDS Configuration Setup")
    click.echo("-" * 50)
    
    config = ConfigManager.load()
    
    # Get user input for each setting
    if interface is None:
        interface = click.prompt(
            'Network interface',
            default=config.get('interface', 'eth0'),
            type=str
        )
    
    if port is None:
        port = click.prompt(
            'Server port',
            default=config.get('port', 5000),
            type=int
        )
    
    if model_dir is None:
        model_dir = click.prompt(
            'Model directory',
            default=config.get('model_dir', './model'),
            type=str
        )
    
    # Update configuration
    new_config = {
        'interface': interface,
        'port': port,
        'model_dir': model_dir,
        'debug': debug,
    }
    
    if ConfigManager.update(new_config):
        click.echo("\n✓ Configuration saved successfully!")
        click.echo(f"  Interface:  {interface}")
        click.echo(f"  Port:       {port}")
        click.echo(f"  Model Dir:  {model_dir}")
        click.echo(f"  Debug:      {debug}")
    else:
        click.echo("\n✗ Failed to save configuration", err=True)


@cli.command()
def start():
    """Start the IDS server"""
    
    click.echo("▶ Starting IDS server...")
    
    daemon = DaemonManager()
    success, message = daemon.start()
    
    if success:
        click.echo(f"✓ {message}")
        config = ConfigManager.load()
        click.echo(f"  Dashboard: http://localhost:{config.get('port')}")
    else:
        click.echo(f"✗ {message}", err=True)
        exit(1)


@cli.command()
def stop():
    """Stop the IDS server"""
    
    click.echo("⏹ Stopping IDS server...")
    
    daemon = DaemonManager()
    success, message = daemon.stop()
    
    if success:
        click.echo(f"✓ {message}")
    else:
        click.echo(f"✗ {message}", err=True)
        exit(1)


@cli.command()
def status():
    """Check server status"""
    
    daemon = DaemonManager()
    running, status_msg = daemon.get_status()
    
    config = ConfigManager.load()
    
    click.echo("📊 IDS Server Status")
    click.echo("-" * 50)
    click.echo(f"Status:     {status_msg}")
    click.echo(f"Interface:  {config.get('interface')}")
    click.echo(f"Port:       {config.get('port')}")
    click.echo(f"Model Dir:  {config.get('model_dir')}")
    
    exit(0 if running else 1)


@cli.command()
@click.option('--lines', '-n', default=50, type=int, help='Number of log lines to show')
def logs(lines):
    """View server logs"""
    
    logs_content = ConfigManager.get_logs(lines)
    
    click.echo("📋 IDS Server Logs")
    click.echo("-" * 50)
    click.echo(logs_content)


@cli.command()
def config():
    """Display current configuration"""
    
    cfg = ConfigManager.load()
    
    click.echo("⚙️ Current Configuration")
    click.echo("-" * 50)
    
    for key, value in cfg.items():
        click.echo(f"{key:<15} : {value}")
    
    click.echo()
    click.echo("Config stored in: " + str(ConfigManager.CONFIG_DIR))


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset configuration to defaults?')
def reset():
    """Reset configuration to defaults"""
    
    if ConfigManager.reset():
        click.echo("✓ Configuration reset to defaults")
        click.echo()
        cfg = ConfigManager.load()
        for key, value in cfg.items():
            click.echo(f"  {key:<15} : {value}")
    else:
        click.echo("✗ Failed to reset configuration", err=True)
        exit(1)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all logs?')
def clear_logs():
    """Clear log file"""
    
    if ConfigManager.clear_logs():
        click.echo("✓ Logs cleared")
    else:
        click.echo("✗ Failed to clear logs", err=True)
        exit(1)


@cli.command()
def info():
    """Show IDS information"""
    
    cfg = ConfigManager.load()
    
    click.echo()
    click.echo("╔" + "═" * 48 + "╗")
    click.echo("║" + " " * 48 + "║")
    click.echo("║" + "  Network Intrusion Detection System (IDS)".center(48) + "║")
    click.echo("║" + "  Version 1.0.0 | Phase 4: CLI Tool".center(48) + "║")
    click.echo("║" + " " * 48 + "║")
    click.echo("╚" + "═" * 48 + "╝")
    click.echo()
    click.echo("📖 Available Commands:")
    click.echo("  ids-cli setup          Configure the IDS")
    click.echo("  ids-cli start          Start the server")
    click.echo("  ids-cli stop           Stop the server")
    click.echo("  ids-cli status         Check server status")
    click.echo("  ids-cli logs           View server logs")
    click.echo("  ids-cli config         Show current configuration")
    click.echo("  ids-cli reset          Reset to default configuration")
    click.echo("  ids-cli clear-logs     Clear log file")
    click.echo("  ids-cli info           Show this help")
    click.echo()
    click.echo("🔗 Web Dashboard: http://localhost:" + str(cfg.get('port')))
    click.echo("📁 Config Directory: " + str(ConfigManager.CONFIG_DIR))
    click.echo()


def main():
    """Entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()
