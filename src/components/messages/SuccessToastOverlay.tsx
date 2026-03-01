import InfoPanel from './InfoPanel'
import { useUiMessages } from '../../ui/messages/UiMessagesContext'

type Props = {
  closeLabel: string
}

export default function SuccessToastOverlay({ closeLabel }: Props) {
  const { messages, dismiss } = useUiMessages()

  const visible = messages.filter(m => m.variant === 'success')
  if (visible.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex w-[min(28rem,calc(100vw-2rem))] flex-col gap-2 pointer-events-none"
      data-ui-message-center="true"
    >
      {visible.map(message => (
        <div key={message.id} className="pointer-events-auto">
          <InfoPanel
            variant={message.variant}
            title={message.title}
            description={message.description}
            details={message.details}
            closeLabel={closeLabel}
            onClose={() => dismiss(message.id)}
          />
        </div>
      ))}
    </div>
  )
}
