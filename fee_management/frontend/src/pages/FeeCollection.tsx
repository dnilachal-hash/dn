import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Search, User, Plus, Trash2, Printer, CheckCircle, Loader2, IndianRupee, AlertCircle
} from 'lucide-react'
import client from '../api/client'
import { format } from 'date-fns'

const fmt = (n: number) => '₹' + (n || 0).toLocaleString('en-IN')

const PAYMENT_MODES = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'DEMAND_DRAFT', label: 'Demand Draft' },
  { value: 'NEFT', label: 'NEFT/RTGS' },
  { value: 'UPI', label: 'UPI' },
  { value: 'CARD', label: 'Card' },
  { value: 'ONLINE', label: 'Online' },
]

interface FeeRow {
  fee_head_id: string
  amount: string
}

export default function FeeCollection() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const prefilledStudentId = searchParams.get('student_id')

  const [studentSearch, setStudentSearch] = useState('')
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<any>(null)
  const [loadingStudent, setLoadingStudent] = useState(false)
  const [paymentMode, setPaymentMode] = useState('CASH')
  const [feeRows, setFeeRows] = useState<FeeRow[]>([{ fee_head_id: '', amount: '' }])
  const [receiptDate, setReceiptDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [remarks, setRemarks] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [receipt, setReceipt] = useState<any>(null)
  const searchRef = useRef<HTMLDivElement>(null)

  // Cheque / DD fields
  const [chequeNumber, setChequeNumber] = useState('')
  const [chequeDate, setChequeDate] = useState('')
  const [bankName, setBankName] = useState('')
  const [branchName, setBranchName] = useState('')
  // UPI / Online fields
  const [upiRef, setUpiRef] = useState('')
  const [transactionId, setTransactionId] = useState('')

  const { data: feeSummary } = useQuery({
    queryKey: ['student-fee-summary', selectedStudent?.id],
    queryFn: () => client.get(`/students/${selectedStudent.id}/fee-summary`).then((r) => r.data),
    enabled: !!selectedStudent,
  })

  const { data: feeHeads } = useQuery({
    queryKey: ['fee-heads'],
    queryFn: () => client.get('/fee-heads/').then((r) => r.data),
  })

  // Load pre-filled student
  useEffect(() => {
    if (prefilledStudentId && !selectedStudent) {
      setLoadingStudent(true)
      client.get(`/students/${prefilledStudentId}`)
        .then((r) => setSelectedStudent(r.data))
        .catch(() => toast.error('Student not found'))
        .finally(() => setLoadingStudent(false))
    }
  }, [prefilledStudentId])

  // Search suggestions
  const handleSearchChange = useCallback(async (val: string) => {
    setStudentSearch(val)
    if (val.length < 2) { setSuggestions([]); return }
    try {
      const res = await client.get('/students/', { params: { search: val, limit: 8 } })
      setSuggestions(res.data?.items || res.data || [])
      setShowSuggestions(true)
    } catch {
      setSuggestions([])
    }
  }, [])

  const selectStudent = (s: any) => {
    setSelectedStudent(s)
    setStudentSearch('')
    setSuggestions([])
    setShowSuggestions(false)
    setReceipt(null)
    setFeeRows([{ fee_head_id: '', amount: '' }])
  }

  // Close suggestions on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const feeItems = feeSummary?.items || feeSummary || []
  const outstandingHeads = feeItems.filter((f: any) => (f.balance || (f.total_due - f.paid)) > 0)
  const feeHeadList = feeHeads?.items || feeHeads || []

  const addRow = () => setFeeRows([...feeRows, { fee_head_id: '', amount: '' }])
  const removeRow = (i: number) => setFeeRows(feeRows.filter((_, idx) => idx !== i))
  const updateRow = (i: number, key: keyof FeeRow, val: string) => {
    setFeeRows(feeRows.map((r, idx) => idx === i ? { ...r, [key]: val } : r))
    // Auto-fill outstanding balance
    if (key === 'fee_head_id') {
      const outstanding = outstandingHeads.find((f: any) => f.fee_head_id?.toString() === val)
      if (outstanding) {
        const bal = outstanding.balance || (outstanding.total_due - outstanding.paid)
        setFeeRows(prev => prev.map((r, idx) => idx === i ? { ...r, amount: bal.toString() } : r))
      }
    }
  }

  const totalAmount = feeRows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0)

  const handleSubmit = async () => {
    if (!selectedStudent) { toast.error('Please select a student'); return }
    const validRows = feeRows.filter((r) => r.fee_head_id && parseFloat(r.amount) > 0)
    if (validRows.length === 0) { toast.error('Add at least one fee item'); return }

    const payload: any = {
      student_id: selectedStudent.id,
      receipt_date: receiptDate,
      payment_mode: paymentMode,
      remarks,
      items: validRows.map((r) => ({
        fee_head_id: Number(r.fee_head_id),
        amount: parseFloat(r.amount),
      })),
    }

    // Payment details
    if (['CHEQUE', 'DEMAND_DRAFT'].includes(paymentMode)) {
      payload.payment_details = { cheque_number: chequeNumber, cheque_date: chequeDate, bank_name: bankName, branch_name: branchName }
    } else if (['UPI', 'NEFT', 'ONLINE'].includes(paymentMode)) {
      payload.payment_details = { upi_reference: upiRef, transaction_id: transactionId, bank_name: bankName }
    }

    setSubmitting(true)
    try {
      const res = await client.post('/receipts/', payload)
      setReceipt(res.data)
      toast.success('Receipt created successfully!')
      setFeeRows([{ fee_head_id: '', amount: '' }])
      setRemarks('')
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Failed to create receipt'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setSubmitting(false)
    }
  }

  const handlePrint = async () => {
    if (!receipt) return
    try {
      const res = await client.get(`/receipts/${receipt.id}/pdf`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      toast.error('Failed to generate PDF')
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Fee Collection</h1>
      </div>

      {/* Success state */}
      {receipt && (
        <div className="card bg-emerald-50 border-emerald-200 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
              <CheckCircle size={24} className="text-emerald-600" />
            </div>
            <div className="flex-1">
              <div className="text-lg font-semibold text-emerald-800">Receipt Created!</div>
              <div className="text-emerald-700 text-sm">
                Receipt No: <strong>{receipt.receipt_number}</strong> | Amount: <strong>{fmt(receipt.total_amount)}</strong>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={handlePrint} className="btn-success">
                <Printer size={15} /> Print Receipt
              </button>
              <button onClick={() => navigate(`/receipts/${receipt.id}`)} className="btn-secondary">
                View Receipt
              </button>
              <button onClick={() => { setReceipt(null); setSelectedStudent(null) }} className="btn-primary">
                New Collection
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Student + Form */}
        <div className="xl:col-span-2 space-y-5">
          {/* Student Search */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4">Step 1: Select Student</h2>
            <div className="relative" ref={searchRef}>
              <Search size={15} className="absolute left-3 top-3 text-gray-400" />
              <input
                className="input pl-9"
                placeholder="Search by name, roll number, admission no, or mobile..."
                value={studentSearch}
                onChange={(e) => handleSearchChange(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              />
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-20 mt-1 overflow-hidden">
                  {suggestions.map((s: any) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => selectStudent(s)}
                      className="w-full text-left px-4 py-3 hover:bg-indigo-50 transition-colors border-b border-gray-100 last:border-0"
                    >
                      <div className="font-medium text-gray-900">{s.full_name}</div>
                      <div className="text-xs text-gray-500">
                        {s.admission_number && `Adm: ${s.admission_number}`}
                        {s.roll_number && ` · Roll: ${s.roll_number}`}
                        {s.course_name && ` · ${s.course_name}`}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {loadingStudent && (
              <div className="flex items-center gap-2 mt-3 text-gray-500">
                <Loader2 size={16} className="animate-spin" />
                Loading student...
              </div>
            )}

            {/* Selected student card */}
            {selectedStudent && (
              <div className="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-200 rounded-full flex items-center justify-center">
                  <User size={22} className="text-indigo-700" />
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900 text-lg">{selectedStudent.full_name}</div>
                  <div className="text-sm text-gray-600">
                    {selectedStudent.course_name} · {selectedStudent.batch_name} · {selectedStudent.session_name}
                  </div>
                  <div className="text-xs text-gray-500">
                    Adm: {selectedStudent.admission_number || '-'} · Roll: {selectedStudent.roll_number || '-'}
                  </div>
                </div>
                <button
                  onClick={() => { setSelectedStudent(null); setReceipt(null) }}
                  className="text-gray-400 hover:text-red-500"
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          {/* Fee Items */}
          {selectedStudent && (
            <div className="card">
              <h2 className="font-semibold text-gray-900 mb-4">Step 2: Fee Items</h2>

              {/* Outstanding summary */}
              {outstandingHeads.length > 0 && (
                <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-1">
                    <AlertCircle size={14} /> Outstanding Dues
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {outstandingHeads.map((f: any) => (
                      <span key={f.fee_head_id} className="text-xs bg-amber-100 text-amber-800 rounded px-2 py-0.5">
                        {f.fee_head_name}: {fmt(f.balance || (f.total_due - f.paid))}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <table className="tbl mb-3">
                <thead>
                  <tr>
                    <th>Fee Head</th>
                    <th>Amount (₹)</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {feeRows.map((row, i) => (
                    <tr key={i}>
                      <td>
                        <select
                          className="input py-1 text-sm"
                          value={row.fee_head_id}
                          onChange={(e) => updateRow(i, 'fee_head_id', e.target.value)}
                        >
                          <option value="">Select fee head</option>
                          {outstandingHeads.length > 0 && (
                            <optgroup label="Outstanding">
                              {outstandingHeads.map((f: any) => (
                                <option key={f.fee_head_id} value={f.fee_head_id}>
                                  {f.fee_head_name} (Due: {fmt(f.balance || (f.total_due - f.paid))})
                                </option>
                              ))}
                            </optgroup>
                          )}
                          <optgroup label="All Fee Heads">
                            {feeHeadList.map((fh: any) => (
                              <option key={fh.id} value={fh.id}>{fh.name}</option>
                            ))}
                          </optgroup>
                        </select>
                      </td>
                      <td>
                        <input
                          type="number"
                          step="0.01"
                          min={0}
                          className="input py-1 text-sm"
                          placeholder="0.00"
                          value={row.amount}
                          onChange={(e) => updateRow(i, 'amount', e.target.value)}
                        />
                      </td>
                      <td>
                        {feeRows.length > 1 && (
                          <button type="button" onClick={() => removeRow(i)} className="text-red-400 hover:text-red-600">
                            <Trash2 size={15} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button type="button" onClick={addRow} className="btn-secondary btn-sm">
                <Plus size={13} /> Add Row
              </button>
            </div>
          )}

          {/* Payment Details */}
          {selectedStudent && (
            <div className="card">
              <h2 className="font-semibold text-gray-900 mb-4">Step 3: Payment Details</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Payment Mode</label>
                  <select className="input" value={paymentMode} onChange={(e) => setPaymentMode(e.target.value)}>
                    {PAYMENT_MODES.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Receipt Date</label>
                  <input
                    type="date"
                    className="input"
                    value={receiptDate}
                    onChange={(e) => setReceiptDate(e.target.value)}
                  />
                </div>

                {/* Cheque / DD specific */}
                {['CHEQUE', 'DEMAND_DRAFT'].includes(paymentMode) && (
                  <>
                    <div>
                      <label className="label">Cheque/DD Number</label>
                      <input className="input" value={chequeNumber} onChange={(e) => setChequeNumber(e.target.value)} placeholder="Instrument number" />
                    </div>
                    <div>
                      <label className="label">Cheque/DD Date</label>
                      <input type="date" className="input" value={chequeDate} onChange={(e) => setChequeDate(e.target.value)} />
                    </div>
                    <div>
                      <label className="label">Bank Name</label>
                      <input className="input" value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="Issuing bank" />
                    </div>
                    <div>
                      <label className="label">Branch Name</label>
                      <input className="input" value={branchName} onChange={(e) => setBranchName(e.target.value)} placeholder="Bank branch" />
                    </div>
                  </>
                )}

                {/* UPI / NEFT / Online */}
                {['UPI', 'NEFT', 'ONLINE'].includes(paymentMode) && (
                  <>
                    <div>
                      <label className="label">{paymentMode === 'UPI' ? 'UPI Reference' : 'Transaction ID'}</label>
                      <input className="input" value={upiRef} onChange={(e) => setUpiRef(e.target.value)} placeholder="Reference / UTR number" />
                    </div>
                    <div>
                      <label className="label">Bank Name</label>
                      <input className="input" value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="Bank name" />
                    </div>
                  </>
                )}

                <div className="sm:col-span-2">
                  <label className="label">Remarks</label>
                  <textarea
                    className="input"
                    rows={2}
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    placeholder="Optional remarks..."
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Summary Panel */}
        <div className="space-y-5">
          {/* Fee Summary */}
          {selectedStudent && feeItems.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-gray-900 mb-3">Fee Summary</h2>
              <table className="tbl text-xs">
                <thead><tr><th>Fee Head</th><th className="text-right">Due</th><th className="text-right">Paid</th><th className="text-right">Balance</th></tr></thead>
                <tbody>
                  {feeItems.map((f: any) => (
                    <tr key={f.fee_head_id || f.id}>
                      <td>{f.fee_head_name || f.name}</td>
                      <td className="text-right">{fmt(f.total_due)}</td>
                      <td className="text-right text-emerald-700">{fmt(f.paid)}</td>
                      <td className={`text-right font-medium ${(f.balance || f.total_due - f.paid) > 0 ? 'text-red-600' : ''}`}>
                        {fmt(f.balance || (f.total_due - f.paid))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Receipt Preview */}
          {selectedStudent && (
            <div className="card border-2 border-dashed border-indigo-200">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <IndianRupee size={16} className="text-indigo-600" />
                Receipt Preview
              </h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Student:</span>
                  <span className="font-medium">{selectedStudent.full_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Date:</span>
                  <span>{receiptDate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Mode:</span>
                  <span className="badge-info">
                    {PAYMENT_MODES.find((m) => m.value === paymentMode)?.label}
                  </span>
                </div>
                <div className="border-t pt-2 mt-2">
                  {feeRows
                    .filter((r) => r.fee_head_id && parseFloat(r.amount) > 0)
                    .map((r, i) => {
                      const head = feeHeadList.find((fh: any) => fh.id?.toString() === r.fee_head_id)
                      return (
                        <div key={i} className="flex justify-between text-xs py-1 border-b border-gray-100">
                          <span>{head?.name || '—'}</span>
                          <span className="font-medium">{fmt(parseFloat(r.amount) || 0)}</span>
                        </div>
                      )
                    })}
                </div>
                <div className="flex justify-between text-base font-bold text-indigo-800 pt-2">
                  <span>Total</span>
                  <span>{fmt(totalAmount)}</span>
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={submitting || !selectedStudent || totalAmount <= 0}
                className="btn-success w-full mt-5 py-3 text-base"
              >
                {submitting ? (
                  <><Loader2 size={18} className="animate-spin" /> Processing…</>
                ) : (
                  <><CheckCircle size={18} /> Collect {fmt(totalAmount)}</>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
