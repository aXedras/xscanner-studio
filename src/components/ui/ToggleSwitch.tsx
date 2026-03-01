type Props = {
  checked: boolean
  onChange: (next: boolean) => void
  disabled?: boolean
  label: string
}

export function ToggleSwitch({ checked, onChange, disabled = false, label }: Props) {
  return (
    <button
      type="button"
      className="w-full flex items-center justify-between gap-3 rounded-md border border-[color:var(--bg-card-border)] px-3 py-2 text-left"
      onClick={() => onChange(!checked)}
      disabled={disabled}
      aria-pressed={checked}
    >
      <span className="text-sm text-[color:var(--text-secondary)]">{label}</span>
      <span
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-[color:var(--color-gold)]' : 'bg-black/20 dark:bg-white/20'
        } ${disabled ? 'opacity-60' : ''}`}
        aria-hidden="true"
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-1'
          }`}
        />
      </span>
    </button>
  )
}
