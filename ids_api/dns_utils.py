"""DNS utility functions for reverse IP lookups with caching."""

import socket
import threading
from functools import lru_cache

# Thread-safe lock for DNS caching
_dns_lock = threading.Lock()


@lru_cache(maxsize=512)
def get_hostname(ip_address):
    """
    Resolve IP address to hostname using reverse DNS lookup.
    
    Results are cached for performance. If lookup fails, returns the IP address.
    
    Args:
        ip_address (str): IP address to resolve
        
    Returns:
        str: Hostname if available, otherwise the IP address
    """
    if not ip_address:
        return ip_address
    
    try:
        # Set a short timeout to avoid blocking
        socket.setdefaulttimeout(2)
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        socket.setdefaulttimeout(None)
        
        # Return just the hostname part (not FQDN if possible)
        return hostname.split('.')[0] if hostname else ip_address
    except (socket.herror, socket.timeout, socket.gaierror, OSError):
        # DNS lookup failed, return the IP address
        return ip_address
    except Exception:
        return ip_address


def clear_dns_cache():
    """Clear the DNS lookup cache."""
    with _dns_lock:
        get_hostname.cache_clear()


def get_dns_cache_info():
    """Get DNS cache statistics."""
    return get_hostname.cache_info()
