import type { OrderRow, OrderUpdateInput } from '../../services/core/order/types'
import { formatDecimalInput } from '../../lib/utils/number'

export type OrderCanonicalFieldsForm = {
  documentIssuer: string
  documentNumber: string
  documentDate: string

  orderNumber: string
  orderDate: string
  valueDate: string
  shippingDate: string
  transactionType: string

  sellerName: string
  buyerName: string

  currency: string
  shippingChargesAmount: string
  otherChargesAmount: string
  subtotalAmount: string
  totalAmount: string
}

function toDateInputValue(value: string | null): string {
  if (!value) return ''
  // API returns DATE as "YYYY-MM-DD" already.
  return value
}

function parseNullableNumber(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const normalized = trimmed.replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatMoneyInput(value: number | null | undefined, language: string): string {
  if (value === null || value === undefined) return ''
  return formatDecimalInput(value, language, { maximumFractionDigits: 6 })
}

export function createOrderCanonicalFieldsForm(order: OrderRow, language: string): OrderCanonicalFieldsForm {
  return {
    documentIssuer: order.document_issuer ?? '',
    documentNumber: order.document_number ?? '',
    documentDate: toDateInputValue(order.document_date),

    orderNumber: order.order_number ?? '',
    orderDate: toDateInputValue(order.order_date),
    valueDate: toDateInputValue(order.value_date),
    shippingDate: toDateInputValue(order.shipping_date),
    transactionType: order.transaction_type ?? '',

    sellerName: order.seller_name ?? '',
    buyerName: order.buyer_name ?? '',

    currency: order.currency ?? '',
    shippingChargesAmount: formatMoneyInput(order.shipping_charges_amount, language),
    otherChargesAmount: formatMoneyInput(order.other_charges_amount, language),
    subtotalAmount: formatMoneyInput(order.subtotal_amount, language),
    totalAmount: formatMoneyInput(order.total_amount, language),
  }
}

export function buildOrderUpdatePatch(form: OrderCanonicalFieldsForm): OrderUpdateInput {
  return {
    order_number: form.orderNumber.trim() || null,
    order_date: form.orderDate || null,
    value_date: form.valueDate || null,
    shipping_date: form.shippingDate || null,
    transaction_type: form.transactionType.trim() || null,

    seller_name: form.sellerName.trim() || null,
    buyer_name: form.buyerName.trim() || null,

    currency: form.currency.trim() || null,
    shipping_charges_amount: parseNullableNumber(form.shippingChargesAmount),
    other_charges_amount: parseNullableNumber(form.otherChargesAmount),
    subtotal_amount: parseNullableNumber(form.subtotalAmount),
    total_amount: parseNullableNumber(form.totalAmount),
  } as OrderUpdateInput
}
