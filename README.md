# Retrograde SDK

**Embed 28,000+ HTML5 games in your site with one script tag.**

```html
<div id="retro-arcade"></div>
<script src="https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/retro.min.js"></script>
<script>
  new Retrograde({ target: '#retro-arcade' }).init();
</script>
```

That's it. No build step, no dependencies, no API keys.

## Features

- **28,154 games** across 21 categories — action, racing, puzzle, strategy, and more
- **23,273 video previews** — hover any game card to see a live MP4 preview
- **Monochrome design** — grayscale thumbnails bloom into full color on hover
- **Multi-proxy loading** — automatic fallback chain (direct → Google Proxy → alt CDN)
- **Zero dependencies** — single 63KB file, no framework required
- **Mobile responsive** — adaptive grid layout for any screen size
- **Offline-capable** — catalog caches to localStorage for 24 hours
- **Search** — instant full-text search across all 28k+ game titles
- **Favorites & Recent** — persistent user collections via localStorage

## Quick Start

### 1. Add the container

```html
<div id="retro-arcade" style="width:100%;height:100vh"></div>
```

### 2. Load the SDK

```html
<script src="https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/retro.min.js"></script>
```

### 3. Initialize

```html
<script>
  new Retrograde({ target: '#retro-arcade' }).init();
</script>
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target` | `string \| Element` | `'#retro-arcade'` | CSS selector or DOM element to mount into |

## API

The SDK automatically creates a full game portal with:

- **Home view** — featured game + paginated grid of all games
- **Category filtering** — 21 categories with game counts
- **Search** — type 2+ characters to search all games instantly
- **Favorites** — heart icon to save games, persists across sessions
- **Recent** — auto-tracked play history (last 50 games)
- **Game player** — fullscreen modal with proxy fallback chain
- **Video previews** — autoplay on card hover for 23k+ games

## Architecture

```
retro.min.js (63KB)
├── CatalogManager    — fetches & caches game data from CDN
├── GamePlayer        — multi-proxy iframe loading with splash screen
└── Retrograde        — main UI controller (search, categories, grid)
```

### Data Format

Games are stored as compact arrays to minimize transfer size:

```json
["game-slug", "Display Name", categoryId, "gameHash", "optionalVideoUrl"]
```

Categories:

```json
{"1": {"s": "action-games", "n": "Action Games"}, ...}
```

### CDN Endpoints

| Asset | URL |
|-------|-----|
| Game HTML | `html5.gamemonetize.co/{hash}/` |
| Thumbnails | `img.gamemonetize.com/{hash}/512x384.jpg` |
| Video previews | `gamemonetize.video/{path}.mp4` |
| Game catalog | `cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/games.min.json` |
| Categories | `cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/categories.json` |

### Proxy Chain

When a user clicks Play, the SDK tries three methods in order:

1. **Direct** — load game iframe from primary CDN
2. **Google Proxy** — fetch via Google Apps Script proxy (bypasses some network restrictions)
3. **Fallback CDN** — try secondary CDN endpoint

Each attempt has a 12-second timeout before switching to the next method.

## Live Demo

**[Open the demo](https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/index.html)** — fully interactive, no installation needed.

## Browser Support

| Browser | Support |
|---------|----------|
| Chrome 80+ | ✅ Full |
| Firefox 78+ | ✅ Full |
| Safari 14+ | ✅ Full |
| Edge 80+ | ✅ Full |
| Mobile Safari | ✅ Full |
| Mobile Chrome | ✅ Full |

## License

This SDK is provided for integration purposes. Game content is sourced from [GameMonetize](https://gamemonetize.com) and subject to their terms of service.
