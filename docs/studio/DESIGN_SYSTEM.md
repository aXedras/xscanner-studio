# xScanner Studio Design System

Minimales CSS-System basierend auf aXedras Design-Prinzipien.

## Philosophie

- **Einfachheit**: Nur 8 CSS-Klassen, Rest mit Tailwind
- **Konsistenz**: aXedras Brand Colors (Gold, Success, Error, Warning)
- **Wartbarkeit**: CSS Custom Properties für Farben
- **Performance**: Minimaler CSS-Footprint (~70 Zeilen)

## CSS Custom Properties

```css
:root {
  --gold: 196 160 83;        /* Brand Gold */
  --gold-dark: 154 122 58;   /* Darker Gold */
  --success: 92 184 92;      /* Success Green */
  --error: 255 59 48;        /* Error Red */
  --warning: 243 156 18;     /* Warning Orange */
  --dark: 28 28 30;          /* Dark Background */
}
```

**Usage**: `rgb(var(--gold))` für RGB-Farben

## CSS Klassen (8 Total)

### Layouts

#### `.app-layout`
Container mit Hintergrund-Gradient und subtilen Radial Gradients.
```tsx
<div className="app-layout">
  {/* Page content */}
</div>
```

#### `.content`
Max-width 7xl Container mit responsive Padding.
```tsx
<main className="content">
  {/* Main content */}
</main>
```

### Components

#### `.card`
Weiße Card mit Glassmorphism, Border, Hover-Effekten.
```tsx
<div className="card">
  {/* Card content */}
</div>
```
**Usage**: Stats Cards, Content Cards

#### `.card-gold`
Gold-Gradient Card mit weißem Text, größeres Padding.
```tsx
<div className="card-gold">
  {/* Feature content */}
</div>
```
**Usage**: Feature Cards, Call-to-Actions

#### `.nav`
Navigation Bar mit Glassmorphism und Border.
```tsx
<nav className="nav">
  {/* Navigation content */}
</nav>
```

#### `.btn`
Gold Primary Button mit Hover-Effekten.
```tsx
<button className="btn">Logout</button>
```

### Elements

#### `.logo`
Logo Box mit Gold-Gradient Background.
```tsx
<div className="logo">
  <svg className="w-6 h-6 text-white">...</svg>
</div>
```

#### `.icon-box`
Icon Container, 12x12 mit Border-Radius.
```tsx
<div className="icon-box" style={{ backgroundColor: 'rgba(196, 160, 83, 0.1)' }}>
  <svg className="w-6 h-6">...</svg>
</div>
```

## Inline Styling (Tailwind)

Alles andere wird direkt mit Tailwind inline gestylt:

### Typografie
```tsx
<h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 bg-clip-text text-transparent">
<p className="text-lg text-gray-600">
```

### Grids
```tsx
<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
```

### Flex
```tsx
<div className="flex items-center gap-3">
<div className="flex justify-between items-center h-16">
```

### Buttons (Custom)
```tsx
<button className="w-full px-6 py-3 font-medium bg-white text-gray-900 rounded-lg hover:bg-gray-100 transition-all">
```

## Farben (aXedras)

| Color | Hex | RGB | Usage |
|-------|-----|-----|-------|
| Gold | #C4A053 | 196 160 83 | Primary Brand, Buttons, Gradients |
| Gold Dark | #9A7A3A | 154 122 58 | Hover States, Gradient End |
| Success | #5CB85C | 92 184 92 | Status Indicators, Success States |
| Error | #FF3B30 | 255 59 48 | Error Messages, Destructive Actions |
| Warning | #F39C12 | 243 156 18 | Warning Messages, Pending States |
| Dark | #1C1C1E | 28 28 30 | Dark Backgrounds (Login) |

## Komponenten Patterns

### Stats Card
```tsx
<div className="card">
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm font-medium text-gray-600 mb-1">Label</p>
      <p className="text-3xl font-bold text-gray-900">Value</p>
    </div>
    <div className="icon-box" style={{ backgroundColor: 'rgba(196, 160, 83, 0.1)' }}>
      <svg className="w-6 h-6" style={{ color: 'rgb(196, 160, 83)' }}>...</svg>
    </div>
  </div>
</div>
```

### Feature Card
```tsx
<div className="card-gold">
  <div className="mb-6">
    <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center mb-4">
      <svg className="w-8 h-8">...</svg>
    </div>
    <h3 className="text-2xl font-bold mb-2">Title</h3>
    <p className="text-base leading-relaxed text-white/80">Description</p>
  </div>
  <button className="w-full px-6 py-3 font-medium bg-white text-gray-900 rounded-lg hover:bg-gray-100 transition-all">
    Action
  </button>
</div>
```

### Navigation
```tsx
<nav className="nav">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div className="flex justify-between items-center h-16">
      <div className="flex items-center gap-3">
        <div className="logo">
          <svg className="w-6 h-6 text-white">...</svg>
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
          Brand
        </span>
      </div>
      <button className="btn">Action</button>
    </div>
  </div>
</nav>
```

## Best Practices

1. **Verwende CSS-Klassen** nur für wiederverwendbare Komponenten
2. **Inline Tailwind** für einmalige/spezifische Styles
3. **RGB-Format** für dynamische Farben: `rgb(var(--gold))`
4. **Glassmorphism**: `backdrop-blur-sm` + `bg-white/80`
5. **Hover-Effekte**: `hover:shadow-lg hover:scale-[1.02]`
6. **Responsive**: `text-4xl md:text-5xl`, `grid-cols-1 md:grid-cols-4`

## Erweiterung

Neue CSS-Klasse nur hinzufügen wenn:
- Mindestens 3x verwendet
- Nicht einfach mit Tailwind inline möglich
- Klare semantische Bedeutung

Dokumentation aktualisieren bei jeder neuen Klasse.
