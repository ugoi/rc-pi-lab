// One disposable browser process. CDP is carried only over its private pipes.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';

export function launchOwnedBrowser(onEvent) {
  if (process.env.M3_BROWSER_TARGET)
    throw Error('M3_BROWSER_TARGET is retired: shared/external targets are forbidden');
  const executable = process.env.M3_BROWSER_EXECUTABLE;
  const expected = process.env.M3_BROWSER_SHA256;
  if (!executable || !path.isAbsolute(executable) || !/^[a-f0-9]{64}$/.test(expected || ''))
    throw Error('Set absolute M3_BROWSER_EXECUTABLE and its pinned M3_BROWSER_SHA256');
  const sha256 = createHash('sha256').update(fs.readFileSync(executable)).digest('hex');
  if (sha256 !== expected) throw Error('browser executable SHA256 mismatch');
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'm3-browser-'));
  const args = ['--headless=new', '--no-sandbox', '--disable-gpu',
    '--disable-background-networking', '--disable-component-update',
    '--disable-default-apps', '--disable-extensions', '--no-first-run',
    '--no-default-browser-check', '--remote-debugging-pipe',
    '--window-size=1280,900', `--user-data-dir=${profile}`, 'about:blank'];
  const child = spawn(executable, args, {
    detached: true, stdio: ['ignore', 'ignore', 'inherit', 'pipe', 'pipe'],
  });
  const info = {transport: 'owned-process-pipe', browserPid: child.pid,
    executable, sha256, profile, nodeVersion: process.version, startedAt: new Date().toISOString()};
  let id = 0, buffer = '', dead = null, cleaning = null;
  const pending = new Map();
  function fail(error) {
    dead = error;
    for (const p of pending.values()) { clearTimeout(p.timer); p.reject(error); }
    pending.clear();
  }
  child.on('error', fail);
  child.on('exit', (code, signal) => {
    info.exitCode = code; info.exitSignal = signal;
    fail(Error(`owned browser exited: code=${code}, signal=${signal}`));
  });
  child.stdio[3].on('error', fail);
  child.stdio[4].on('error', fail);
  child.stdio[4].setEncoding('utf8');
  child.stdio[4].on('data', chunk => {
    buffer += chunk;
    let end;
    while ((end = buffer.indexOf('\0')) !== -1) {
      const frame = buffer.slice(0, end); buffer = buffer.slice(end + 1);
      if (!frame) continue;
      let message;
      try { message = JSON.parse(frame); } catch (error) { fail(error); continue; }
      if (message.id && pending.has(message.id)) {
        const p = pending.get(message.id); pending.delete(message.id); clearTimeout(p.timer);
        message.error ? p.reject(Error(JSON.stringify(message.error))) : p.resolve(message.result);
      } else if (message.method) {
        try { onEvent(message); } catch (error) { fail(error); }
      }
    }
  });
  function rpc(method, params = {}, sessionId) {
    if (dead) return Promise.reject(dead);
    return new Promise((resolve, reject) => {
      const key = ++id;
      const timer = setTimeout(() => { pending.delete(key); reject(Error('CDP timeout ' + method)); }, 7000);
      pending.set(key, {resolve, reject, timer});
      child.stdio[3].write(JSON.stringify({id: key, method, params, sessionId}) + '\0');
    });
  }
  function livingGroup() {
    if (!child.pid) return [];
    return fs.readdirSync('/proc').filter(n => /^\d+$/.test(n)).filter(n => {
      try {
        const stat = fs.readFileSync(`/proc/${n}/stat`, 'utf8').split(') ').at(-1).split(' ');
        return stat[0] !== 'Z' && Number(stat[2]) === child.pid;
      } catch { return false; }
    }).map(Number);
  }
  async function waitEmpty(ms) {
    const deadline = Date.now() + ms;
    while (livingGroup().length && Date.now() < deadline)
      await new Promise(resolve => setTimeout(resolve, 25));
  }
  function signalGroup(signal) {
    if (!child.pid) return;
    try { process.kill(-child.pid, signal); } catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
  function cleanup(reason) {
    if (cleaning) return cleaning;
    cleaning = (async () => {
      info.closeReason = reason;
      if (!dead) await Promise.race([rpc('Browser.close').catch(() => {}), new Promise(r => setTimeout(r, 1000))]);
      child.stdio[3].destroy();
      await waitEmpty(1500);
      if (livingGroup().length) { signalGroup('SIGTERM'); await waitEmpty(1500); }
      if (livingGroup().length) { signalGroup('SIGKILL'); await waitEmpty(1500); }
      fail(Error('owned browser closed'));
      child.stdio[4].destroy();
      info.remainingPids = livingGroup();
      if (!info.remainingPids.length) fs.rmSync(profile, {recursive: true, force: true});
      info.profileRemoved = !fs.existsSync(profile);
      info.finishedAt = new Date().toISOString();
      const evidence = process.env.M3_BROWSER_EVIDENCE;
      if (evidence) fs.writeFileSync(evidence, JSON.stringify(info, null, 2));
      if (info.remainingPids.length) throw Error('owned browser process cleanup failed');
      return info;
    })();
    return cleaning;
  }
  return {rpc, cleanup, info};
}
