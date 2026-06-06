/**
 * Registriert das Regis-Lab Custom Icon als Lovelace Resource
 * Nutzt window.hassConnection (Browser bereits eingeloggt)
 */
export async function registerRegisIcon(ingressUrl) {
  try {
    const iconUrl = '/local/regis-icon.js'
    const hassConn = window.parent?.hassConnection || window.hassConnection
    if (!hassConn) return false

    const hass = await hassConn
    const ws   = hass.conn

    if (!ws?.sendMessagePromise) return false

    const resources = await ws.sendMessagePromise({ type: 'lovelace/resources' })
    if (resources.some(r => r.url?.includes('regis-icon'))) return true

    await ws.sendMessagePromise({
      type: 'lovelace/resources/create',
      res_type: 'module',
      url: iconUrl,
    })
    return true
  } catch(e) {
    // Kein Log-Spam — Icon-Registrierung ist optional
    return false
  }
}
