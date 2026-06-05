/**
 * Registriert das Regis-Lab Custom Icon als Lovelace Resource
 * Nutzt die bestehende Browser-Session (kein Token nötig)
 */
export async function registerRegisIcon(ingressUrl) {
  try {
    const iconUrl = `${ingressUrl}regis-icon.js`

    // HA WebSocket über Parent-Frame nutzen (Browser ist bereits eingeloggt)
    const haWs = window.parent?.hassConnection || window.hassConnection
    if (!haWs) return false

    const conn = await haWs

    // Bestehende Resources prüfen
    const resources = await conn.sendMessagePromise({
      type: 'lovelace/resources',
    })

    if (resources.some(r => r.url?.includes('regis-icon'))) {
      console.log('[Regis-Lab] Icon bereits registriert')
      return true
    }

    // Resource registrieren
    await conn.sendMessagePromise({
      type: 'lovelace/resources/create',
      res_type: 'module',
      url: iconUrl,
    })

    console.log('[Regis-Lab] Icon registriert:', iconUrl)
    return true
  } catch(e) {
    console.warn('[Regis-Lab] Icon-Registrierung fehlgeschlagen:', e)
    return false
  }
}
