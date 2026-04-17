# RetroArcade SDK

A lightweight, embeddable HTML5 game arcade with **28,000+ games** — drop it into any website with a single script tag.

## Quick Start

Add the SDK to your page and initialize it:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>My Arcade</title>
</head>
<body>
  <!-- Container where the arcade will render -->
  <div id="retro-arcade" style="width:100%;height:600px;"></div>

  <!-- Load the SDK -->
  <script src="retro.min.js"></script>
  <script>
    new Retrograde({ target: '#retro-arcade' }).init();
  </script>
</body>
</html>
```

That's it — the arcade loads automatically with a full game catalog, search, categories, and a game player.

## Installation

### Option 1: Self-hosted (recommended)

Download `retro.min.js` and serve it from your own domain:

```html
<script src="/js/retro.min.js"></script>
```

### Option 2: CDN

```html
<script src="https://cdn.jsdelivr.net/gh/xazalea/retrograde@main/sdk/retro.min.js"></script>
```

## Configuration

### Constructor Options

```javascript
new Retrograde({
  target: '#retro-arcade',  // CSS selector or DOM element (required)
}).init();
```

| Option    | Type             | Default           | Description                    |
|-----------|------------------|-------------------|--------------------------------|
| `target`  | `string` \| `Element` | `'#retro-arcade'` | Container selector or element  |

### Auto-initialization

You can also initialize the SDK declaratively using a `data-target` attribute:

```html
<script src="retro.min.js" data-target="#retro-arcade"></script>
```

This will automatically create a `Retrograde` instance targeting the specified element.

## Features

- 🎮 **28,000+ HTML5 games** — Instant access to a massive game catalog
- 🔍 **Real-time search** — Find any game in milliseconds
- 📂 **15 categories** — Action, Racing, Puzzle, Sports, and more
- 🎯 **Featured game** — Randomized spotlight on every page load
- ⭐ **Favorites** — Users can save their favorite games (persisted in localStorage)
- 🕐 **Recently played** — Automatic history tracking
- 🔄 **Multi-proxy loading** — Automatic fallback chain ensures games load even on restricted networks
- 📱 **Fully responsive** — Works on mobile, tablet, and desktop
- 🎨 **Dark theme** — Sleek, modern UI with smooth animations
- ⚡ **Zero dependencies** — Pure vanilla JS, ~62KB minified
- 🔒 **Tamper-resistant** — Multiple layers of code protection

## API Reference

### `new Retrograde(options)`

Creates a new Retrograde instance.

```javascript
const arcade = new Retrograde({ target: '#arcade' });
```

### `arcade.init()`

Initializes the arcade — loads the game catalog, renders the UI, and sets up event handlers. Returns the instance for chaining.

```javascript
const arcade = new Retrograde({ target: '#arcade' }).init();
```

## Styling

The SDK injects its own scoped CSS into the page. All styles are prefixed with `ra-` to avoid conflicts with your existing styles.

The arcade fills its container element, so set the container's dimensions to control the size:

```css
#retro-arcade {
  width: 100%;
  height: 100vh;  /* Full viewport height */
}
```

## Browser Support

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+
- Mobile browsers (iOS Safari, Chrome for Android)

## License

MIT License — free for personal and commercial use.
