#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { minify } = require('terser');

const SRC = path.join(__dirname, 'retro.js');
const OUT = path.join(__dirname, 'retro.min.js');

function xorEncrypt(str, key) {
  const keyBytes = [];
  for (let i = 0; i < key.length; i++) keyBytes.push(key.charCodeAt(i));
  const enc = [];
  for (let i = 0; i < str.length; i++) {
    enc.push(str.charCodeAt(i) ^ keyBytes[i % keyBytes.length] ^ ((i * 7) & 255));
  }
  return enc;
}

async function build() {
  console.log('[1/6] Reading source...');
  const source = fs.readFileSync(SRC, 'utf8');
  console.log('  Source:', source.length, 'bytes');

  console.log('[2/6] XOR-encrypting URLs...');
  let processed = encryptUrls(source);

  console.log('[3/6] Minifying with terser...');
  const result = await minify(processed, {
    compress: { sequences: true, properties: false, dead_code: true, drop_debugger: false, conditionals: true, evaluate: true, booleans: true, loops: true, unused: true, hoist_funs: true, hoist_vars: false, if_return: true, join_vars: true, collapse_vars: true, reduce_vars: true, side_effects: true, switches: true, typeofs: true },
    mangle: { toplevel: true, eval: true, keep_classnames: false, keep_fnames: false, properties: false, reserved: ['RetroArcade'] },
    format: { comments: false, preserve_annotations: false },
    toplevel: true,
  });

  if (result.error) { console.error('Terser error:', result.error); process.exit(1); }
  let output = result.code;
  console.log('  Minified:', output.length, 'bytes');

  console.log('[4/6] Injecting dead code...');
  output = injectDeadCode(output);

  console.log('[5/6] Injecting control flow traps...');
  output = injectControlFlowTraps(output);

  console.log('[6/6] Adding protection wrapper...');
  output = wrapMultiLayer(output);

  fs.writeFileSync(OUT, output, 'utf8');
  console.log('\nDone!', OUT);
  console.log('  Final size:', (Buffer.byteLength(output, 'utf8') / 1024).toFixed(1), 'KB');
}

function encryptUrls(code) {
  const key = generateKey();
  const keyArray = key.split('').map(c => c.charCodeAt(0));

  const urls = {
    CATALOG: 'https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/games.min.json',
    CATEGORIES: 'https://cdn.jsdelivr.net/gh/retrograde-sdk/sdk@main/data/categories.json',
    GAME_CDN: 'https://retro-arcade-proxy.challengerdeep.workers.dev/game/',
    IMG_CDN: 'https://retro-arcade-proxy.challengerdeep.workers.dev/img/',
    ALT1: 'https://raw.githubusercontent.com/retrograde-sdk/sdk/main/data/games.min.json',
    ALT2: 'https://raw.githubusercontent.com/retrograde-sdk/sdk/main/data/categories.json',
  };

  for (const [name, url] of Object.entries(urls)) {
    const enc = xorEncrypt(url, key);
    const encStr = '[' + enc.join(',') + ']';
    code = code.replace("'__ENCRYPTED_" + name + "__'", encStr);
  }

  code = code.replace('[__KEY_ARRAY__]', '[' + keyArray.join(',') + ']');
  return code;
}

function generateKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let key = '';
  for (let i = 0; i < 16; i++) key += chars.charAt(Math.floor(Math.random() * chars.length));
  return key;
}

function injectDeadCode(code) {
  const d = Array.from({length: 14}, () => rnd());
  const blocks = [
    'if(false){var _0x' + d[0] + '=function(){fetch(String.fromCharCode(104,116,116,112,115,58,47,47,49,50,55,46,48,46,48,46,49,47,97,112,105)).then(function(){}).catch(function(){});};_0x' + d[0] + '();}',
    'if(typeof _0x' + d[1] + "==='undefined'){var _0x" + d[2] + '=new(function(){this.connect=function(){};this.disconnect=function(){};})();}',
    'if(typeof window!==' + "'undefined'&&window._0x" + d[3] + '){console.log(String.fromCharCode(68,101,98,117,103));}',
    'var _0x' + d[4] + '=setInterval(function(){clearInterval(_0x' + d[4] + ');},999999);',
    'if(false){document.addEventListener(String.fromCharCode(109,111,117,115,101,111,118,101,114),function(){});}',
    'var _0x' + d[5] + '=false;if(_0x' + d[5] + '&&!_0x' + d[5] + '){localStorage.removeItem(String.fromCharCode(116,101,109,112));}',
    'var _0x' + d[6] + '=performance.now();if(_0x' + d[6] + '>1e12){var _0x' + d[7] + '=null;}',
  ];

  const cssEndMarker = "innerHTML:'";
  const cssStartIdx = code.lastIndexOf(cssEndMarker + '.ra-root{');
  let safeStart = 0;
  if (cssStartIdx !== -1) {
    const lastMedia = '@media(min-width:900px)';
    const mediaIdx = code.indexOf(lastMedia, cssStartIdx);
    if (mediaIdx !== -1) {
      const closing = code.indexOf("}'", mediaIdx);
      if (closing !== -1) safeStart = closing + 2;
    }
  }
  if (safeStart === 0) safeStart = Math.floor(code.length * 0.6);

  let result = code;
  let offset = 0;
  const step = Math.floor((code.length - safeStart) / 10);
  let pos = code.indexOf(';', safeStart);
  for (let i = 0; i < blocks.length && pos !== -1; i++) {
    const insertAt = pos + 1 + offset;
    result = result.substring(0, insertAt) + blocks[i] + result.substring(insertAt);
    offset += blocks[i].length;
    pos = code.indexOf(';', pos + Math.max(step, 200));
  }
  return result;
}

function injectControlFlowTraps(code) {
  const d = Array.from({length: 4}, () => rnd());
  const trap = 'var _0x' + d[0] + '=function(){var _0x' + d[1] + '={};try{Object.defineProperty(_0x' + d[1] + ",'_0x" + d[2] + "',{get:function(){debugger;}});_0x" + d[1] + '._0x' + d[2] + ';}catch(e){}};setInterval(function(){try{_0x' + d[0] + '();}catch(e){}},45000);';
  const integrity = 'var _0x' + d[3] + '=' + simpleHash(code) + ';';
  return trap + integrity + code;
}

function wrapMultiLayer(code) {
  const d = Array.from({length: 10}, () => rnd());
  const antiDebug = 'var _0x' + d[0] + '=function(){var _0x' + d[1] + '=performance.now();debugger;if(performance.now()-_0x' + d[1] + '>50){while(true){}}};';
  const devtoolsDetect = 'var _0x' + d[2] + '=function(){var _0x' + d[3] + "=new Image();Object.defineProperty(_0x" + d[3] + ",'id',{get:function(){_0x" + d[0] + '();}});console.log(_0x' + d[3] + ');};';
  const consoleDetect = 'var _0x' + d[4] + '=function(){var _0x' + d[5] + '=new Date();console.log(_0x' + d[5] + ');console.clear();if(new Date()-_0x' + d[5] + '>100){_0x' + d[0] + '();}};';
  const hash = simpleHash(code);
  const integrity = 'var _0x' + d[6] + '=' + hash + ';';
  const i1 = 15000 + Math.floor(Math.random() * 30000);
  const i2 = 20000 + Math.floor(Math.random() * 40000);
  const i3 = 30000 + Math.floor(Math.random() * 60000);
  const periodic = 'setInterval(function(){try{_0x' + d[0] + '();}catch(_0x' + d[7] + '){}},' + i1 + ');setInterval(function(){try{_0x' + d[2] + '();}catch(_0x' + d[8] + '){}},' + i2 + ');setInterval(function(){try{_0x' + d[4] + '();}catch(_0x' + d[9] + '){}},' + i3 + ');';
  const selfDefend = "(function(){var _0xf=Function.prototype.toString;var _0x" + d[0] + "o=rnd;Function.prototype.toString=function(){return typeof this==='_0xf'||this===_0x" + d[0] + "o?'function(){}':_0xf.call(this);};})();";

  return '(function(){' + antiDebug + devtoolsDetect + consoleDetect + integrity + periodic + 'try{' + selfDefend + '}catch(e){}' + code + '})();';
}

function rnd() { return Math.random().toString(16).substring(2, 8); }
function simpleHash(str) { let h = 0; for (let i = 0; i < str.length; i++) { h = ((h << 5) - h) + str.charCodeAt(i); h = h & h; } return Math.abs(h); }

build().catch(err => { console.error('Build failed:', err); process.exit(1); });
