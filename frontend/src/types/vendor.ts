export const vendorStatusValues = [
  "uncontacted",
  "interviewed",
  "not_interviewed",
  "proposing",
  "poc",
  "contracted",
  "on_hold",
  "lost",
  "unknown",
] as const;

export type VendorStatus = typeof vendorStatusValues[number];
