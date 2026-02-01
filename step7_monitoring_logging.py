"""
STEP 7: MONITORING & LOGGING SETUP
====================================
Set up comprehensive monitoring for your recommendation system
"""

import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from functools import wraps
import time
from prometheus_flask_exporter import PrometheusMetrics
from flask import Flask, request

# ============================================
# LOGGING CONFIGURATION
# ============================================

def setup_logging(app, log_level=logging.INFO):
    """
    Configure structured logging for the application
    """
    
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/recommendation_api.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Also configure root logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(log_level)
    
    app.logger.info("Logging configured successfully")


class StructuredLogger:
    """
    Structured logging for better analysis
    """
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_request(self, user_id, endpoint, duration_ms, status_code, items_returned=None):
        """Log API request details"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'request',
            'user_id': user_id,
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'items_returned': items_returned
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error_type, message, user_id=None, additional_data=None):
        """Log errors with context"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'error_type': error_type,
            'message': message,
            'user_id': user_id,
            'additional_data': additional_data
        }
        self.logger.error(json.dumps(log_data))
    
    def log_recommendation(self, user_id, item_ids, algorithm_used, computation_time_ms):
        """Log recommendation generation"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'recommendation',
            'user_id': user_id,
            'item_count': len(item_ids),
            'algorithm': algorithm_used,
            'computation_time_ms': computation_time_ms
        }
        self.logger.info(json.dumps(log_data))


# ============================================
# PROMETHEUS METRICS
# ============================================

def setup_prometheus_metrics(app):
    """
    Setup Prometheus metrics for monitoring
    """
    metrics = PrometheusMetrics(app)
    
    # Custom metrics
    from prometheus_client import Counter, Histogram, Gauge
    
    # Request counter
    request_counter = Counter(
        'recommendation_requests_total',
        'Total recommendation requests',
        ['endpoint', 'status']
    )
    
    # Response time histogram
    response_time = Histogram(
        'recommendation_response_time_seconds',
        'Response time in seconds',
        ['endpoint']
    )
    
    # Active users gauge
    active_users = Gauge(
        'recommendation_active_users',
        'Number of active users'
    )
    
    # Cache hit rate
    cache_hits = Counter(
        'recommendation_cache_hits_total',
        'Total cache hits'
    )
    
    cache_misses = Counter(
        'recommendation_cache_misses_total',
        'Total cache misses'
    )
    
    return {
        'request_counter': request_counter,
        'response_time': response_time,
        'active_users': active_users,
        'cache_hits': cache_hits,
        'cache_misses': cache_misses
    }


# ============================================
# REQUEST MONITORING DECORATOR
# ============================================

def monitor_request(logger):
    """
    Decorator to monitor API requests
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the function
                result = f(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract user_id from kwargs or args
                user_id = kwargs.get('user_id') or (args[0] if args else None)
                
                # Log the request
                logger.log_request(
                    user_id=user_id,
                    endpoint=request.path,
                    duration_ms=duration_ms,
                    status_code=200
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_error(
                    error_type=type(e).__name__,
                    message=str(e),
                    user_id=kwargs.get('user_id'),
                    additional_data={'endpoint': request.path}
                )
                raise
        
        return decorated_function
    return decorator


# ============================================
# HEALTH CHECK MONITORING
# ============================================

class HealthMonitor:
    """
    Monitor system health
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.last_check = datetime.now()
    
    def record_request(self, success=True):
        """Record a request"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.last_check = datetime.now()
    
    def get_health_status(self):
        """Get current health status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'status': 'healthy' if error_rate < 1 else 'degraded',
            'uptime_seconds': uptime,
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate_percent': error_rate,
            'last_request': self.last_check.isoformat()
        }


# ============================================
# ALERTING SYSTEM
# ============================================

class AlertManager:
    """
    Simple alerting for critical issues
    """
    
    def __init__(self, webhook_url=None, email_config=None):
        self.webhook_url = webhook_url
        self.email_config = email_config
        self.alert_history = []
    
    def send_alert(self, severity, message, details=None):
        """
        Send alert notification
        
        severity: 'critical', 'warning', 'info'
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'message': message,
            'details': details
        }
        
        self.alert_history.append(alert)
        
        # Log the alert
        logger = logging.getLogger('AlertManager')
        logger.error(json.dumps(alert))
        
        # Send to webhook if configured
        if self.webhook_url and severity == 'critical':
            self._send_webhook(alert)
        
        # Send email if configured
        if self.email_config and severity in ['critical', 'warning']:
            self._send_email(alert)
    
    def _send_webhook(self, alert):
        """Send alert to webhook (e.g., Slack)"""
        try:
            import requests
            requests.post(
                self.webhook_url,
                json={
                    'text': f"🚨 {alert['severity'].upper()}: {alert['message']}",
                    'details': alert['details']
                },
                timeout=5
            )
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")
    
    def _send_email(self, alert):
        """Send email alert"""
        # Implement email sending logic
        pass
    
    def check_metrics_and_alert(self, metrics):
        """
        Check metrics and send alerts if thresholds are exceeded
        """
        # Example: Alert if error rate is high
        if metrics.get('error_rate_percent', 0) > 5:
            self.send_alert(
                'critical',
                'High error rate detected',
                {'error_rate': metrics['error_rate_percent']}
            )
        
        # Example: Alert if response time is high
        if metrics.get('avg_response_time_ms', 0) > 500:
            self.send_alert(
                'warning',
                'High response time detected',
                {'avg_response_time_ms': metrics['avg_response_time_ms']}
            )


# ============================================
# MONITORING DASHBOARD DATA
# ============================================

class MonitoringDashboard:
    """
    Collect data for monitoring dashboard
    """
    
    def __init__(self):
        self.metrics = {
            'requests_per_minute': [],
            'response_times': [],
            'error_counts': [],
            'cache_hit_rates': []
        }
        self.window_size = 60  # Keep last 60 data points
    
    def record_request(self, response_time_ms, is_error=False, cache_hit=False):
        """Record request metrics"""
        timestamp = datetime.now()
        
        # Record response time
        self.metrics['response_times'].append({
            'timestamp': timestamp,
            'value': response_time_ms
        })
        
        # Record error
        if is_error:
            self.metrics['error_counts'].append({
                'timestamp': timestamp,
                'value': 1
            })
        
        # Record cache hit
        self.metrics['cache_hit_rates'].append({
            'timestamp': timestamp,
            'value': 1 if cache_hit else 0
        })
        
        # Trim old data
        self._trim_old_data()
    
    def _trim_old_data(self):
        """Keep only recent data"""
        for metric_name, data in self.metrics.items():
            if len(data) > self.window_size:
                self.metrics[metric_name] = data[-self.window_size:]
    
    def get_dashboard_data(self):
        """Get data for dashboard display"""
        now = datetime.now()
        
        # Calculate metrics
        recent_response_times = [m['value'] for m in self.metrics['response_times'][-60:]]
        avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0
        
        recent_cache_hits = [m['value'] for m in self.metrics['cache_hit_rates'][-60:]]
        cache_hit_rate = (sum(recent_cache_hits) / len(recent_cache_hits) * 100) if recent_cache_hits else 0
        
        return {
            'timestamp': now.isoformat(),
            'avg_response_time_ms': avg_response_time,
            'cache_hit_rate_percent': cache_hit_rate,
            'total_requests_last_minute': len(self.metrics['response_times'][-60:]),
            'error_count_last_minute': len(self.metrics['error_counts'][-60:])
        }


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    Example: How to integrate monitoring into Flask app
    """
    
    app = Flask(__name__)
    
    # Setup logging
    setup_logging(app)
    
    # Setup Prometheus metrics
    metrics = setup_prometheus_metrics(app)
    
    # Create monitoring instances
    logger = StructuredLogger('recommendation_api')
    health_monitor = HealthMonitor()
    alert_manager = AlertManager(
        webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    )
    dashboard = MonitoringDashboard()
    
    # Example endpoint with monitoring
    @app.route('/api/v1/recommendations/user/<int:user_id>')
    @monitor_request(logger)
    def get_recommendations(user_id):
        start_time = time.time()
        
        try:
            # Your recommendation logic here
            recommendations = []  # Get recommendations
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            dashboard.record_request(duration_ms, is_error=False, cache_hit=False)
            health_monitor.record_request(success=True)
            
            return {'recommendations': recommendations}
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            dashboard.record_request(duration_ms, is_error=True, cache_hit=False)
            health_monitor.record_request(success=False)
            alert_manager.send_alert('critical', f'Recommendation failed: {str(e)}')
            raise
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        status = health_monitor.get_health_status()
        return status
    
    # Metrics endpoint for Prometheus
    @app.route('/metrics')
    def metrics_endpoint():
        # Prometheus metrics are automatically exposed
        pass
    
    # Dashboard data endpoint
    @app.route('/dashboard/metrics')
    def dashboard_metrics():
        return dashboard.get_dashboard_data()
    
    print("Monitoring configured. Endpoints:")
    print("  /health - Health check")
    print("  /metrics - Prometheus metrics")
    print("  /dashboard/metrics - Dashboard data")
