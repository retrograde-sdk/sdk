#!/usr/bin/env python3
"""
Retrograde Game Integration Pipeline
=====================================
Fetches the latest game catalog from gamemonetize.com/feed.json (~36k games),
merges with existing SDK data (preserving video URLs), and generates all
necessary data files for the SDK and API.

Usage:
  python3 integrate_games.py [--skip-fetch] [--dry-run]

Output files:
  - sdk/data/games.json      — Full catalog [slug, name, catId, hash]
  - sdk/data/games.min.json  — Compact catalog [slug, name, catId, hash, videoUrl]
  - sdk/data/videos.json     — Hash → video URL mapping
  - sdk/data/categories.json — Category ID → {slug, name} mapping
  - data/games/pages/*.json  — Paginated API data (if --with-pages)
  - data/categories.json     — Full category metadata for API
"""

import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict

# Fix SSL certificate verification on macOS (scoped to this script only)
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
ssl._create_default_https_context = lambda: _ctx

# ─── Configuration ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK_DATA_DIR = os.path.join(BASE_DIR, 'sdk', 'data')
API_DATA_DIR = os.path.join(BASE_DIR, 'data')

FEED_URL = 'https://gamemonetize.com/feed.json'
GAMES_PER_PAGE = 50

# Category mapping: feed.json string → SDK category ID
# The feed only has 8 categories; we map them to our 20-category system
CATEGORY_MAP = {
    'Action': 1,
    'Driving': 2,       # Racing
    'Shooting': 3,
    'Arcade': 4,
    'Puzzles': 5,        # Puzzle
    'Multiplayer': 7,
    'Sports': 8,
    'Fighting': 9,
}

# Full category definitions for the SDK
SDK_CATEGORIES = {
    "0":  {"s": "uncategorized", "n": "Uncategorized"},
    "1":  {"s": "action-games", "n": "Action"},
    "2":  {"s": "racing-games", "n": "Racing"},
    "3":  {"s": "shooting-games", "n": "Shooting"},
    "4":  {"s": "arcade-games", "n": "Arcade"},
    "5":  {"s": "puzzle-games", "n": "Puzzle"},
    "6":  {"s": "strategy-games", "n": "Strategy"},
    "7":  {"s": "multiplayer-games", "n": "Multiplayer"},
    "8":  {"s": "sports-games", "n": "Sports"},
    "9":  {"s": "fighting-games", "n": "Fighting"},
    "10": {"s": "girls-games", "n": "Girls"},
    "11": {"s": "hypercasual-games", "n": "Hypercasual"},
    "12": {"s": "boys-games", "n": "Boys"},
    "13": {"s": "adventure-games", "n": "Adventure"},
    "14": {"s": "bejeweled-games", "n": "Bejeweled"},
    "15": {"s": "clicker-games", "n": "Clicker"},
    "16": {"s": "cooking-games", "n": "Cooking"},
    "17": {"s": "soccer-games", "n": "Soccer"},
    "18": {"s": "stickman-games", "n": "Stickman"},
    "19": {"s": "io-games", "n": ".IO"},
    "20": {"s": "3d-games", "n": "3D"},
}


def slugify(name):
    """Convert a game title to a URL-friendly slug."""
    slug = name.lower().strip()
    # Replace common patterns
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug or 'untitled'


def extract_hash_from_url(url):
    """Extract the game hash/catalog_id from a gamemonetize URL.
    
    URL format: https://html5.gamemonetize.co/{hash}/
    or: https://html5.gamemonetize.com/{hash}/
    """
    if not url:
        return None
    # Match the hash from the URL path
    m = re.search(r'gamemonetize\.[a-z]+/([a-z0-9]+)/?', url)
    if m:
        return m.group(1)
    # Fallback: last path segment
    parts = url.rstrip('/').split('/')
    last = parts[-1] if parts else None
    if last and re.match(r'^[a-z0-9]{20,}$', last):
        return last
    return None


def fetch_feed(url=FEED_URL, timeout=120):
    """Fetch the game feed from gamemonetize.com."""
    print(f'[1/7] Fetching game catalog from {url}...')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        print(f'  ✓ Fetched {len(data)} games from feed')
        return data
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f'  ✗ Failed to fetch feed: {e}')
        return None


def load_existing_data():
    """Load existing SDK data to preserve video URLs and other metadata."""
    print('[2/7] Loading existing SDK data...')
    
    # Load existing games.min.json (has video URLs)
    min_path = os.path.join(SDK_DATA_DIR, 'games.min.json')
    existing_videos = {}
    existing_slugs = set()
    existing_hash_to_slug = {}
    
    if os.path.exists(min_path):
        with open(min_path) as f:
            existing_min = json.load(f)
        for g in existing_min:
            slug = g[0]
            hash_id = g[3] if len(g) > 3 else None
            video_url = g[4] if len(g) > 4 and g[4] else ''
            existing_slugs.add(slug)
            if hash_id:
                existing_hash_to_slug[hash_id] = slug
                if video_url:
                    existing_videos[hash_id] = video_url
        print(f'  ✓ Loaded {len(existing_min)} existing games')
        print(f'  ✓ Found {len(existing_videos)} existing video URLs')
    else:
        print('  ⚠ No existing games.min.json found')
    
    # Load existing videos.json
    vid_path = os.path.join(SDK_DATA_DIR, 'videos.json')
    if os.path.exists(vid_path):
        with open(vid_path) as f:
            extra_videos = json.load(f)
        # Merge: videos.json may have additional entries
        for k, v in extra_videos.items():
            if v and k not in existing_videos:
                existing_videos[k] = v
        print(f'  ✓ Merged videos.json ({len(extra_videos)} entries)')
    
    # Load existing games.json (for slug→hash mapping consistency)
    full_path = os.path.join(SDK_DATA_DIR, 'games.json')
    existing_full = {}
    if os.path.exists(full_path):
        with open(full_path) as f:
            existing_full_list = json.load(f)
        for g in existing_full_list:
            if len(g) >= 4:
                existing_full[g[0]] = g  # slug → [slug, name, catId, hash]
        print(f'  ✓ Loaded {len(existing_full_list)} entries from games.json')
    
    return existing_videos, existing_slugs, existing_hash_to_slug, existing_full


def process_feed(feed_data, existing_videos, existing_slugs, existing_hash_to_slug, existing_full):
    """Process the feed data into SDK format, merging with existing data."""
    print('[3/7] Processing feed data into SDK format...')
    
    games_full = []      # [slug, name, catId, hash]
    games_min = []       # [slug, name, catId, hash, videoUrl]
    videos = {}          # hash → videoUrl
    seen_hashes = set()
    seen_slugs = set()
    slug_counters = defaultdict(int)
    cat_counts = defaultdict(int)
    unmapped_cats = defaultdict(int)
    
    for game in feed_data:
        if not isinstance(game, dict):
            continue
        
        # Extract hash from URL
        url = game.get('url', '')
        hash_id = extract_hash_from_url(url)
        if not hash_id:
            continue
        
        # Skip duplicates by hash
        if hash_id in seen_hashes:
            continue
        seen_hashes.add(hash_id)
        
        # Generate slug from title
        title = game.get('title', '').strip()
        if not title:
            title = game.get('id', 'untitled')
        
        base_slug = slugify(title)
        # Handle duplicate slugs
        slug_counters[base_slug] += 1
        if slug_counters[base_slug] > 1 or (base_slug in seen_slugs and base_slug not in existing_slugs):
            slug = f"{base_slug}-{slug_counters[base_slug]}"
        else:
            slug = base_slug
        seen_slugs.add(slug)
        
        # Map category — prefer existing category assignment over feed's 8-category mapping
        # The feed only has 8 categories; existing data may have finer-grained 20-category assignments
        existing_entry = existing_full.get(slug) or existing_full.get(existing_hash_to_slug.get(hash_id, ''))
        if existing_entry and len(existing_entry) >= 3 and existing_entry[2] != 0:
            cat_id = existing_entry[2]  # Preserve existing category
        else:
            cat_str = game.get('category', '').strip()
            cat_id = CATEGORY_MAP.get(cat_str, 0)
            if cat_str and cat_id == 0:
                unmapped_cats[cat_str] += 1
        cat_counts[cat_id] += 1
        
        # Get video URL: prefer existing, then check feed
        video_url = existing_videos.get(hash_id, '')
        
        # Build entries
        games_full.append([slug, title, cat_id, hash_id])
        games_min.append([slug, title, cat_id, hash_id, video_url])
        if video_url:
            videos[hash_id] = video_url
    
    # Also include any existing games that are NOT in the feed
    feed_hashes = seen_hashes
    existing_only_count = 0
    for g_hash, g_slug in existing_hash_to_slug.items():
        if g_hash not in feed_hashes:
            # Find full data from existing_full
            if g_slug in existing_full:
                eg = existing_full[g_slug]
                video_url = existing_videos.get(g_hash, '')
                games_full.append(eg[:4])
                games_min.append(eg[:4] + [video_url])
                if video_url:
                    videos[g_hash] = video_url
                existing_only_count += 1
    
    if existing_only_count > 0:
        print(f'  ℹ Preserved {existing_only_count} games from existing data not in feed')
    
    # Sort by category then name for consistent ordering
    games_full.sort(key=lambda g: (g[2], g[1].lower()))
    games_min.sort(key=lambda g: (g[2], g[1].lower()))
    
    # Report
    print(f'  ✓ Total games: {len(games_full)}')
    print(f'  ✓ Games with video: {len(videos)}')
    print(f'  ✓ Games without video: {len(games_min) - len(videos)}')
    print(f'\n  Category distribution:')
    for cat_id in sorted(cat_counts.keys()):
        cat_name = SDK_CATEGORIES.get(str(cat_id), {}).get('n', f'Cat {cat_id}')
        print(f'    {cat_id:2d} ({cat_name:15s}): {cat_counts[cat_id]:5d} games')
    
    if unmapped_cats:
        print(f'\n  ⚠ Unmapped categories:')
        for cat, count in sorted(unmapped_cats.items(), key=lambda x: -x[1]):
            print(f'    "{cat}": {count} games → assigned to category 0')
    
    return games_full, games_min, videos, cat_counts


def generate_category_data(cat_counts):
    """Generate updated categories.json for both SDK and API."""
    print('[4/7] Generating category data...')
    
    # SDK categories: only include categories that have games
    sdk_cats = {}
    for cat_id_str, cat_info in SDK_CATEGORIES.items():
        cat_id = int(cat_id_str)
        if cat_id in cat_counts and cat_counts[cat_id] > 0:
            sdk_cats[cat_id_str] = {"s": cat_info["s"], "n": cat_info["n"]}
        elif cat_id == 0 and cat_counts.get(0, 0) > 0:
            sdk_cats[cat_id_str] = {"s": cat_info["s"], "n": cat_info["n"]}
    
    # Ensure we always have the basic categories even if empty
    for cat_id_str in ["1", "2", "3", "4", "5", "7", "8", "9"]:
        if cat_id_str not in sdk_cats:
            sdk_cats[cat_id_str] = SDK_CATEGORIES[cat_id_str]
    
    # API categories: full format with metadata
    api_cats = {"categories": []}
    for cat_id_str in sorted(SDK_CATEGORIES.keys(), key=lambda x: int(x)):
        cat_id = int(cat_id_str)
        cat_info = SDK_CATEGORIES[cat_id_str]
        total = cat_counts.get(cat_id, 0)
        pages = (total + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE if total > 0 else 0
        api_cats["categories"].append({
            "id": cat_id,
            "slug": cat_info["s"],
            "name": cat_info["n"],
            "total": total,
            "pages": pages,
            "imageUrl": f"/assets/cat/{cat_info['s']}.jpg"
        })
    
    print(f'  ✓ SDK categories: {len(sdk_cats)} categories')
    print(f'  ✓ API categories: {len(api_cats["categories"])} categories')
    return sdk_cats, api_cats


def generate_page_data(games_full, videos, cat_counts):
    """Generate paginated game data files for the API."""
    print('[5/7] Generating paginated API data...')
    
    pages_dir = os.path.join(API_DATA_DIR, 'games', 'pages')
    cat_dir = os.path.join(API_DATA_DIR, 'games', 'cat')
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(cat_dir, exist_ok=True)
    
    total_games = len(games_full)
    total_pages = (total_games + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
    
    # Build category name lookup
    cat_name_lookup = {}
    for cid, cinfo in SDK_CATEGORIES.items():
        cat_name_lookup[int(cid)] = cinfo["n"]
    
    # Generate paginated files: all games
    for page in range(1, total_pages + 1):
        start = (page - 1) * GAMES_PER_PAGE
        end = min(start + GAMES_PER_PAGE, total_games)
        page_games = games_full[start:end]
        
        page_data = {
            "page": page,
            "total": total_games,
            "pages": total_pages,
            "games": []
        }
        
        for g in page_games:
            slug, name, cat_id, hash_id = g
            video_url = videos.get(hash_id, '')
            page_data["games"].append({
                "id": hash_id,
                "name": name,
                "slug": slug,
                "category": cat_id,
                "categoryName": cat_name_lookup.get(cat_id, "Uncategorized"),
                "tags": [],
                "tagNames": [],
                "width": 800,
                "height": 600,
                "mobile": False,
                "plays": 0,
                "rating": 0,
                "description": "",
                "instructions": "",
                "gameUrl": f"https://html5.gamemonetize.co/{hash_id}/",
                "imageUrl": f"https://img.gamemonetize.com/{hash_id}/512x384.jpg",
                "videoUrl": video_url
            })
        
        out_path = os.path.join(pages_dir, f'{page}.json')
        with open(out_path, 'w') as f:
            json.dump(page_data, f, separators=(',', ':'))
    
    print(f'  ✓ Generated {total_pages} page files in {pages_dir}')
    
    # Generate category-specific page files
    # Group games by category
    games_by_cat = defaultdict(list)
    for g in games_full:
        games_by_cat[g[2]].append(g)
    
    for cat_id, cat_games in games_by_cat.items():
        cat_slug = SDK_CATEGORIES.get(str(cat_id), {}).get("s", f"cat-{cat_id}")
        cat_page_dir = os.path.join(cat_dir, cat_slug)
        os.makedirs(cat_page_dir, exist_ok=True)
        
        total_cat = len(cat_games)
        cat_pages = (total_cat + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
        
        for page in range(1, cat_pages + 1):
            start = (page - 1) * GAMES_PER_PAGE
            end = min(start + GAMES_PER_PAGE, total_cat)
            page_games = cat_games[start:end]
            
            page_data = {
                "page": page,
                "total": total_cat,
                "pages": cat_pages,
                "games": []
            }
            
            for g in page_games:
                slug, name, cid, hash_id = g
                video_url = videos.get(hash_id, '')
                page_data["games"].append({
                    "id": hash_id,
                    "name": name,
                    "slug": slug,
                    "category": cid,
                    "categoryName": cat_name_lookup.get(cid, "Uncategorized"),
                    "tags": [],
                    "tagNames": [],
                    "width": 800,
                    "height": 600,
                    "mobile": False,
                    "plays": 0,
                    "rating": 0,
                    "description": "",
                    "instructions": "",
                    "gameUrl": f"https://html5.gamemonetize.co/{hash_id}/",
                    "imageUrl": f"https://img.gamemonetize.com/{hash_id}/512x384.jpg",
                    "videoUrl": video_url
                })
            
            out_path = os.path.join(cat_page_dir, f'{page}.json')
            with open(out_path, 'w') as f:
                json.dump(page_data, f, separators=(',', ':'))
        
        print(f'  ✓ Category "{cat_slug}": {total_cat} games, {cat_pages} pages')
    
    return total_pages


def save_data(games_full, games_min, videos, sdk_cats, api_cats, cat_counts):
    """Save all generated data files."""
    print('[6/7] Saving data files...')
    
    os.makedirs(SDK_DATA_DIR, exist_ok=True)
    os.makedirs(API_DATA_DIR, exist_ok=True)
    
    # SDK data files
    # games.json — [slug, name, catId, hash]
    with open(os.path.join(SDK_DATA_DIR, 'games.json'), 'w') as f:
        json.dump(games_full, f, separators=(',', ':'))
    print(f'  ✓ games.json: {len(games_full)} games')
    
    # games.min.json — [slug, name, catId, hash, videoUrl]
    with open(os.path.join(SDK_DATA_DIR, 'games.min.json'), 'w') as f:
        json.dump(games_min, f, separators=(',', ':'))
    games_min_size = os.path.getsize(os.path.join(SDK_DATA_DIR, 'games.min.json'))
    print(f'  ✓ games.min.json: {len(games_min)} games ({games_min_size/1024:.0f} KB)')
    
    # videos.json — hash → videoUrl
    with open(os.path.join(SDK_DATA_DIR, 'videos.json'), 'w') as f:
        json.dump(videos, f, separators=(',', ':'))
    print(f'  ✓ videos.json: {len(videos)} entries')
    
    # SDK categories.json — {id: {s, n}}
    with open(os.path.join(SDK_DATA_DIR, 'categories.json'), 'w') as f:
        json.dump(sdk_cats, f, separators=(',', ':'))
    print(f'  ✓ sdk/categories.json: {len(sdk_cats)} categories')
    
    # API categories.json — full format
    with open(os.path.join(API_DATA_DIR, 'categories.json'), 'w') as f:
        json.dump(api_cats, f, indent=2)
    print(f'  ✓ data/categories.json: {len(api_cats["categories"])} categories')
    
    # API index.json
    total_tags = 513  # We don't recalculate tags from the feed
    total_pages = (len(games_full) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE
    index_data = {
        "version": "1.0",
        "totalGames": len(games_full),
        "totalCategories": len(sdk_cats),
        "totalTags": total_tags,
        "gamesPerPage": GAMES_PER_PAGE,
        "totalPages": total_pages
    }
    with open(os.path.join(API_DATA_DIR, 'index.json'), 'w') as f:
        json.dump(index_data, f, indent=2)
    print(f'  ✓ data/index.json: {len(games_full)} total games, {total_pages} pages')
    
    # Category-specific SDK data files (cat_N.json)
    games_by_cat = defaultdict(list)
    for g in games_min:
        games_by_cat[g[2]].append(g)
    
    for cat_id, cat_games in games_by_cat.items():
        cat_path = os.path.join(SDK_DATA_DIR, f'cat_{cat_id}.json')
        with open(cat_path, 'w') as f:
            json.dump(cat_games, f, separators=(',', ':'))
    
    print(f'  ✓ Generated {len(games_by_cat)} category files (cat_N.json)')


def main():
    args = set(sys.argv[1:])
    dry_run = '--dry-run' in args
    skip_fetch = '--skip-fetch' in args
    with_pages = '--with-pages' in args
    
    print('╔══════════════════════════════════════════════════════════╗')
    print('║     Retrograde Game Integration Pipeline                  ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print()
    
    if dry_run:
        print('  ⚠ DRY RUN — no files will be written\n')
    
    start_time = time.time()
    
    # Step 1: Fetch latest feed
    if skip_fetch:
        # Try to use a cached feed file
        cache_path = os.path.join(SDK_DATA_DIR, '_feed_cache.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                feed_data = json.load(f)
            print(f'[1/7] Using cached feed: {len(feed_data)} games')
        else:
            print('[1/7] No cached feed found, fetching...')
            feed_data = fetch_feed()
    else:
        feed_data = fetch_feed()
    
    if not feed_data:
        print('✗ No feed data available. Exiting.')
        sys.exit(1)
    
    # Cache the feed for reuse
    if not dry_run:
        cache_path = os.path.join(SDK_DATA_DIR, '_feed_cache.json')
        with open(cache_path, 'w') as f:
            json.dump(feed_data, f, separators=(',', ':'))
    
    # Step 2: Load existing data
    existing_videos, existing_slugs, existing_hash_to_slug, existing_full = load_existing_data()
    
    # Step 3: Process feed data
    games_full, games_min, videos, cat_counts = process_feed(
        feed_data, existing_videos, existing_slugs, existing_hash_to_slug, existing_full
    )
    
    # Step 4: Generate category data
    sdk_cats, api_cats = generate_category_data(cat_counts)
    
    # Step 5: Generate paginated API data (optional, can be slow)
    if with_pages and not dry_run:
        generate_page_data(games_full, videos, cat_counts)
    else:
        print('[5/7] Skipping paginated API data (use --with-pages to generate)')
    
    # Step 6: Save all data files
    if not dry_run:
        save_data(games_full, games_min, videos, sdk_cats, api_cats, cat_counts)
    else:
        print('[6/7] DRY RUN — skipping file saves')
        print(f'  Would save: {len(games_full)} games, {len(videos)} videos, {len(sdk_cats)} categories')
    
    # Summary
    elapsed = time.time() - start_time
    print(f'\n[7/7] ✓ Pipeline complete in {elapsed:.1f}s')
    print(f'  Total games: {len(games_full)}')
    print(f'  Games with video: {len(videos)} ({len(videos)*100//len(games_full)}%)')
    print(f'  Categories: {len(sdk_cats)}')
    print()
    
    if len(games_full) >= 33000:
        print('  🎯 TARGET MET: 33k+ games integrated!')
    else:
        print(f'  ⚠ Below 33k target: {33000 - len(games_full)} more games needed')
    
    # Next step hint
    print('\n  Next steps:')
    print('    1. Run: cd sdk && node build.js')
    print('    2. Test: open sdk/test.html')
    print('    3. Push data to CDN: git add data/ sdk/data/ && git commit && git push')


if __name__ == '__main__':
    main()
