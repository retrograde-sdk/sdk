#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { minify } = require('terser');

const SRC = path.join(__dirname, 'retro.js');
const OUT = path.join(__dirname, 'retro.min.js');

async function build() {
  console.log('[1/5] Reading source...');
  const source = fs.readFileSync(SRC, 'utf8');
  console.log(`  Source: ${source.length} bytes`);

  console.log('[2/5] Encoding sensitive strings...');
  let processed = encodeSensitiveStrings(source);

  console.log('[3/5] Minifying with terser...');
  const result = await minify(processed, {
    compress: {
      sequences: true,
      properties: false,
      dead_code: true,
      drop_debugger: false,
      conditionals: true,
      evaluate: true,
      booleans: true,
      loops: true,
      unused: true,
      hoist_funs: true,
      hoist_vars: false,
      if_return: true,
      join_vars: true,
      collapse_vars: true,
      reduce_vars: true,
      side_effects: true,
      switches: true,
      typeofs: true,
    },
    mangle: {
      toplevel: true,
      eval: true,
      keep_classnames: false,
      keep_fnames: false,
      properties: false,
      reserved: ['RetroArcade']
    },
    format: {
      comments: false,
      preserve_annotations: false,
    },
    toplevel: true,
  });

  if (result.error) {
    console.error('Terser error:', result.error);
    process.exit(1);
  }

  let output = result.code;
  console.log(`  Minified: ${output.length} bytes`);

  console.log('[4/5] Injecting dead code...');
  output = injectDeadCode(output);

  console.log('[5/5] Adding multi-layer protection wrapper...');
  output = wrapMultiLayer(output);

  fs.writeFileSync(OUT, output, 'utf8');
  const finalSize = Buffer.byteLength(output, 'utf8');
  console.log(`\nDone! ${OUT}`);
  console.log(`  Final size: ${(finalSize / 1024).toFixed(1)} KB`);
}

// --- Layer 1: Encode sensitive strings with String.fromCharCode ---
function toCharCodes(s) {
  return `String.fromCharCode(${Array.from(s).map(c => c.charCodeAt(0)).join(',')})`;
}

function encodeSensitiveStrings(code) {
  const sensitiveStrings = [
    'https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/games.min.json',
    'https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/categories.json',
    'https://raw.githubusercontent.com/retrograde-sdk/sdk/main/data/games.min.json',
    'https://raw.githubusercontent.com/retrograde-sdk/sdk/main/data/categories.json',
    'https://retro-arcade-proxy.challengerdeep.workers.dev/game/',
    'https://retro-arcade-proxy.challengerdeep.workers.dev/img/',
    'retroarcade_',
  ];

  for (const str of sensitiveStrings) {
    const encoded = toCharCodes(str);
    const escaped = str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    code = code.replace(new RegExp(`'${escaped}'`, 'g'), encoded);
    code = code.replace(new RegExp(`"${escaped}"`, 'g'), encoded);
  }

  return code;
}

function injectDeadCode(code) {
  const d1 = rnd(), d2 = rnd(), d3 = rnd(), d4 = rnd();
  const d5 = rnd(), d6 = rnd(), d7 = rnd(), d8 = rnd();

  const deadCodeBlocks = [
    `if(false){var _0x${d1}=function(){fetch(String.fromCharCode(104,116,116,112,115,58,47,47,49,50,55,46,48,46,48,46,49,47,97,112,105)).then(function(){}).catch(function(){});};_0x${d1}();}`,
    `if(typeof _0x${d2}==='undefined'){var _0x${d3}=new(function(){this.connect=function(){};this.disconnect=function(){};})();}`,
    `if(typeof window!=='undefined'&&window._0x${d4}){console.log(String.fromCharCode(68,101,98,117,103));}`,
    `var _0x${d5}=setInterval(function(){clearInterval(_0x${d5});},999999);`,
    `if(false){document.addEventListener(String.fromCharCode(109,111,117,115,101,111,118,101,114),function(){});}`,
    `var _0x${d6}=false;if(_0x${d6}&&!_0x${d6}){localStorage.removeItem(String.fromCharCode(116,101,109,112));}`,
    `var _0x${d7}=performance.now();if(_0x${d7}>1e12){var _0x${d8}=null;}`,
  ];

  // Find the CSS string boundary - CSS is inside innerHTML:'...'
  // We need to find where the CSS ends and only inject AFTER that
  const cssEndMarker = "innerHTML:'";
  const cssStartIdx = code.lastIndexOf(cssEndMarker + '.ra-root{');
  let safeStart = 0;
  if (cssStartIdx !== -1) {
    // Find the closing quote of the CSS string
    // The CSS is the longest string in innerHTML - find the matching closing quote
    let depth = 0;
    let cssEnd = cssStartIdx + cssEndMarker.length;
    // The CSS string ends with }' - find the quote after the last }
    const lastMediaQuery = '@media(min-width:900px)';
    const mediaIdx = code.indexOf(lastMediaQuery, cssEnd);
    if (mediaIdx !== -1) {
      // Find the closing } and quote after it
      const closingBrace = code.indexOf("}'", mediaIdx);
      if (closingBrace !== -1) {
        safeStart = closingBrace + 2; // skip past }'
      }
    }
  }

  if (safeStart === 0) {
    // Fallback: skip first 60% of code (CSS is roughly in the middle)
    safeStart = Math.floor(code.length * 0.6);
  }

  const insertPoints = [];
  let pos = code.indexOf(';', safeStart);
  const step = Math.floor((code.length - safeStart) / 10);
  while (pos !== -1 && pos < code.length * 0.92 && insertPoints.length < deadCodeBlocks.length) {
    insertPoints.push(pos + 1);
    const nextPos = code.indexOf(';', pos + Math.max(step, 200));
    if (nextPos === pos) break;
    pos = nextPos;
  }

  let result = code;
  let offset = 0;
  for (let i = 0; i < deadCodeBlocks.length && i < insertPoints.length; i++) {
    const insertAt = insertPoints[i] + offset;
    result = result.substring(0, insertAt) + deadCodeBlocks[i] + result.substring(insertAt);
    offset += deadCodeBlocks[i].length;
  }

  return result;
}

// --- Layer 4: Multi-layer protection wrapper ---
function wrapMultiLayer(code) {
  const d1 = rnd(), d2 = rnd(), d3 = rnd(), d4 = rnd(), d5 = rnd();
  const d6 = rnd(), d7 = rnd(), d8 = rnd(), d9 = rnd(), d10 = rnd();

  // Anti-debug: debugger trap + timing check
  const antiDebug = `var _0x${d1}=function(){var _0x${d2}=performance.now();debugger;if(performance.now()-_0x${d2}>50){while(true){}}};`;

  // Anti-debug: DevTools detection via toString
  const devtoolsDetect = `var _0x${d3}=function(){var _0x${d4}=new Image();Object.defineProperty(_0x${d4},'id',{get:function(){_0x${d1}();}});console.log(_0x${d4});};`;

  // Anti-debug: Console detection
  const consoleDetect = `var _0x${d5}=function(){var _0x${d6}=new Date();console.log(_0x${d6});console.clear();if(new Date()-_0x${d6}>100){_0x${d1}();}};`;

  // Integrity check: hash verification
  const hash = simpleHash(code);
  const integrityCheck = `var _0x${d7}=${hash};`;

  // Periodic anti-debug (every 15-45 seconds, random)
  const interval1 = 15000 + Math.floor(Math.random() * 30000);
  const interval2 = 20000 + Math.floor(Math.random() * 40000);
  const interval3 = 30000 + Math.floor(Math.random() * 60000);

  const periodicChecks = `setInterval(function(){try{_0x${d1}();}catch(_0x${d8}){}},${interval1});setInterval(function(){try{_0x${d3}();}catch(_0x${d9}){}},${interval2});setInterval(function(){try{_0x${d5}();}catch(_0x${d10}){}},${interval3});`;

  // Self-defending: prevent toString/function inspection
  const selfDefending = `(function(){var _0xf=Function.prototype.toString;var _0x${d1}o=rnd;Function.prototype.toString=function(){return typeof this==='_0xf'||this===_0x${d1}o?'function(){}':_0xf.call(this);};})();`;

  // Assemble wrapper
  return `(function(){` +
    antiDebug +
    devtoolsDetect +
    consoleDetect +
    integrityCheck +
    periodicChecks +
    `try{` + selfDefending + `}catch(e){}` +
    code +
  `})();`;
}

// --- Utilities ---
function rnd() {
  return Math.random().toString(16).substring(2, 8);
}

function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return Math.abs(hash);
}

build().catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
