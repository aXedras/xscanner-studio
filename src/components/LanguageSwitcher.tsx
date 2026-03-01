import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'de' ? 'en' : 'de'
    i18n.changeLanguage(newLang)
  }

  const currentLang = i18n.language?.toLowerCase().startsWith('de') ? 'DE' : 'EN'
  const nextLang = currentLang === 'DE' ? 'EN' : 'DE'

  return (
    <button onClick={toggleLanguage} className="btn btn-outline btn-icon" aria-label={`Switch language to ${nextLang}`}>
      {currentLang}
    </button>
  )
}
