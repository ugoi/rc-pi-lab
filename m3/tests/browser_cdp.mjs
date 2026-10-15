// Bounded test client for its own disposable browser, never shared CDP9222.
import fs from 'node:fs';
import readline from 'node:readline';
import {spawnSync} from 'node:child_process';
import {launchOwnedBrowser} from './owned_browser.mjs';
let recording=null;
const browser=launchOwnedBrowser(m=>{
 if(m.method==='Page.screencastFrame'){
  const r=recording;
  if(r){const file=`${r.dir}/${String(r.frames.length).padStart(6,'0')}.jpg`;fs.writeFileSync(file,Buffer.from(m.params.data,'base64'));r.frames.push({file,timestamp:m.params.metadata.timestamp});}
  rpc('Page.screencastFrameAck',{sessionId:m.params.sessionId},m.sessionId).catch(()=>{});
 }
});
const rpc=browser.rpc;
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>{
 browser.cleanup(signal).then(()=>process.exit(signal==='SIGTERM'?143:130),error=>{console.error(error);process.exit(1);});
});
try {
const root=await rpc('Browser.getVersion');browser.info.browserVersion=root.product;
const ownedContext=(await rpc('Target.createBrowserContext',{disposeOnDetach:true})).browserContextId;
const target=(await rpc('Target.createTarget',{url:'about:blank',browserContextId:ownedContext})).targetId;
const {sessionId}=await rpc('Target.attachToTarget',{targetId:target,flatten:true});
const call=(method,params={})=>rpc(method,params,sessionId);
const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result?.value;};
await call('Page.enable');
async function click(sel){const p=await evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);for(const type of ['mousePressed','mouseReleased'])await call('Input.dispatchMouseEvent',{type,...p,button:'left',clickCount:1});}
async function command(a){
 if(a[0]==='tab'){if(a[1]!==target && a[1]!=='__owned__')throw Error('refusing other target');return {targetId:target,browserContextId:ownedContext,...browser.info};}
 if(a[0]==='open'){
  const address=new URL(a[1]);
  if(address.protocol!=='http:' || address.hostname!=='127.0.0.1')throw Error('test browser accepts only loopback HTTP');
  await call('Page.navigate',{url:a[1]});await call('Page.bringToFront');
  const end=Date.now()+5000;while(!await evaluate("Boolean(document.querySelector('#arm'))")){if(Date.now()>end)throw Error('UI load timeout');await new Promise(r=>setTimeout(r,50));}return {};
 }
 if(a[0]==='set') {await call('Emulation.setDeviceMetricsOverride',{width:+a[2],height:+a[3],deviceScaleFactor:1,mobile:false});return {};}
 if(a[0]==='click'||a[0]==='focus'){const end=Date.now()+3000;while(!await evaluate(`!document.querySelector(${JSON.stringify(a[1])}).disabled`)){if(Date.now()>end)throw Error('disabled control '+a[1]);await new Promise(r=>setTimeout(r,50));}await click(a[1]);return {};}
 if(a[0]==='press'){const code={End:35,Home:36,Space:32}[a[1]];if(!code)throw Error('unsupported key');for(const type of ['keyDown','keyUp'])await call('Input.dispatchKeyEvent',{type,key:a[1],code:a[1],windowsVirtualKeyCode:code});return {};}
 if(a[0]==='eval')return {result:await evaluate(a[1])};
 if(a[0]==='is'&&a[1]==='enabled')return {enabled:await evaluate(`!document.querySelector(${JSON.stringify(a[2])}).disabled`)};
 if(a[0]==='get'){const property=a[1]==='text'?'textContent':'value';return {[a[1]]:await evaluate(`document.querySelector(${JSON.stringify(a[2])})[${JSON.stringify(property)}]`)};}
 if(a[0]==='screenshot'){const r=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(a[1],Buffer.from(r.data,'base64'));return {};}
 if(a[0]==='record'&&a[1]==='start'){
  recording={output:a[2],dir:a[2]+'.frames',frames:[]};fs.mkdirSync(recording.dir,{recursive:true});await call('Page.startScreencast',{format:'jpeg',quality:65,maxWidth:1280,maxHeight:900,everyNthFrame:2});return {};
 }
 if(a[0]==='record'&&a[1]==='stop'){
  await call('Page.stopScreencast');const r=recording;recording=null;if(!r||r.frames.length<2)throw Error('no live recording frames');
  fs.writeFileSync(r.output+'.timestamps.json',JSON.stringify({client:'Chrome CDP Page.startScreencast',target,frames:r.frames},null,2));
  let list='';for(let i=0;i<r.frames.length;i++){list+=`file '${r.frames[i].file}'\n`;if(i+1<r.frames.length)list+=`duration ${Math.max(.001,r.frames[i+1].timestamp-r.frames[i].timestamp)}\n`;}
  list+=`file '${r.frames.at(-1).file}'\n`;fs.writeFileSync(r.dir+'/frames.txt',list);
  const p=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',r.dir+'/frames.txt','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2,fps=15','-c:v','libx264','-threads','1','-filter_threads','1','-pix_fmt','yuv420p',r.output],{encoding:'utf8',timeout:30000});
  if(p.status!==0)throw Error('video encode failed '+p.stderr);fs.rmSync(r.dir,{recursive:true});return {path:r.output,frames:r.frames.length};
 }
 throw Error('unsupported browser command '+a.join(' '));
}
for await(const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})){
 try {process.stdout.write(JSON.stringify({success:true,data:await command(JSON.parse(line))})+'\n');}
 catch(error){process.stdout.write(JSON.stringify({success:false,error:String(error)})+'\n');}
}
} finally { await browser.cleanup('EOF or command/startup failure'); }
