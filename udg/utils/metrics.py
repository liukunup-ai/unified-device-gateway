from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

http_requests_total = Counter('udg_http_requests_total', 'Total HTTP requests', ['method', 'path', 'status'])
http_request_duration_seconds = Histogram('udg_http_request_duration_seconds', 'HTTP request duration', ['method', 'path'])
command_executions_total = Counter('udg_command_executions_total', 'Total command executions', ['device_type', 'command', 'status'])
command_duration_seconds = Histogram('udg_command_duration_seconds', 'Command execution duration', ['device_type', 'command'])
devices_connected = Gauge('udg_devices_connected', 'Number of connected devices', ['device_type'])
commands_active = Gauge('udg_commands_active', 'Number of active commands')
token_rotations_total = Counter('udg_token_rotations_total', 'Total token rotations')

def get_metrics():
    return generate_latest()