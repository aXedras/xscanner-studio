import InfoPanel from './InfoPanel'
import { useUiMessages } from '../../ui/messages/UiMessagesContext'

type Props = {
  closeLabel: string
}

export default function MessageCenter({ closeLabel }: Props) {
  const { messages, dismiss } = useUiMessages()

  const visible = messages.filter(m => m.variant !== 'success')
  if (visible.length === 0) return null

  return (
    <div className="w-full flex flex-col gap-2" data-ui-message-center="true">
      {visible.map(message => (
        <InfoPanel
          key={message.id}
          variant={message.variant}
          title={message.title}
          description={message.description}
          details={message.details}
          closeLabel={closeLabel}
          onClose={() => dismiss(message.id)}
        />
      ))}
    </div>
  )
}
