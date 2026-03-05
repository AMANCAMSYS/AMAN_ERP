import { useTheme } from '../../context/ThemeContext'

function FloatingThemeToggle() {
    const { darkMode, toggleDarkMode } = useTheme()

    return (
        <button
            type="button"
            className="floating-theme-toggle"
            onClick={toggleDarkMode}
            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            title={darkMode ? 'Light mode' : 'Dark mode'}
        >
            <span className="floating-theme-toggle-icon" aria-hidden="true">
                {darkMode ? '☀' : '☾'}
            </span>
        </button>
    )
}

export default FloatingThemeToggle