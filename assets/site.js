(() => {
  'use strict';

  const KEY = 're-theme';
  const palettes = {
    graphite:{accent:'#c9a86a',accent2:'#e7d4a7',accentRgb:'201,168,106'},
    sand:{accent:'#b77b57',accent2:'#e3b49b',accentRgb:'183,123,87'},
    sage:{accent:'#8aa68a',accent2:'#c2d4bf',accentRgb:'138,166,138'},
    plum:{accent:'#a58aa8',accent2:'#d2bfd5',accentRgb:'165,138,168'},
    copper:{accent:'#c2875a',accent2:'#e2b894',accentRgb:'194,135,90'},
    mono:{accent:'#b8bec7',accent2:'#eef0f2',accentRgb:'184,190,199'}
  };
  const names={graphite:'Graphite',sand:'Terracotta',sage:'Sage',plum:'Plum',copper:'Copper',mono:'Monochrome'};
  const root=document.documentElement;

  function readState(){
    try{
      const raw=localStorage.getItem(KEY);
      if(!raw) return {};
      const parsed=JSON.parse(raw);
      return parsed && typeof parsed==='object' ? parsed : {};
    }catch(_){ return {}; }
  }
  const saved=readState();

  function persist(){
    try{localStorage.setItem(KEY,JSON.stringify(saved));}catch(_){}
  }

  function apply(){
    const palette=palettes[saved.palette] ? saved.palette : 'graphite';
    const mode=saved.mode==='light'||saved.mode==='dark'
      ? saved.mode
      : (matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');
    root.dataset.theme=mode;
    root.dataset.palette=palette;
    root.dataset.motion=saved.motion===false?'off':'on';
    const p=palettes[palette];
    root.style.setProperty('--accent',p.accent);
    root.style.setProperty('--accent2',p.accent2);
    root.style.setProperty('--accent-rgb',p.accentRgb);
    persist();
  }
  apply();

  const style=document.createElement('style');
  style.textContent=`
    .re-tools{position:fixed;right:18px;bottom:18px;z-index:10000;display:flex;gap:8px}
    .re-tool{width:44px;height:44px;border:1px solid var(--line);border-radius:50%;background:var(--panel);color:var(--text);display:grid;place-items:center;cursor:pointer;box-shadow:0 12px 35px rgba(0,0,0,.18);font-size:18px}
    .re-tool:hover{transform:translateY(-2px);border-color:var(--accent)}
    .re-panel{position:fixed;right:18px;bottom:72px;z-index:9999;width:min(350px,calc(100vw - 36px));padding:18px;border:1px solid var(--line);border-radius:18px;background:var(--panel);color:var(--text);box-shadow:0 25px 70px rgba(0,0,0,.28);display:none}
    .re-panel.open{display:block}.re-panel h3{margin:0 0 5px}.re-panel p{margin:0 0 15px;color:var(--muted);font-size:12px}
    .re-palette{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
    .re-palette button,.re-modes button,.re-option{border:1px solid var(--line);background:var(--panel2);color:var(--text);padding:10px;border-radius:10px;cursor:pointer;font:inherit}
    .re-palette button:hover,.re-modes button:hover,.re-option:hover{border-color:var(--accent)}
    .re-palette button span{display:block;width:20px;height:20px;border-radius:50%;margin:0 auto 5px;background:var(--swatch)}
    .re-modes{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
    .re-contact{margin-top:35px;padding:22px;border:1px solid var(--line);border-radius:17px;background:linear-gradient(145deg,var(--panel2),var(--panel))}
    .re-contact-grid{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}.re-contact a{display:inline-flex;align-items:center;gap:7px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
    .re-progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent);z-index:20000}
    .re-top{position:fixed;left:18px;bottom:18px;z-index:10000;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);opacity:0;pointer-events:none;transition:.2s}.re-top.show{opacity:1;pointer-events:auto}
    [data-motion="off"] *{scroll-behavior:auto!important;animation:none!important;transition:none!important}
    @media(max-width:640px){.re-tools{right:12px;bottom:12px}.re-top{left:12px;bottom:12px}}
  `;
  document.head.appendChild(style);

  function moon(){return root.dataset.theme==='dark'?'☼':'☾';}
  const tools=document.createElement('div');
  tools.className='re-tools';
  tools.innerHTML='<button type="button" class="re-tool" id="re-theme" aria-label="Toggle light and dark mode">'+moon()+'</button><button type="button" class="re-tool" id="re-custom" aria-label="Customize appearance" aria-expanded="false">✦</button>';
  document.body.appendChild(tools);

  const panel=document.createElement('div');
  panel.className='re-panel';
  panel.id='re-panel';
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-label','Appearance settings');
  panel.setAttribute('aria-hidden','true');
  panel.innerHTML='<h3>Appearance</h3><p>Choose your mode, accent and motion preference. Settings are saved on this device.</p><div class="re-modes"><button type="button" data-mode="light">☀ Light</button><button type="button" data-mode="dark">☾ Dark</button></div><div class="re-palette">'+Object.entries(palettes).map(([k,v])=>'<button type="button" data-palette="'+k+'"><span style="--swatch:'+v.accent+'"></span>'+names[k]+'</button>').join('')+'</div><button type="button" class="re-option" id="re-motion" style="width:100%;margin-top:10px">Reduce motion</button>';
  document.body.appendChild(panel);

  const custom=document.getElementById('re-custom');
  function setPanel(open){
    panel.classList.toggle('open',open);
    panel.setAttribute('aria-hidden',String(!open));
    custom.setAttribute('aria-expanded',String(open));
  }
  custom.addEventListener('click',e=>{e.stopPropagation();setPanel(!panel.classList.contains('open'));});
  panel.addEventListener('click',e=>e.stopPropagation());
  document.addEventListener('click',()=>setPanel(false));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setPanel(false);});

  document.getElementById('re-theme').addEventListener('click',()=>{
    saved.mode=root.dataset.theme==='dark'?'light':'dark'; apply();
    document.getElementById('re-theme').textContent=moon();
  });
  panel.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{
    saved.mode=b.dataset.mode;apply();document.getElementById('re-theme').textContent=moon();
  }));
  panel.querySelectorAll('[data-palette]').forEach(b=>b.addEventListener('click',()=>{
    saved.palette=b.dataset.palette;apply();
  }));
  document.getElementById('re-motion').addEventListener('click',()=>{
    saved.motion=saved.motion===false?true:false;apply();
  });

  const progress=document.createElement('div');progress.className='re-progress';document.body.appendChild(progress);
  const top=document.createElement('button');top.type='button';top.className='re-top';top.textContent='↑';top.setAttribute('aria-label','Back to top');document.body.appendChild(top);
  addEventListener('scroll',()=>{const h=document.documentElement.scrollHeight-innerHeight;progress.style.width=(h>0?(scrollY/h)*100:0)+'%';top.classList.toggle('show',scrollY>500)},{passive:true});
  top.addEventListener('click',()=>scrollTo({top:0,behavior:root.dataset.motion==='off'?'auto':'smooth'}));

  const footer=document.querySelector('.footer .w');
  if(footer&&!document.querySelector('.re-contact')){
    const c=document.createElement('div');c.className='re-contact';
    c.innerHTML='<div class="ey">Contact & acquisition</div><h3>Interested in Robot Embodiment?</h3><p class="muted">For acquisition, partnerships, licensing or project inquiries, contact us directly.</p><div class="re-contact-grid"><a href="mailto:Domainzax@gmail.com">✉ Domainzax@gmail.com</a><a href="https://wa.me/573196552559" target="_blank" rel="noopener">◉ WhatsApp · +57 319 655 2559</a></div>';
    footer.parentNode.insertBefore(c,footer);
  }
  // SEO: add a lightweight breadcrumb graph for pages that do not already provide one.
  if(!document.querySelector('script[data-re-breadcrumb]')){
    const path=location.pathname.replace(/\\/$/,'').split('/').filter(Boolean);
    const items=[{name:'Robot Embodiment',item:'https://robotembodiment.com/'}];
    if(path.length){
      let acc='https://robotembodiment.com/';
      path.forEach((part,i)=>{
        acc+=part+(i===path.length-1?'':'/');
        const label=document.title.split('|')[0].trim()||part.replace(/[-_]/g,' ');
        items.push({name:i===path.length-1?label:part.replace(/[-_]/g,' '),item:acc});
      });
    }
    const s=document.createElement('script');
    s.type='application/ld+json';s.dataset.reBreadcrumb='true';
    s.textContent=JSON.stringify({'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:items.map((x,i)=>({'@type':'ListItem',position:i+1,name:x.name,item:x.item}))});
    document.head.appendChild(s);
  }

  root.dataset.reReady='true';
})();