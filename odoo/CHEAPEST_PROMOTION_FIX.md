# Fix for Multiple Cheapest Product Promotions

## Problem
When 2 or more eligible promotions with type "cheapest product" exist, Odoo was only applying one promotion. This is because Odoo treats cheapest promotions as "global discounts" and picks only the one with the maximum value.

## Solution
Modified the `_calculateRewards()` function in `/addons-pos/pos_coupon_multiples/static/src/js/coupon.js` to:

1. **Remove cheapest promotions from globalDiscounts logic**: Cheapest product promotions are no longer grouped with "on_order" discounts for comparison.

2. **Apply all eligible cheapest promotions**: All cheapest product promotions whose conditions are satisfied are now added to the rewardsContainer, regardless of their discount values.

## Changes Made

### File: `pos_coupon_multiples/static/src/js/coupon.js`

#### 1. Added Reward import
```javascript
const { Reward } = require('pos_coupon.pos');
```

#### 2. Overrode `_calculateRewards()` method
The method now:
- Creates a new rewardsContainer
- Separates cheapest product discounts from global discounts (on_order)
- Collects all cheapest product discounts independently
- Only applies the "max value" logic to on_order discounts
- Adds ALL cheapest product discounts to the final rewards

#### Key Code Changes:
```javascript
// Separate collection: on_order discounts only go to globalDiscounts
globalDiscounts.push(...collectRewards(onOrderPrograms, onOrderDiscountGetter));

// Cheapest discounts are collected separately
const cheapestDiscounts = collectRewards(onCheapestPrograms, (program, coupon_id) => 
    this._getOnCheapestProductDiscount(program, coupon_id, freeProducts)
);

// Add ALL cheapest discounts (not just the max one)
rewardsContainer.add([
    ...freeProducts,
    ...fixedAmountDiscounts,
    ...specificDiscounts,
    ...theOnlyGlobalDiscount,  // Only one on_order discount (max value)
    ...cheapestDiscounts,      // ALL cheapest product discounts
]);
```

## Testing
To test this fix:
1. Create 2 or more promotion programs with reward_type = "discount" and discount_apply_on = "cheapest_product"
2. Add products to an order that satisfy the conditions for multiple cheapest product promotions
3. Verify that ALL eligible cheapest product promotions are applied (not just one)

## Technical Notes
- The `_getOnCheapestProductDiscount()` method remains unchanged - it still handles scale_in_multiples logic correctly
- Only the reward collection and application logic in `_calculateRewards()` was modified
- The fix works for both scale_in_multiples and non-scale_in_multiples promotions

## Additional Fix: Zero-Discount Lines

### Problem
When scanning items for a "buy 2 get 1 free" promotion, discount lines were appearing with 0.0 price before the promotion conditions were met (e.g., after scanning 2 items instead of waiting for the 3rd).

### Solution
Fixed at the source in `_getOnCheapestProductDiscount()` by only adding to `amountsToDiscount` when `quantityMultiple > 0`:

```javascript
// In _getOnCheapestProductDiscount method:
let quantityMultiple = computeFreeQuantity(totalQuantity, program.rule_min_quantity, program.reward_product_quantity);

// Only add to amountsToDiscount if quantityMultiple > 0
if (quantityMultiple > 0) {
    amountsToDiscount[key] = cheapestLine.price * quantityMultiple;
}
```

This prevents the creation of zero-value reward objects at the source, so discount lines only appear when:
- The promotion conditions are fully satisfied (e.g., all 3 items scanned for "buy 2 get 1 free")
- There's an actual non-zero discount to apply
