import type { NextApiRequest, NextApiResponse } from "next"

// Dummy AI categorization endpoint for demo
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" })
  }
  const { transactions } = req.body
  if (!Array.isArray(transactions)) {
    return res.status(400).json({ error: "Missing transactions array" })
  }
  // Simulate AI categorization
  const categorized = transactions.map((txn: any) => ({
    ...txn,
    category: guessCategory(txn)
  }))
  res.status(200).json({ categorized })
}

function guessCategory(txn: any) {
  const desc = (txn.description || "").toLowerCase()
  if (desc.includes("amex")) return "Credit Card Payment"
  if (desc.includes("novo")) return "Business Deposit"
  if (desc.includes("payroll")) return "Payroll"
  if (desc.includes("fuel")) return "Fuel"
  if (desc.includes("office")) return "Office Expense"
  if (desc.includes("insurance")) return "Insurance"
  if (desc.includes("tax")) return "Tax Payment"
  if (desc.includes("deposit")) return "Deposit"
  if (desc.includes("payment")) return "Payment"
  return "Uncategorized"
}
