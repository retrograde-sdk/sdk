# RetroArcade SDK

28,000+ HTML5 games in a single script tag. Unblockable. Self-contained.

## Quick Start

Add one line to your HTML:

```html
<div id="arcade" style="width:100%;height:100vh"></div>
<script src="https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/retro.min.js"></script>
<script>new RetroArcade({target:'#arcade'}).init();</script>
```

Or use the `data-target` attribute:

```html
<div id="arcade" style="width:100%;height:100vh"></div>
<script src="https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/retro.min.js" data-target="#arcade"></script>
```

## Configuration

```js
new RetroArcade({
  target: '#arcade',  // CSS selector or DOM element (required)
}).init();
```

## Features

- **28,154 games** — full HTML5 game library
- **Categories** — 21 genres with filtering
- **Search** — instant search across all games
- **Favorites** — saved locally, persists across sessions
- **Recently Played** — automatic history tracking
- **Fullscreen** — one-click fullscreen mode
- **Monochrome UI** — sleek grayscale design, covers colorize on hover

## Architecture

All traffic is proxied through a Cloudflare Worker to ensure unblockable access:

```
Browser → retro.min.js → jsdelivr (game catalog) → Cloudflare Worker (game/image proxy) → GameMonetize CDN
```

No direct connections to game CDN servers — everything routes through `workers.dev`, `jsdelivr.net`, and `githubusercontent.com`, all of which are unblockable in school environments.

## Files

| File | Description |
|------|-------------|
| `retro.min.js` | Production SDK (obfuscated) |
| `retro.js` | Source code |
| `worker.js` | Cloudflare Worker proxy |
| `build.js` | Build & obfuscation script |
| `data/games.json` | Game catalog (28,154 entries) |
| `data/categories.json` | Category definitions |

## Building from Source

```bash
npm install terser
node build.js
```

Output: `retro.min.js` — obfuscated, URL-encoded, anti-debug protected.

## License

Private. All rights reserved.
