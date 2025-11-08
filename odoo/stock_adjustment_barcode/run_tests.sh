#!/bin/bash
# Script to run stock_adjustment_barcode module tests

echo "=========================================="
echo "Running Stock Adjustment Barcode Tests"
echo "=========================================="

# Activate virtual environment
source /Users/jamshid/PycharmProjects/Siafa/.venv/bin/activate

# Set test database name
TEST_DB="sep_24"

echo "Using test database: $TEST_DB"

# Run all tests for the module
echo ""
echo "Running all tests for stock_adjustment_barcode module..."
python3 /Users/jamshid/PycharmProjects/Siafa/src/odoo-bin \
    -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
    -d "$TEST_DB" \
    --test-enable \
    --stop-after-init \
    -u stock_adjustment_barcode \
    --log-level=test

# Run specific test files if needed
if [ "$1" == "basic" ]; then
    echo ""
    echo "Running basic adjustment tests..."
    python3 /Users/jamshid/PycharmProjects/Siafa/src/odoo-bin \
        -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
        -d "$TEST_DB" \
        --test-enable \
        --stop-after-init \
        --test-tags stock_adjustment_barcode.TestStockAdjustmentBarcode
        
elif [ "$1" == "line" ]; then
    echo ""
    echo "Running line tests..."
    python3 /Users/jamshid/PycharmProjects/Siafa/src/odoo-bin \
        -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
        -d "$TEST_DB" \
        --test-enable \
        --stop-after-init \
        --test-tags stock_adjustment_barcode.TestStockAdjustmentBarcodeLine
        
elif [ "$1" == "info" ]; then
    echo ""
    echo "Running line info tests..."
    python3 /Users/jamshid/PycharmProjects/Siafa/src/odoo-bin \
        -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
        -d "$TEST_DB" \
        --test-enable \
        --stop-after-init \
        --test-tags stock_adjustment_barcode.TestStockAdjustmentBarcodeLineInfo
        
elif [ "$1" == "bom" ]; then
    echo ""
    echo "Running BOM consolidation tests..."
    python3 /Users/jamshid/PycharmProjects/Siafa/src/odoo-bin \
        -c /Users/jamshid/PycharmProjects/Siafa/src/odoo.conf \
        -d "$TEST_DB" \
        --test-enable \
        --stop-after-init \
        --test-tags stock_adjustment_barcode.TestBOMConsolidation
fi

echo ""
echo "=========================================="
echo "Test execution completed"
echo "=========================================="

# Usage examples
if [ -z "$1" ]; then
    echo ""
    echo "Usage examples:"
    echo "  ./run_tests.sh         # Run all tests"
    echo "  ./run_tests.sh basic   # Run basic adjustment tests only"
    echo "  ./run_tests.sh line    # Run line tests only"
    echo "  ./run_tests.sh info    # Run line info tests only"
    echo "  ./run_tests.sh bom     # Run BOM consolidation tests only"
fi