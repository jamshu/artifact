#!/bin/bash

# Script to run tests for stock_grn_invoice module
# Usage: ./run_tests.sh

echo "=========================================="
echo "Running Tests for Stock GRN Invoice Module"
echo "=========================================="

# Navigate to Odoo root directory (adjust path as needed)
ODOO_PATH="/Users/jamshid/PycharmProjects/Siafa/src"
DB_NAME="aug_17"
PROJECT_ROOT="/Users/jamshid/PycharmProjects/Siafa"

# Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"

cd "$ODOO_PATH"

# Run specific test file
echo "Running test_picking_invoice_wizard tests..."
python3 odoo-bin \
    -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
    -d "$DB_NAME" \
    --test-enable \
    --stop-after-init \
    -i stock_grn_invoice \
    --log-level=test

# Alternative: Run all tests in the module
# python3 odoo-bin -d "$DB_NAME" \
#     --db_port=5433 \
#     --test-enable \
#     --stop-after-init \
#     -u stock_grn_invoice

echo ""
echo "=========================================="
echo "Test execution completed"
echo "=========================================="
