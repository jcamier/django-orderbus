#!/bin/sh
# Generate Prometheus configuration with optional Grafana Cloud remote_write

PROMETHEUS_CONFIG_FILE="/etc/prometheus/prometheus.yml"

# Start with the base config (already mounted)
# If template exists, use it as base
if [ -f "/etc/prometheus/prometheus.yml.template" ]; then
    cp "/etc/prometheus/prometheus.yml.template" "$PROMETHEUS_CONFIG_FILE"
fi

# Check if Grafana Cloud credentials are provided
if [ -n "$GRAFANA_CLOUD_PROMETHEUS_URL" ] && [ -n "$GRAFANA_CLOUD_PROMETHEUS_USERNAME" ] && [ -n "$GRAFANA_CLOUD_PROMETHEUS_PASSWORD" ]; then
    echo "Configuring Prometheus remote_write to Grafana Cloud..."

    # Check if remote_write already exists
    if ! grep -q "^remote_write:" "$PROMETHEUS_CONFIG_FILE"; then
        # Create remote_write config block
        cat > /tmp/remote_write.yml <<EOF
remote_write:
  - url: ${GRAFANA_CLOUD_PROMETHEUS_URL}
    basic_auth:
      username: ${GRAFANA_CLOUD_PROMETHEUS_USERNAME}
      password: ${GRAFANA_CLOUD_PROMETHEUS_PASSWORD}
    queue_config:
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      max_retries: 3

EOF
        # Insert before scrape_configs
        head -n -1 "$PROMETHEUS_CONFIG_FILE" > /tmp/prometheus.yml.new
        cat /tmp/remote_write.yml >> /tmp/prometheus.yml.new
        echo "scrape_configs:" >> /tmp/prometheus.yml.new
        sed -n '/^scrape_configs:/,$p' "$PROMETHEUS_CONFIG_FILE" | tail -n +2 >> /tmp/prometheus.yml.new
        mv /tmp/prometheus.yml.new "$PROMETHEUS_CONFIG_FILE"
        rm -f /tmp/remote_write.yml
    else
        echo "remote_write already configured, skipping"
    fi
else
    echo "Grafana Cloud credentials not provided, skipping remote_write configuration"
fi

# Execute the original Prometheus command
exec "$@"

