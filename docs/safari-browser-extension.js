browser.runtime.onMessage.addListener((message, sender) => {
  if (message && message.type === 'refresh') {
    return Promise.resolve({ ok: true, refreshedAt: Date.now() });
  }
  if (message && message.greeting === 'hello') {
    return Promise.resolve({ reply: 'hi from background' });
  }
  // Generieke API GET via de background (omzeilt CORS in het content script).
  if (message && message.type === 'api_get') {
    return fetch(message.url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${message.token}`, 'accept': '*/*' }
    })
      .then(async r => ({ ok: r.ok, status: r.status, data: r.ok ? await r.json() : null }))
      .catch(e => ({ ok: false, status: 0, data: null, error: e.message }));
  }
  // Live token validity check: fetch a known Portflow API endpoint from the
  // background so we are not blocked by CORS restrictions in the content script.
  if (message && message.type === 'check_token') {
    const baseUrl = message.baseUrl || 'https://portfolio.drieam.app';
    const url = `${baseUrl}/api/v1/me`;
    return fetch(url, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${message.token}` }
    })
      .then(r => ({ valid: r.ok, status: r.status }))
      .catch(e => ({ valid: false, status: 0, error: e.message }));
  }
});

// Luister naar network requests op de achtergrond.
// Dit is veel betrouwbaarder dan het proberen te patchen van window.fetch in een Safari Extension.
chrome.webRequest.onSendHeaders.addListener(
  function(details) {
    if (details.requestHeaders) {
      for (let header of details.requestHeaders) {
        if (header.name.toLowerCase() === 'authorization' && header.value.startsWith('Bearer ')) {
          console.log("[Portflow Ext] Bearer token onderschept via webRequest API!");
          const token = header.value.slice(7);
          
          chrome.storage.local.set({ portflow_token: { token, timestamp: Date.now() } });
          try { chrome.storage.session.set({ portflow_token: { token, timestamp: Date.now() } }); } catch(e) {}
          break;
        }
      }
    }
  },
  { urls: ["*://*.portflow.io/*", "*://*.hu.nl/*", "*://*.drieam.app/*"] },
  ["requestHeaders"]
);
