# Odoo Agent - Usage Examples

## Example 1: E-Commerce Product Review Module

### Command
```bash
node index.js create product_reviews \
  --description "Product Review and Rating System" \
  --features "5-star rating system, review comments, verified purchase badge, helpful votes, moderation workflow, email notifications"
```

### What Gets Generated
```
product_reviews/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── product_review.py
├── views/
│   ├── product_review_views.xml
│   └── menu.xml
├── security/
│   └── ir.model.access.csv
└── data/
    └── review_data.xml
```

### Generated Features
- `product.review` model with fields: `product_id`, `customer_id`, `rating`, `comment`, `verified_purchase`, `helpful_count`, `state`
- Tree, form, search, and kanban views
- Workflow states: draft, published, rejected
- Access rights for users and managers
- Menu items under Sales

## Example 2: Inventory Low Stock Alerts

### Interactive Mode Flow
```
$ npm start

What would you like to do?
> Create a new Odoo module

Module name: inventory_alerts
Description: Automated low stock alert system
Features: automatic threshold monitoring, email alerts, SMS notifications, dashboard widget

[AI generates module...]

Files generated:
  CREATE __manifest__.py (Manifest file)
  CREATE models/stock_alert.py (Alert model)
  CREATE models/stock_alert_rule.py (Alert rule configuration)
  CREATE views/stock_alert_views.xml (Views)
  CREATE data/cron_job.xml (Scheduled action)
  CREATE security/ir.model.access.csv (Access rights)

Would you like to review the changes in detail? Yes

[1/6] Reviewing: __manifest__.py
[Shows full file content...]
What would you like to do? ✓ Approve

[Continues for all files...]

Apply 6 changes? Yes

✓ Created: inventory_alerts/__manifest__.py
✓ Created: inventory_alerts/models/stock_alert.py
...

✨ Module created successfully!
```

## Example 3: Customizing Sales Module

### Scenario
Add a custom approval workflow for high-value sales orders.

### Command
```bash
node index.js customize /opt/odoo/addons/sale \
  --request "Add a two-level approval workflow for sales orders above $50,000. First level: Sales Manager, Second level: Finance Manager. Add approval state fields and buttons to the form view."
```

### What Gets Modified/Created
```
sale/
├── models/
│   └── sale_order.py (MODIFIED - adds approval fields)
├── views/
│   └── sale_order_views.xml (MODIFIED - adds approval buttons and states)
└── security/
    └── ir.model.access.csv (MODIFIED - approval permissions)
```

### Generated Changes
- New fields: `requires_approval`, `first_approval_user_id`, `second_approval_user_id`, `approval_state`
- New methods: `action_request_approval()`, `action_first_approve()`, `action_second_approve()`, `action_reject_approval()`
- State selection: `draft`, `pending_first`, `pending_second`, `approved`, `rejected`
- Constraints: order amount threshold check
- View inheritance with approval buttons

## Example 4: Debugging a Common Error

### Scenario
You get an error when trying to create a sale order.

### Error Message
```
ValidationError: The following fields are invalid:
Field 'custom_field' does not exist
Error context:
Model: sale.order
Method: create
```

### Using the Debug Command
```bash
node index.js debug \
  --error "ValidationError: Field 'custom_field' does not exist on sale.order" \
  --context "class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def create(self, vals):
        vals['custom_field'] = 'test'
        return super().create(vals)" \
  --module /opt/odoo/addons/sale_custom
```

### AI Response
```
🔍 Diagnosis:

Error Type: FieldNotDefined
Root Cause: Attempting to set 'custom_field' in create() but field is not declared in model
Severity: high

💡 Solution:

Approach: Add field definition to model before using it
Explanation: Odoo requires all fields to be explicitly declared as class attributes before they can be used...

Fixes:
  MODIFY models/sale_order.py
  + Add custom_field definition

  [Shows full fixed code with field definition]

🧪 Testing Steps:
  1. Restart Odoo server
     Expected: No errors in logs

  2. Update sale_custom module
     Expected: Module updates successfully

  3. Create a sale order
     Expected: Order created with custom_field value

💡 Prevention Tips:
  1. Always declare fields as class attributes using fields.* types
  2. Check field names match exactly (case-sensitive)
  3. Ensure field type matches usage
```

## Example 5: Code Quality Analysis

### Command
```bash
node index.js analyze /opt/odoo/addons/my_module/models/product.py
```

### Output
```
📊 Code Analysis Results:

Summary:
  Quality: 7/10
  Issues: 5 issues found
  Recommendation: Address security concerns and add missing constraints

⚠ Issues Found (5):

1. [HIGH] SQL injection vulnerability
   Line: 45 | Category: security
   Description: Direct SQL query without parameterization
   Suggestion: Use ORM methods (search, browse) instead of cr.execute

2. [MEDIUM] N+1 query problem
   Line: 67 | Category: performance
   Description: Loop executes database query for each iteration
   Suggestion: Use read_group() or load related records in batch

3. [MEDIUM] Missing field constraint
   Line: 23 | Category: validation
   Description: Price field has no validation
   Suggestion: Add @api.constrains decorator to validate price > 0

4. [LOW] Missing docstring
   Line: 12 | Category: documentation
   Description: compute_total() method has no documentation
   Suggestion: Add docstring explaining calculation logic

5. [LOW] Inefficient search
   Line: 89 | Category: performance
   Description: Using search() + filtered() instead of domain
   Suggestion: Move filter logic into search domain

🔒 Security Concerns (1):

1. [High] User input not sanitized
   Mitigation: Use Odoo ORM search() with proper domains instead of raw SQL
```

## Example 6: Creating a REST API Module

### Interactive Mode
```
$ npm start

> Create a new Odoo module

Module name: api_integration
Description: RESTful API for external integrations
Features: JWT authentication, product CRUD endpoints, order webhooks, rate limiting, API key management, Swagger documentation
```

### Generated Module Includes
- `api.key` model for API key management
- `api.request.log` for audit trail
- `/api/v1/products` endpoints
- `/api/v1/orders` endpoints
- JWT token generation and validation
- Rate limiting decorator
- OpenAPI/Swagger documentation
- Security rules for API access

## Example 7: Multi-Company Support

### Customization Request
```bash
node index.js customize /opt/odoo/addons/inventory_custom \
  --request "Add multi-company support to inventory_custom module. Ensure all records are company-specific and users only see their company's data."
```

### Generated Changes
- Adds `company_id` field to all custom models
- Updates search views with company filter
- Adds record rules for company data separation
- Updates security rules
- Modifies default values to use current company
- Adds company switching capability

## Example 8: Batch Module Creation Script

### Shell Script
```bash
#!/bin/bash

# Create multiple related modules

node index.js create hr_attendance_extended \
  --description "Extended HR Attendance" \
  --features "geolocation tracking, photo capture, overtime calculation" \
  --yes

node index.js create hr_payroll_custom \
  --description "Custom Payroll Rules" \
  --features "custom salary structures, bonus calculations, tax rules" \
  --yes

node index.js create hr_reports \
  --description "HR Reporting Dashboard" \
  --features "attendance reports, payroll analytics, charts" \
  --yes

echo "All modules created!"
```

## Tips for Best Results

### 1. Be Specific with Features
❌ Bad: "customer management"
✅ Good: "customer registration form, address validation, credit limit tracking, contact history"

### 2. Provide Context for Debugging
Include:
- Full error message
- Relevant code snippet
- Module path
- What you were trying to do

### 3. Test Incrementally
- Create basic module first
- Test in Odoo
- Then customize with additional features

### 4. Review Changes Carefully
- Always review diffs before approving
- Check field names and types
- Verify security rules
- Test computed fields logic

### 5. Use Appropriate LLM
- **Gemini**: Fast, good for standard modules
- **GPT-4**: Better for complex logic
- **Claude**: Excellent for understanding context and nuanced requirements

## Common Patterns

### Pattern 1: Master-Detail Module
```bash
node index.js create project_task_extended \
  --description "Project task management with subtasks" \
  --features "parent-child task relationships, task dependencies, Gantt chart view, progress calculation, resource allocation"
```

### Pattern 2: Approval Workflow
```bash
node index.js customize /opt/odoo/addons/purchase \
  --request "Add 3-level approval workflow based on purchase amount: <$1000 auto-approve, <$10000 manager approval, >$10000 requires CFO approval"
```

### Pattern 3: Integration Module
```bash
node index.js create shopify_connector \
  --description "Shopify integration" \
  --features "product sync, order import, inventory sync, webhook listeners, error handling, sync logs"
```

### Pattern 4: Reporting Dashboard
```bash
node index.js create sales_dashboard \
  --description "Sales analytics dashboard" \
  --features "sales by region charts, top products, sales trends, KPI widgets, exportable reports, date range filters"
```

## Troubleshooting Common Issues

### Issue: Generated Code Has Syntax Errors
**Solution**: Check LLM temperature (should be low: 0.1-0.3), try again, or manually fix and report.

### Issue: Module Dependencies Missing
**Solution**: Edit `__manifest__.py` and add required dependencies in `depends` list.

### Issue: Access Rights Not Working
**Solution**: Restart Odoo and update the module. Check `ir.model.access.csv` has correct format.

### Issue: Views Not Appearing
**Solution**: Ensure views XML is listed in `__manifest__.py` under `data` section.

---

For more examples and patterns, explore the [Odoo documentation](https://www.odoo.com/documentation/16.0/).
