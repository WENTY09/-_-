import os
import platform
import psutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def calculate_platform_stats():
    """Calculate system platform statistics for display in dashboard."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Uptime calculation
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        # Format uptime
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'hostname': platform.node(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'uptime': uptime_str,
            'python_version': platform.python_version()
        }
    except Exception as e:
        logger.error(f"Error calculating platform stats: {e}")
        return {
            'os': platform.system(),
            'os_version': 'N/A',
            'hostname': 'N/A',
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'uptime': 'N/A',
            'python_version': platform.python_version()
        }
