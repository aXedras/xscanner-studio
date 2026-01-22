import type { TFunction } from 'i18next'
import { NavLink } from 'react-router-dom'

type NavItem = {
  to: string
  label: string
  end?: boolean
}

type Props = {
  t: TFunction
}

export function TopNavigation({ t }: Props) {
  const items: NavItem[] = [
    { to: '/', label: t('common.nav.dashboard'), end: true },
    { to: '/extractions', label: t('common.nav.extractions') },
  ]

  return (
    <div className="flex items-center gap-6">
      {items.map(item => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            [
              'px-2 py-1 text-sm font-medium transition-colors border-b-2',
              isActive
                ? 'text-[color:var(--text-primary)] border-[color:var(--color-gold)]'
                : 'text-[color:var(--text-secondary)] border-transparent hover:text-[color:var(--color-gold)]',
            ].join(' ')
          }
        >
          {item.label}
        </NavLink>
      ))}
    </div>
  )
}
