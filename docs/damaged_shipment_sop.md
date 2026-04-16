# Damaged Shipment SOP
**Standard Operating Procedure**
*Last Updated: April 2026*

## Purpose
This SOP provides step-by-step procedures for handling damaged shipment claims, including verification, resolution, and carrier accountability.

## When to Use This SOP
Customer reports any of the following:
- Product arrived damaged/broken
- Packaging was damaged upon delivery
- Missing items from order
- Wrong items shipped

## Decision Tree Overview

```
Customer reports damage
    ↓
Verify order & claim
    ↓
Request photo documentation (unless VIP)
    ↓
Assess damage severity
    ↓
Check inventory for replacement
    ↓
Offer resolution (replacement or refund)
    ↓
Issue compensation
    ↓
File carrier claim if needed
    ↓
Monitor damage patterns
```

## Step-by-Step Procedures

### Step 1: Initial Verification (Required - 5 minutes)

**Collect information:**
- Order number
- Delivery date
- Damage description
- Carrier name (UPS/USPS/etc.)

**Verify in system:**
- Order exists and was delivered
- Items claimed as damaged match order contents
- Delivery confirmation shows successful delivery

**Red flags (potential fraud):**
- Customer has multiple damage claims (>2 in 6 months)
- High-value items claimed damaged
- Claim made >7 days after delivery
- **Action if red flags:** Escalate to manager before proceeding

### Step 2: Photo Documentation (Required unless VIP)

**Request from customer:**
- Photo of damaged product
- Photo of product packaging (inner)
- Photo of shipping box exterior
- Photo of shipping label

**Email template:**
"To process your damage claim quickly, please send photos showing: [list above]. This helps us improve packaging and file a carrier claim on your behalf."

**VIP Exception:**
- Customers with 5+ orders and no prior damage claims
- Skip photo requirement
- Note in claim: "VIP - photo waived"
- **Rationale:** Trust established customers to reduce friction

**Timeline:**
- Give customer 48 hours to provide photos
- If no response: Send reminder
- If no response after 72 hours: Close claim (notify customer)

### Step 3: Damage Assessment (2 minutes)

**Category A - Minor Damage:**
- Outer box damaged but product intact
- Cosmetic damage to product packaging only
- Product itself undamaged and functional

**Category B - Moderate Damage:**
- Product container damaged but contents usable
- Partial leakage but >50% product remaining
- Packaging damage affecting product presentation (gifts)

**Category C - Severe Damage:**
- Product completely destroyed/unusable
- Full leakage/spills
- Contamination risk
- Multiple items damaged in same shipment

### Step 4: Inventory Check (Required - 2 minutes)

**Check product database:**
- Is replacement item in stock?
- Current stock level
- Is product discontinued?
- Restock ETA if out of stock

**Decision matrix:**
| Product Status | Action |
|---------------|--------|
| In stock (>10 units) | Offer replacement or refund (customer choice) |
| Low stock (1-10 units) | Offer replacement or refund (customer choice) + flag for restock |
| Out of stock | Refund only OR wait for restock (customer choice, provide ETA) |
| Discontinued | Refund only + 20% store credit compensation |

### Step 5: Resolution Offer (Immediate)

**For Category A (Minor Damage):**
- **Option 1:** Keep product + $10 store credit
- **Option 2:** Full refund (return not required for damaged goods)
- **Timeline:** Store credit issued immediately, refund in 3-5 days
- **No replacement:** Product is still usable

**For Category B (Moderate Damage):**
- **Option 1:** Replacement shipped immediately (expedited, no charge)
- **Option 2:** Full refund (return not required)
- **Bonus:** 10% discount code for next purchase
- **Timeline:** Replacement ships within 24 hours if in stock

**For Category C (Severe Damage):**
- **Option 1:** Replacement shipped immediately (expedited, no charge)
- **Option 2:** Full refund
- **Bonus:** 15% discount code for next purchase
- **Priority:** Flag as urgent - process same day
- **Note:** If multiple items damaged, offer free expedited shipping on next order

**For Multiple Damages (>1 item in order):**
- Automatic upgrade to Category C resolution
- 20% discount code (higher than standard)
- Personal call from manager (if >$100 order value)
- **Investigate:** Check if carrier has pattern issue

### Step 6: Processing the Resolution

**If Replacement Selected:**
1. Create new order in system (tag: REPLACEMENT-DAMAGE)
2. Set shipping to expedited at no charge
3. Link to original order number
4. Add note: "Damage claim - expedited no charge"
5. Process within 1 hour
6. Email customer with tracking within 4 hours
7. Do NOT require customer to return damaged goods (not worth cost)

**If Refund Selected:**
1. Process full refund to original payment method
2. Include original shipping cost in refund
3. Timeline: 3-5 business days
4. Email confirmation immediately
5. Do NOT require return of damaged goods

**Discount Code Issuance:**
1. Generate unique code (format: DAMAGE-[ORDER#]-[%])
2. 30-day expiration
3. No minimum purchase
4. Email to customer with resolution confirmation

### Step 7: Compensation Thresholds

**Standard (most cases):**
- 10% discount code for Categories B and C
- $10 store credit for Category A

**Enhanced (VIP customers or high-value orders):**
- 15% discount code
- Free shipping on next order
- Personal follow-up call

**Maximum (severe cases or repeat issues):**
- 20% discount code
- Free expedited shipping for 3 months
- Manager approval required
- **Use when:** Multiple damages, high customer LTV, retention risk

### Step 8: Carrier Claim Filing (Required for Category B & C)

**File claim with carrier if:**
- Shipment value >$50
- Category B or C damage
- Photos available

**Information needed:**
- Tracking number
- Delivery date
- Photos of damage
- Declared value of shipment
- Cost of goods

**Timeline:**
- File within 24 hours of resolution
- Claims take 2-4 weeks to process
- We handle all carrier communication (not customer's responsibility)

**Reimbursement:**
- If approved: Recovers cost of replacement/refund
- If denied: We absorb cost (don't charge customer)

### Step 9: Damage Pattern Monitoring (Required)

**After every damage claim, log:**
- Carrier name
- Date
- Damage type
- Resolution
- Carrier claim filed (Y/N)

**Monthly review:**
- Count damages per carrier
- Calculate damage rate (damages / total shipments)
- Identify patterns (specific routes, seasons, product types)

**Escalation triggers:**
- 3+ damages from same carrier in one month
- 5+ damages from any carrier in one month
- Damage rate >1% of shipments

**Escalation action:**
- Report to Operations Manager
- Manager contacts carrier representative
- May require packaging improvement
- May require carrier switch (see Shipping Policy)

### Step 10: Follow-Up (24-48 hours after resolution)

**Send follow-up email:**
- Confirm resolution received/processed
- Ask if issue fully resolved
- Invite feedback on handling

**If replacement shipped:**
- Confirm replacement delivered successfully
- If second damage: Escalate to director immediately (rare but serious)

**Customer satisfaction check:**
- Log customer sentiment (satisfied/neutral/dissatisfied)
- If dissatisfied: Manager follow-up call

## Special Cases

### International Orders

**Additional considerations:**
- Customs may have opened/inspected (not carrier damage)
- Customer must file claim with local carrier in some countries
- Return shipping prohibitively expensive - always offer keep + credit or refund

**Process:**
- Same verification steps
- More lenient photo requirements (time zones complicate)
- Default to refund over replacement (shipping cost)
- Enhanced compensation (international shipping expensive)

**Cross-reference:** See Shipping Policy - International section

### Subscription Damage Claims

**Check if recurring order:**
- If yes: Ensure future shipments don't have same issue
- Review packaging for this product
- Consider packaging upgrade if recurring damages

**Resolution:**
- Standard damage process applies
- PLUS: Offer to pause next shipment while issue investigated
- See Subscription Cancellation SOP

### High-Value Items (>$100)

**Additional steps:**
- Manager notification required
- Personal call to customer (not just email)
- Expedited claim processing
- Enhanced compensation automatically (15% minimum)
- Photo documentation mandatory (even for VIP)

### Wrong Item Shipped (Not Damage)

**If customer reports wrong product:**
- Verify: Check picking/packing notes
- If our error:
  - Ship correct item (expedited, no charge)
  - Let customer keep wrong item (if unopened)
  - 15% discount code
- If customer error (ordered wrong item):
  - Standard return/exchange process
  - See Return & Refund Policy

### Missing Items (Not Damage)

**If customer reports missing items:**
1. Verify order contents vs. what was picked
2. Check packing list photo (we photograph all shipments)
3. If our error: Ship missing items (expedited, no charge) + 10% code
4. If items were shipped: Possible theft/lost - file carrier claim
5. Reship missing items immediately (don't wait for claim)

## Fraud Prevention

### Red Flags
- Customer has >2 damage claims in 6 months
- High-value items always reported damaged
- Damage claim >7 days after delivery
- Customer refuses photo documentation
- Photos don't match damage description

### Investigation Steps
1. Review customer order history
2. Check for patterns (always same product, always same claim type)
3. Compare to average damage rate
4. Check if customer in high-fraud risk segment

**If fraud suspected:**
- Do NOT accuse customer
- Process current claim normally
- Flag account for future monitoring
- If pattern continues: Manager approval required for future damage claims
- If egregious: Restrict account to store credit only on returns

## Cost Impact Tracking

**Monthly metrics:**
- Total damage claim cost
- Cost by carrier
- Carrier claim recovery rate
- Average resolution cost
- Damage rate as % of orders

**Target metrics:**
- Damage rate: <0.5% of orders
- Carrier claim recovery: >60%
- Customer satisfaction with resolution: >90%

**Use data for:**
- Carrier negotiation
- Packaging improvement decisions
- Cost-benefit of insurance
- Operational efficiency

## Cross-References
- For refund processing: See Return & Refund Policy
- For shipping timelines and carriers: See Shipping Policy
- For product replacement inventory checks: See Product FAQ
- For escalation beyond manager: See Escalation Criteria (Day 4 expansion)

## Approval Authority

| Resolution Type | Approval Needed |
|----------------|----------------|
| Standard (10% code, replacement) | None - auto-approved |
| Enhanced (15% code, free shipping) | Manager approval |
| Maximum (20% code, extended benefits) | Manager approval |
| High-value orders (>$200) | Manager notification required |
| Suspected fraud | Manager investigation required |
| Pattern issues (>3/month) | Operations Manager escalation |
