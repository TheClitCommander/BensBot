#!/bin/bash
set -e

# Create admin user if ADMIN_USERNAME is set
if [[ -n "$ADMIN_USERNAME" ]]; then
    echo "Creating admin user..."
    python scripts/create_admin.py
fi

# Execute the main command
exec "$@" 