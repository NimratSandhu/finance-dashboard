// assets/dashAgGridFunctions.js
var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

// Currency formatter (USD)
dagfuncs.USD = function (val) {
  if (val === null || val === undefined || isNaN(val)) return val;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(val);
};

// Percent formatter (expects fraction, e.g., 0.153 -> 15.3%)
dagfuncs.PCT = function (val) {
  if (val === null || val === undefined || isNaN(val)) return val;
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(val);
};
