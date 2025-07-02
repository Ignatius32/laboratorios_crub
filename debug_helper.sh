#!/bin/bash

# Keycloak Authentication Debug Helper Script
# Run this script to perform various debugging tasks

echo "================================"
echo "KEYCLOAK DEBUG HELPER SCRIPT"
echo "================================"
echo

# Check if we're in the right directory
if [ ! -f "debug_keycloak_production.py" ]; then
    echo "❌ Error: This script must be run from the laboratorios-crub directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "Select debug action:"
echo "1. Run production Keycloak debug"
echo "2. Check application logs"
echo "3. Test Keycloak callback (debug script)"
echo "4. Check Apache error log"
echo "5. Tail security logs (real-time)"
echo "6. Check environment variables"
echo "7. Test network connectivity"
echo "8. All tests"
echo

read -p "Enter choice (1-8): " choice

case $choice in
    1)
        echo "Running production Keycloak debug..."
        python3 debug_keycloak_production.py
        ;;
    2)
        echo "Checking application logs..."
        echo "=== App Log (last 50 lines) ==="
        tail -n 50 logs/app_structured.log 2>/dev/null || echo "App log not found"
        echo
        echo "=== Security Log (last 50 lines) ==="
        tail -n 50 logs/security_structured.log 2>/dev/null || echo "Security log not found"
        ;;
    3)
        echo "Running Keycloak callback debug..."
        python3 debug_keycloak_callback.py
        ;;
    4)
        echo "Checking Apache error log..."
        echo "=== Apache Error Log (last 50 lines) ==="
        sudo tail -n 50 /var/log/apache2/error.log 2>/dev/null || echo "Apache error log not accessible"
        ;;
    5)
        echo "Tailing security logs (real-time). Press Ctrl+C to stop..."
        tail -f logs/security_structured.log 2>/dev/null || echo "Security log not found"
        ;;
    6)
        echo "Checking environment variables..."
        echo "=== Keycloak Configuration ==="
        echo "KEYCLOAK_SERVER_URL: ${KEYCLOAK_SERVER_URL:-'Not set'}"
        echo "KEYCLOAK_REALM: ${KEYCLOAK_REALM:-'Not set'}"
        echo "KEYCLOAK_CLIENT_ID: ${KEYCLOAK_CLIENT_ID:-'Not set'}"
        echo "KEYCLOAK_CLIENT_SECRET: ${KEYCLOAK_CLIENT_SECRET:0:5}***"
        echo "KEYCLOAK_REDIRECT_URI: ${KEYCLOAK_REDIRECT_URI:-'Not set'}"
        echo "KEYCLOAK_DEBUG: ${KEYCLOAK_DEBUG:-'Not set'}"
        echo "BROWSER_DEBUG: ${BROWSER_DEBUG:-'Not set'}"
        ;;
    7)
        echo "Testing network connectivity..."
        echo "=== Ping Keycloak server ==="
        ping -c 3 huayca.crub.uncoma.edu.ar
        echo
        echo "=== Test HTTPS connection ==="
        curl -I https://huayca.crub.uncoma.edu.ar/auth/ --max-time 10
        ;;
    8)
        echo "Running all tests..."
        echo
        echo "1. Production Keycloak debug:"
        python3 debug_keycloak_production.py
        echo
        echo "2. Callback debug:"
        python3 debug_keycloak_callback.py
        echo
        echo "3. Application logs:"
        tail -n 20 logs/app_structured.log 2>/dev/null || echo "App log not found"
        echo
        echo "4. Security logs:"
        tail -n 20 logs/security_structured.log 2>/dev/null || echo "Security log not found"
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        ;;
esac

echo
echo "================================"
echo "Debug completed. Check results above."
echo "================================"
