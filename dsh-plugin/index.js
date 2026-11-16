import { execFile, spawn } from 'node:child_process'
import { promisify } from 'node:util'
import { existsSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { defineTool } from '@deepseek-ai/dsh-tools'

const execFileAsync = promisify(execFile)
export const name = 'android-emulator-lab'
export const inject = ['tools']
const adbPath = process.env.ANDROID_ADB || 'adb'
const emulatorPath = process.env.ANDROID_EMULATOR || 'emulator'
const MAX_BUFFER = 8 * 1024 * 1024

async function run(bin, args, timeout = 30000) {
  try {
    const { stdout, stderr } = await execFileAsync(bin, args, { timeout, maxBuffer: MAX_BUFFER, windowsHide: true, encoding: 'utf8' })
    return { ok: true, stdout: stdout.trim(), stderr: stderr.trim() }
  } catch (error) {
    return { ok: false, error: error.message, stdout: String(error.stdout || '').trim(), stderr: String(error.stderr || '').trim(), code: error.code ?? null }
  }
}
function serialArgs(serial) {
  if (!serial || typeof serial !== 'string' || !serial.trim()) throw new Error('A target serial is required. Run android_devices and pass an explicit serial.')
  return ['-s', serial.trim()]
}
function register(ctx, { name, description, parameters, properties, execute }) {
  ctx.tools.register(defineTool({
    name, description, parameters,
    output: { schema: { type: 'object', properties: { ok: { type: 'boolean', required: true }, ...properties }, additionalProperties: false },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }] },
    async execute(args) { try { return await execute(args) } catch (error) { return { ok: false, error: error.message } } },
  }))
}
export function apply(ctx) {
  register(ctx, {
    name: 'android_doctor', description: 'Check Android SDK environment, adb/emulator availability, and connected targets.',
    parameters: {}, properties: { adb: { type: 'string' }, emulator: { type: 'string' }, devices: { type: 'string' }, advice: { type: 'string' } },
    async execute() {
      const [a, e, d] = await Promise.all([run(adbPath, ['version']), run(emulatorPath, ['-version']), run(adbPath, ['devices', '-l'])])
      return { ok: a.ok && d.ok, adb: a.stdout || a.error, emulator: e.stdout || e.error, devices: d.stdout || d.error,
        advice: a.ok ? 'ADB is callable. Use android_devices to inspect targets.' : 'Install Platform-Tools and add adb to PATH or set ANDROID_ADB.' }
    },
  })
  register(ctx, { name: 'android_devices', description: 'List attached ADB devices. Does not select a default target.', parameters: {}, properties: { devices: { type: 'string' } },
    async execute() { const r = await run(adbPath, ['devices', '-l']); return { ok: r.ok, devices: r.stdout || r.error } } })
  register(ctx, { name: 'android_avd_list', description: 'List configured Android Virtual Devices.', parameters: {}, properties: { avds: { type: 'string' } },
    async execute() { const r = await run(emulatorPath, ['-list-avds']); return { ok: r.ok, avds: r.stdout || r.error } } })
  register(ctx, { name: 'android_avd_boot', description: 'Start a named local Android Virtual Device.', parameters: { avd: { type: 'string', required: true } }, properties: { avd: { type: 'string' }, message: { type: 'string' } },
    async execute({ avd }) {
      if (!/^[A-Za-z0-9_.-]+$/.test(avd)) throw new Error('Invalid AVD name.')
      const pid = await new Promise((resolvePid, reject) => {
        const child = spawn(emulatorPath, ['-avd', avd, '-no-snapshot-save'], { detached: true, stdio: 'ignore', windowsHide: true })
        child.once('error', reject); child.once('spawn', () => { const p = child.pid; child.unref(); resolvePid(p) })
      })
      return { ok: true, avd, message: `Emulator process started (pid ${pid}). Check android_devices, then wait for boot.` }
    } })
  register(ctx, { name: 'android_wait_boot', description: 'Wait for an explicit ADB target to finish booting.', parameters: { serial: { type: 'string', required: true }, timeout_seconds: { type: 'number' } }, properties: { serial: { type: 'string' }, boot_completed: { type: 'string' }, message: { type: 'string' } },
    async execute({ serial, timeout_seconds = 120 }) {
      const s = serialArgs(serial), t = Math.max(30, Math.min(300, Number(timeout_seconds) || 120))
      const w = await run(adbPath, [...s, 'wait-for-device'], t * 1000)
      if (!w.ok) return { ok: false, serial, boot_completed: '', message: w.error }
      const r = await run(adbPath, [...s, 'shell', 'getprop', 'sys.boot_completed'], t * 1000)
      return { ok: r.ok && r.stdout === '1', serial, boot_completed: r.stdout, message: r.stdout === '1' ? 'Boot completed.' : 'Boot not yet confirmed; retry.' }
    } })
  register(ctx, { name: 'android_install_apk', description: 'Install or update an APK on an explicitly selected target.', parameters: { serial: { type: 'string', required: true }, apk_path: { type: 'string', required: true }, replace: { type: 'boolean' } }, properties: { serial: { type: 'string' }, output: { type: 'string' } },
    async execute({ serial, apk_path, replace = true }) {
      const path = resolve(apk_path); if (!existsSync(path) || !path.toLowerCase().endsWith('.apk')) throw new Error('APK path does not exist or is not an .apk file.')
      const r = await run(adbPath, [...serialArgs(serial), 'install', ...(replace ? ['-r'] : []), path], 120000)
      return { ok: r.ok, serial, output: r.stdout || r.stderr || r.error }
    } })
  register(ctx, { name: 'android_launch_app', description: 'Launch an installed Android app by package ID.', parameters: { serial: { type: 'string', required: true }, package_id: { type: 'string', required: true } }, properties: { serial: { type: 'string' }, output: { type: 'string' } },
    async execute({ serial, package_id }) {
      if (!/^[A-Za-z0-9_.]+$/.test(package_id)) throw new Error('Invalid package ID.')
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'monkey', '-p', package_id, '1'])
      return { ok: r.ok, serial, output: r.stdout || r.stderr || r.error }
    } })
  register(ctx, { name: 'android_screenshot', description: 'Capture a screenshot from an explicit Android target.', parameters: { serial: { type: 'string', required: true }, output_path: { type: 'string', required: true } }, properties: { serial: { type: 'string' }, output_path: { type: 'string' }, message: { type: 'string' } },
    async execute({ serial, output_path }) {
      const path = resolve(output_path); mkdirSync(dirname(path), { recursive: true })
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'screencap', '-p', '/sdcard/dsh-agent-shot.png'])
      if (!r.ok) return { ok: false, serial, output_path: path, message: r.error }
      const p = await run(adbPath, [...serialArgs(serial), 'pull', '/sdcard/dsh-agent-shot.png', path])
      return { ok: p.ok, serial, output_path: path, message: p.stdout || p.error }
    } })
  register(ctx, { name: 'android_ui_dump', description: 'Dump the Android accessibility/UI hierarchy XML.', parameters: { serial: { type: 'string', required: true } }, properties: { xml: { type: 'string' } },
    async execute({ serial }) {
      const s = serialArgs(serial), d = await run(adbPath, [...s, 'shell', 'uiautomator', 'dump', '/sdcard/window.xml'])
      if (!d.ok) return { ok: false, xml: d.error }
      const r = await run(adbPath, [...s, 'shell', 'cat', '/sdcard/window.xml'])
      return { ok: r.ok, xml: r.stdout || r.error }
    } })
  register(ctx, { name: 'android_tap', description: 'Tap screen coordinates on an explicitly selected Android target.', parameters: { serial: { type: 'string', required: true }, x: { type: 'number', required: true }, y: { type: 'number', required: true } }, properties: { output: { type: 'string' } },
    async execute({ serial, x, y }) {
      if (![x, y].every(n => Number.isFinite(n) && n >= 0 && n <= 10000)) throw new Error('Coordinates must be finite values between 0 and 10000.')
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'input', 'tap', String(Math.round(x)), String(Math.round(y))])
      return { ok: r.ok, output: r.stdout || r.error || 'Tap sent.' }
    } })
  register(ctx, { name: 'android_swipe', description: 'Swipe between two screen points on an explicitly selected target.', parameters: { serial: { type: 'string', required: true }, x1: { type: 'number', required: true }, y1: { type: 'number', required: true }, x2: { type: 'number', required: true }, y2: { type: 'number', required: true }, duration_ms: { type: 'number' } }, properties: { output: { type: 'string' } },
    async execute({ serial, x1, y1, x2, y2, duration_ms = 400 }) {
      const v = [x1, y1, x2, y2]; if (v.some(n => !Number.isFinite(n) || n < 0 || n > 10000)) throw new Error('Invalid coordinates.')
      const d = Math.max(100, Math.min(3000, Number(duration_ms) || 400))
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'input', 'swipe', ...v.map(n => String(Math.round(n))), String(d)])
      return { ok: r.ok, output: r.stdout || r.error || 'Swipe sent.' }
    } })
  register(ctx, { name: 'android_type_text', description: 'Type non-sensitive text into the focused Android field. Never use for passwords or tokens.', parameters: { serial: { type: 'string', required: true }, text: { type: 'string', required: true } }, properties: { output: { type: 'string' } },
    async execute({ serial, text }) {
      if (text.length > 500) throw new Error('Text is limited to 500 characters.')
      const escaped = text.replace(/%/g, '%25').replace(/ /g, '%s').replace(/&/g, '\\&').replace(/[<>|;]/g, '')
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'input', 'text', escaped])
      return { ok: r.ok, output: r.stdout || r.error || 'Text input sent.' }
    } })
  register(ctx, { name: 'android_keyevent', description: 'Send a limited Android navigation key event.', parameters: { serial: { type: 'string', required: true }, key: { type: 'string', required: true } }, properties: { key: { type: 'string' }, output: { type: 'string' } },
    async execute({ serial, key }) {
      const keys = { BACK: '4', HOME: '3', ENTER: '66', TAB: '61', DPAD_UP: '19', DPAD_DOWN: '20', DPAD_LEFT: '21', DPAD_RIGHT: '22' }
      if (!keys[key]) throw new Error('Unsupported key. Use BACK, HOME, ENTER, TAB, or DPAD directions.')
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'input', 'keyevent', keys[key]])
      return { ok: r.ok, key, output: r.stdout || r.error || 'Key event sent.' }
    } })
  register(ctx, { name: 'android_logcat', description: 'Read recent Android logcat output with optional literal substring filter.', parameters: { serial: { type: 'string', required: true }, lines: { type: 'number' }, filter: { type: 'string' } }, properties: { log: { type: 'string' } },
    async execute({ serial, lines = 1000, filter = '' }) {
      const n = Math.max(100, Math.min(5000, Number(lines) || 1000))
      const r = await run(adbPath, [...serialArgs(serial), 'logcat', '-d', '-t', String(n)], 30000)
      const log = filter ? r.stdout.split('\n').filter(x => x.includes(filter)).join('\n') : r.stdout
      return { ok: r.ok, log: log.slice(-100000) || r.error || '' }
    } })
  register(ctx, { name: 'android_google_services_check', description: 'Check for Google Play Store and Google Play Services packages.', parameters: { serial: { type: 'string', required: true } }, properties: { play_store: { type: 'boolean' }, play_services: { type: 'boolean' }, packages: { type: 'string' }, interpretation: { type: 'string' } },
    async execute({ serial }) {
      const r = await run(adbPath, [...serialArgs(serial), 'shell', 'pm', 'list', 'packages'], 30000)
      const lines = r.stdout.split('\n'), store = lines.some(x => x.includes('com.android.vending')), services = lines.some(x => x.includes('com.google.android.gms'))
      return { ok: r.ok, play_store: store, play_services: services,
        packages: lines.filter(x => /com\.android\.vending|com\.google\.android\.gms/.test(x)).join('\n'),
        interpretation: store && services ? 'Both package IDs are present. This does not prove device certification or Play Integrity success.' : 'One or both packages are missing; verify a Google Play system image and complete first-boot setup.' }
    } })
}
