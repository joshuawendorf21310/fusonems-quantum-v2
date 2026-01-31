import React, { useState } from 'react'
import { Calculator, DollarSign, CreditCard, Building2, TrendingDown, CheckCircle, Info } from 'lucide-react'

interface TierOption {
  tier: number
  tier_label: string
  balance_amount: number
  min_payment: number
  payment_schedules: Array<{
    months: number
    monthly_payment: number
    total_with_ach: number
    card_fee_per_payment: number
    total_card_fees: number
    total_with_card: number
    savings_with_ach: number
    recommended: boolean
  }>
  ach_message: string
  card_fee_notice: string
}

const PaymentPlanCalculator: React.FC = () => {
  const [balanceAmount, setBalanceAmount] = useState<string>('500')
  const [tierOptions, setTierOptions] = useState<TierOption | null>(null)
  const [selectedSchedule, setSelectedSchedule] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const calculateTiers = async () => {
    if (!balanceAmount || parseFloat(balanceAmount) <= 0) {
      alert('Please enter a valid balance amount')
      return
    }

    try {
      setLoading(true)
      const response = await fetch(
        `/api/billing/payment-plans/tier-options?balance_amount=${balanceAmount}`
      )
      if (response.ok) {
        const data = await response.json()
        setTierOptions(data)
        setSelectedSchedule(0) // Select first option by default
      }
    } catch (error) {
      console.error('Failed to calculate tiers:', error)
      alert('Failed to calculate payment plan options')
    } finally {
      setLoading(false)
    }
  }

  const getTierColor = (tier: number) => {
    switch (tier) {
      case 1: return 'border-blue-500 bg-blue-50 text-blue-700'
      case 2: return 'border-green-500 bg-green-50 text-green-700'
      case 3: return 'border-purple-500 bg-purple-50 text-purple-700'
      default: return 'border-gray-300 bg-gray-50 text-gray-700'
    }
  }

  const getTierRange = (tier: number) => {
    switch (tier) {
      case 1: return '$1-$249'
      case 2: return '$250-$999'
      case 3: return '$1,000+'
      default: return ''
    }
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center gap-2">
          <Calculator size={20} className="text-purple-600" />
          <h2 className="text-lg font-semibold">Payment Plan Calculator</h2>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Calculate payment plan options with ACH savings • 3 tiers based on balance
        </p>
      </div>

      <div className="p-6">
        {/* Input Section */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Patient Balance Amount</label>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="number"
                value={balanceAmount}
                onChange={(e) => setBalanceAmount(e.target.value)}
                placeholder="Enter balance amount"
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                min="1"
                step="0.01"
              />
            </div>
            <button
              onClick={calculateTiers}
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
            >
              Calculate
            </button>
          </div>
        </div>

        {/* Tier Badge */}
        {tierOptions && (
          <div className="space-y-6">
            <div className={`border-2 rounded-lg p-4 ${getTierColor(tierOptions.tier)}`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-sm font-medium">You're in:</div>
                  <div className="text-2xl font-bold">{tierOptions.tier_label}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm">Tier {tierOptions.tier}</div>
                  <div className="text-xs">{getTierRange(tierOptions.tier)}</div>
                </div>
              </div>
              <div className="text-sm">{tierOptions.description || tierOptions.tier_label}</div>
            </div>

            {/* ACH Savings Banner */}
            <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <TrendingDown size={24} className="text-green-600 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-semibold text-green-800 mb-1">
                    {tierOptions.ach_message}
                  </div>
                  <div className="text-sm text-green-700">{tierOptions.card_fee_notice}</div>
                  <div className="text-sm text-green-700 mt-2">
                    💡 ACH payments save you from 3% credit card processing fees
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Schedule Options */}
            <div>
              <h3 className="font-semibold mb-3">Available Payment Plans:</h3>
              <div className="space-y-3">
                {tierOptions.payment_schedules.map((schedule, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedSchedule(index)}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedSchedule === index
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-lg font-bold">
                          ${schedule.monthly_payment.toFixed(2)}/month
                        </div>
                        <div className="text-sm text-gray-600">
                          {schedule.months} monthly payments
                        </div>
                      </div>
                      {selectedSchedule === index && (
                        <CheckCircle size={24} className="text-purple-600" />
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="bg-white p-3 rounded">
                        <div className="flex items-center gap-2 mb-1">
                          <Building2 size={14} className="text-green-600" />
                          <span className="font-medium text-green-700">ACH (Recommended)</span>
                        </div>
                        <div className="text-xl font-bold text-green-700">
                          ${schedule.total_with_ach.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-600">Total cost</div>
                      </div>

                      <div className="bg-white p-3 rounded">
                        <div className="flex items-center gap-2 mb-1">
                          <CreditCard size={14} className="text-gray-600" />
                          <span className="font-medium">Credit Card</span>
                        </div>
                        <div className="text-xl font-bold">
                          ${schedule.total_with_card.toFixed(2)}
                        </div>
                        <div className="text-xs text-red-600">
                          +${schedule.total_card_fees.toFixed(2)} in fees
                        </div>
                      </div>
                    </div>

                    {schedule.savings_with_ach > 0 && (
                      <div className="mt-3 bg-green-100 border border-green-300 rounded p-2 text-center">
                        <span className="text-sm font-semibold text-green-800">
                          💰 Save ${schedule.savings_with_ach.toFixed(2)} with ACH
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Terms Info */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 text-sm">
              <div className="flex items-start gap-2">
                <Info size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-blue-900 mb-1">Payment Plan Terms</div>
                  <ul className="text-blue-800 space-y-1 ml-4 list-disc">
                    <li>Minimum payment: ${tierOptions.min_payment.toFixed(2)}/month</li>
                    <li>ACH payments: No processing fees (Recommended)</li>
                    <li>Credit card payments: 3% processing fee per payment</li>
                    <li>Auto-pay available for both ACH and card</li>
                    <li>Plans starting as low as $10/week</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center justify-center gap-2">
                <Building2 size={18} />
                Set Up ACH Plan (Recommended)
              </button>
              <button className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium flex items-center justify-center gap-2">
                <CreditCard size={18} />
                Set Up Card Plan
              </button>
            </div>
          </div>
        )}

        {/* Quick Examples */}
        {!tierOptions && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-3">Quick Examples:</h3>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <button
                onClick={() => { setBalanceAmount('150'); setTimeout(calculateTiers, 100) }}
                className="p-3 bg-white border rounded hover:border-blue-500 text-left"
              >
                <div className="font-medium">$150</div>
                <div className="text-xs text-gray-600">Tier 1: Quick Pay</div>
              </button>
              <button
                onClick={() => { setBalanceAmount('500'); setTimeout(calculateTiers, 100) }}
                className="p-3 bg-white border rounded hover:border-green-500 text-left"
              >
                <div className="font-medium">$500</div>
                <div className="text-xs text-gray-600">Tier 2: Standard</div>
              </button>
              <button
                onClick={() => { setBalanceAmount('1500'); setTimeout(calculateTiers, 100) }}
                className="p-3 bg-white border rounded hover:border-purple-500 text-left"
              >
                <div className="font-medium">$1,500</div>
                <div className="text-xs text-gray-600">Tier 3: Custom</div>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PaymentPlanCalculator
