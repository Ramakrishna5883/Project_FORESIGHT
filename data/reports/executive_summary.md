# Project FORESIGHT — Executive Performance Readout
**NorthBay Living Inventory Intelligence**

---

## Executive Summary
Of NorthBay's **150 active SKUs**, our model flags **38 at risk of stocking out** in the next 6 weeks, representing **₹17.87 Lakh in sales at risk**. 
Additionally, **4 SKUs** are significantly overstocked, locking up **₹1.71 Lakh in idle capital**.
The remaining **108 SKUs** are classified as healthy.

### Forecast Model Performance
We evaluated our Machine Learning demand model against the Seasonal Naive baseline using rolling-origin backtesting (4 folds):

- **Baseline WAPE**: 19.33%
- **FORESIGHT Model WAPE**: 6.07%
- **Accuracy Improvement**: 68.58%

---

## Action Priority List

### Top 5 SKUs to Replenish (Stockout Risk)
| SKU ID | Category | Subcategory | Lead Time | Sales at Risk | Recommended Qty |
|---|---|---|---|---|---|
| NBL-1145 | Decor | Wall Art | 10 days | ₹2.96 Lakh | 4,511 |
| NBL-1102 | Furnishings | Sofas | 7 days | ₹2.47 Lakh | 4,607 |
| NBL-1068 | Small Appliances | Air Purifiers | 10 days | ₹2.19 Lakh | 821 |
| NBL-1087 | Furnishings | Tables | 7 days | ₹2.09 Lakh | 1,685 |
| NBL-1116 | Small Appliances | Air Purifiers | 10 days | ₹1.35 Lakh | 1,529 |

### Top 5 SKUs to Markdown (Overstock Risk)
| SKU ID | Category | Subcategory | On Hand | Idle Capital | Suggested Action |
|---|---|---|---|---|---|
| NBL-1088 | Decor | Wall Art | 1314 | ₹1.26 Lakh | Clear excess stock |
| NBL-1131 | Small Appliances | Heaters | 947 | ₹26,630.74 | Clear excess stock |
| NBL-1067 | Decor | Vases | 160 | ₹10,619.62 | Clear excess stock |
| NBL-1129 | Furnishings | Chairs | 180 | ₹8,251.24 | Clear excess stock |

---
*Report generated automatically by the Project FORESIGHT validation & decision pipeline.*
