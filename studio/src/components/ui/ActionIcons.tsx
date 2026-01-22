type IconProps = {
  className?: string
  size?: number | string
}

function toCssSize(size: number | string | undefined): string {
  if (size === undefined) return '1em'
  return typeof size === 'number' ? `${size}px` : size
}

function mergeClassNames(base: string, extra?: string): string {
  return extra ? `${base} ${extra}` : base
}

export function EditIcon({ className, size }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={mergeClassNames('shrink-0', className)}
      style={{ width: toCssSize(size), height: toCssSize(size) }}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 20h9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function DetailsIcon({ className, size }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={mergeClassNames('shrink-0', className)}
      style={{ width: toCssSize(size), height: toCssSize(size) }}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

export function RegisterIcon({ className, size }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={mergeClassNames('shrink-0', className)}
      style={{ width: toCssSize(size), height: toCssSize(size) }}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function RejectIcon({ className, size }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={mergeClassNames('shrink-0', className)}
      style={{ width: toCssSize(size), height: toCssSize(size) }}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function CorrectIcon({ className, size }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={mergeClassNames('shrink-0', className)}
      style={{ width: toCssSize(size), height: toCssSize(size) }}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 20h9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M8.5 12.5l2 2 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
