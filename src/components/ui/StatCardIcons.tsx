import type { ReactNode } from 'react'
import { CorrectIcon, RegisterIcon, RejectIcon } from './ActionIcons'

type WrapperProps = {
  variant: 'gold' | 'orange' | 'green' | 'red'
  children: ReactNode
}

function Wrapper({ variant, children }: WrapperProps) {
  const className = `stat-icon stat-icon-${variant}`
  const colorVar =
    variant === 'gold'
      ? 'var(--color-gold)'
      : variant === 'orange'
        ? 'var(--color-warning)'
        : variant === 'green'
          ? 'var(--color-success)'
          : 'var(--color-error)'

  return (
    <div className={className}>
      <span className="inline-flex" style={{ color: colorVar }}>
        {children}
      </span>
    </div>
  )
}

export function StatIconTotal() {
  return (
    <Wrapper variant="gold">
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    </Wrapper>
  )
}

export function StatIconPending() {
  return (
    <Wrapper variant="orange">
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </Wrapper>
  )
}

export function StatIconCorrected() {
  return (
    <Wrapper variant="gold">
      <CorrectIcon size={24} />
    </Wrapper>
  )
}

export function StatIconValidated() {
  return (
    <Wrapper variant="green">
      <RegisterIcon size={24} />
    </Wrapper>
  )
}

export function StatIconRejected() {
  return (
    <Wrapper variant="red">
      <RejectIcon size={24} />
    </Wrapper>
  )
}

export function StatIconError() {
  return (
    <Wrapper variant="red">
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </Wrapper>
  )
}
