// TechPulse: server-side GitHub Actions dispatch proxy (Cloudflare Worker).
// Secrets: GITHUB_TOKEN; KV binding: COOLDOWN. Public requests are throttled globally.
const ORIGIN='https://nico91630.github.io';
const WORKFLOW='https://api.github.com/repos/nico91630/Techpulse/actions/workflows/actualites.yml/dispatches';
const cors={'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Methods':'POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type','Cache-Control':'no-store'};
function reply(data,status=200,headers={}){return new Response(JSON.stringify(data),{status,headers:{...cors,'Content-Type':'application/json',...headers}})}
export default {async fetch(request,env){const url=new URL(request.url);if(url.pathname!=='/collect')return reply({error:'Not found'},404);if(request.method==='OPTIONS')return new Response(null,{status:204,headers:cors});if(request.method!=='POST')return reply({error:'Method not allowed'},405);if(request.headers.get('Origin')!==ORIGIN)return reply({error:'Origin not allowed'},403);if(!env.GITHUB_TOKEN||!env.COOLDOWN)return reply({error:'Service not configured'},503);
// KV limits global requests (eventually consistent). For stricter protection use Durable Objects or Turnstile.
const last=Number(await env.COOLDOWN.get('last_dispatch')||0),now=Date.now();const wait=15*60*1000-(now-last);if(wait>0)return reply({status:'cooldown',retry_after_seconds:Math.ceil(wait/1000)},429,{'Retry-After':String(Math.ceil(wait/1000))});
await env.COOLDOWN.put('last_dispatch',String(now),{expirationTtl:900});
try{const response=await fetch(WORKFLOW,{method:'POST',headers:{Authorization:'Bearer '+env.GITHUB_TOKEN,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'TechPulse-Collector'},body:JSON.stringify({ref:'main'})});if(response.status!==204){await env.COOLDOWN.delete('last_dispatch');return reply({error:'GitHub dispatch failed',status:response.status},502)}return reply({status:'started',message:'Collecte lancée. Actualisation des articles après publication.'},202)}catch(error){await env.COOLDOWN.delete('last_dispatch');return reply({error:'Collection service unavailable'},502)}}};
