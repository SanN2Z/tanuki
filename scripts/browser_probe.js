async options => {
  "use strict";
  options = options || {};
  const report = {
    kind: "tanuki-browser-report",
    collected_at: new Date().toISOString(),
    context: {origin: location.origin, automated: navigator.webdriver},
    local: {status: "not_measured"},
    network: {status: "not_measured"},
    webrtc: {status: "not_measured"},
    errors: []
  };
  const failed = (source, error) => {
    const entry = {source, name: error.name || "Error", message: String(error.message || error)};
    report.errors.push(entry);
    console.error("[fail]", source, error);
    return {status: "unverified", error: entry};
  };
  function realmSnapshot(w = globalThis) {
    const nav = w.navigator;
    return {
      timezone: new w.Intl.DateTimeFormat().resolvedOptions().timeZone,
      offset_minutes_js: new w.Date().getTimezoneOffset(),
      language: nav.language,
      languages: Array.from(nav.languages || []),
      date_format: new w.Intl.DateTimeFormat().resolvedOptions(),
      number_format: new w.Intl.NumberFormat().resolvedOptions(),
      collator_locale: new w.Intl.Collator().resolvedOptions().locale,
      user_agent: nav.userAgent,
      platform: nav.platform,
      ua_ch: nav.userAgentData ? {
        brands: nav.userAgentData.brands,
        mobile: nav.userAgentData.mobile,
        platform: nav.userAgentData.platform
      } : {status: "unsupported"}
    };
  }
  function workerSnapshot() {
    return new Promise(resolve => {
      let worker, timer, blobUrl;
      const finish = value => {
        clearTimeout(timer);
        if (worker) worker.terminate();
        if (blobUrl) URL.revokeObjectURL(blobUrl);
        resolve(value);
      };
      try {
        blobUrl = URL.createObjectURL(new Blob(
          ["self.postMessage((" + realmSnapshot.toString() + ")());"],
          {type: "application/javascript"}));
        worker = new Worker(blobUrl);
        worker.onmessage = event => finish({status: "measured", ...event.data});
        worker.onerror = event => finish(failed("worker", new Error(event.message)));
        timer = setTimeout(() => finish(failed("worker", new Error("Worker timed out"))), 2000);
      } catch (error) { finish(failed("worker", error)); }
    });
  }
  function fonts() {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return {status: "unverified", reason: "Canvas 2D unavailable"};
    const candidates = [
      "Yu Gothic", "Meiryo", "Yu Mincho", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP",
      "Microsoft YaHei", "SimSun", "PingFang SC", "MiSans", "HarmonyOS Sans SC", "OPPO Sans"
    ];
    const text = "AaBb0123456789 日本語かなカナ中文";
    const bases = ["serif", "sans-serif", "monospace"];
    const likely = candidates.filter(font => bases.some(base => {
      ctx.font = "64px " + base;
      const baseline = ctx.measureText(text).width;
      ctx.font = '64px "' + font + '",' + base;
      return Math.abs(ctx.measureText(text).width - baseline) > 0.5;
    }));
    return {status: "measured", method: "relative_canvas_width",
      likely_available: likely, note: "Approximate font visibility; browser protections and fallback affect results."};
  }
  function graphics() {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl");
    if (!gl) return {status: "unavailable", webgpu_api: Boolean(navigator.gpu)};
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    const result = {
      status: "measured", vendor: gl.getParameter(gl.VENDOR), renderer: gl.getParameter(gl.RENDERER),
      unmasked_vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : null,
      unmasked_renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : null,
      webgpu_api: Boolean(navigator.gpu)
    };
    const cleanup = gl.getExtension("WEBGL_lose_context");
    if (cleanup) cleanup.loseContext();
    return result;
  }
  async function localProbe() {
    const result = {status: "measured", main: realmSnapshot(),
      date_sample: new Date().toLocaleString(), number_sample: (12345.67).toLocaleString(),
      screen: {width: screen.width, height: screen.height, available_width: screen.availWidth,
        available_height: screen.availHeight, dpr: devicePixelRatio, color_depth: screen.colorDepth},
      device: {cores: navigator.hardwareConcurrency, memory_gb_hint: navigator.deviceMemory,
        touch_points: navigator.maxTouchPoints, webdriver: navigator.webdriver},
      capabilities: {canvas: true, audio_context: Boolean(window.AudioContext || window.webkitAudioContext)},
      fonts: fonts(), graphics: graphics()};
    if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
      try {
        result.ua_ch_high = {status: "measured", ...await navigator.userAgentData.getHighEntropyValues(
          ["architecture", "bitness", "model", "platformVersion", "fullVersionList"])};
      } catch (error) { result.ua_ch_high = failed("ua_ch_high", error); }
    } else { result.ua_ch_high = {status: "unsupported"}; }
    let iframe;
    try {
      iframe = document.createElement("iframe");
      iframe.hidden = true;
      document.body.appendChild(iframe);
      result.iframe = {status: "measured", ...realmSnapshot(iframe.contentWindow)};
    } catch (error) { result.iframe = failed("iframe", error); }
    finally { if (iframe) iframe.remove(); }
    result.worker = await workerSnapshot();
    if (navigator.permissions) {
      try {
        const permission = await navigator.permissions.query({name: "geolocation"});
        result.geolocation_permission = {state: permission.state, scope: location.origin,
          coordinates_requested: false};
      } catch (error) { result.geolocation_permission = failed("geolocation_permission", error); }
    } else { result.geolocation_permission = {status: "unsupported", coordinates_requested: false}; }
    if (window.speechSynthesis) {
      if (!speechSynthesis.getVoices().length) {
        await new Promise(resolve => {
          const done = () => {
            clearTimeout(timer);
            speechSynthesis.removeEventListener("voiceschanged", done);
            resolve();
          };
          const timer = setTimeout(done, 700);
          speechSynthesis.addEventListener("voiceschanged", done);
        });
      }
      const voices = speechSynthesis.getVoices();
      result.voices = {status: voices.length ? "measured" : "unavailable_or_not_loaded",
        languages: [...new Set(voices.map(voice => voice.lang))],
        local_voice_count: voices.filter(voice => voice.localService).length};
    } else { result.voices = {status: "unsupported"}; }
    report.local = result;
  }
  async function networkProbe() {
    const sources = ["https://ipapi.co/json/", "https://ipinfo.io/json"];
    const results = await Promise.all(sources.map(async source => {
      try {
        const response = await fetch(source, {credentials: "omit", cache: "no-store",
          referrerPolicy: "no-referrer", signal: AbortSignal.timeout(7000)});
        if (!response.ok) throw new Error("HTTP " + response.status);
        const value = await response.json();
        const country = value.country_code || value.country;
        if (value.error || !country || !value.ip) throw new Error("Provider did not return IP and country");
        return {source, status: "measured", ip: value.ip, country, timezone: value.timezone,
          asn: value.asn, organization: value.org};
      } catch (error) { return {source, ...failed("network:" + source, error)}; }
    }));
    report.network = {status: results.every(item => item.status === "measured") ? "measured" : "partial",
      context: "this_browser_page_only", results};
  }
  function addressClass(address) {
    if (!address) return "unknown";
    const value = address.toLowerCase();
    if (value.endsWith(".local")) return "mdns_host";
    if (value.includes(":")) {
      return value === "::" || value === "::1" || /^(fc|fd|fe[89ab])/.test(value)
        ? "local_or_private" : "public_candidate";
    }
    const parts = value.split(".").map(Number);
    if (parts.length !== 4 || parts.some(part => !Number.isInteger(part) || part < 0 || part > 255))
      return "unknown";
    return parts[0] === 10 || parts[0] === 127 || parts[0] === 0 ||
      parts[0] >= 224 || (parts[0] === 192 && parts[1] === 168) ||
      (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
      (parts[0] === 169 && parts[1] === 254) ||
      (parts[0] === 198 && (parts[1] === 18 || parts[1] === 19)) ||
      (parts[0] === 100 && parts[1] >= 64 && parts[1] <= 127)
      ? "local_or_private" : "public_candidate";
  }
  async function webrtcProbe() {
    if (!window.RTCPeerConnection) {
      report.webrtc = {status: "unsupported"};
      return;
    }
    const pc = new RTCPeerConnection({iceServers: [{urls: "stun:stun.l.google.com:19302"}]});
    const candidates = [], errors = [];
    let timer, finish;
    const gathered = new Promise(resolve => {
      finish = status => { clearTimeout(timer); resolve(status); };
      pc.onicecandidate = event => {
        if (!event.candidate) { finish("gathering_complete"); return; }
        const c = event.candidate;
        const address = c.address || c.candidate.split(" ")[4];
        const type = c.type || (c.candidate.match(/ typ (\w+)/) || [])[1];
        if (!candidates.some(item => item.address === address && item.type === type &&
                             item.protocol === c.protocol)) {
          candidates.push({type, protocol: c.protocol, address, address_class: addressClass(address)});
        }
      };
      pc.onicecandidateerror = event => errors.push({code: event.errorCode});
      timer = setTimeout(() => finish("timeout_partial"), 6000);
    });
    try {
      pc.createDataChannel("tanuki-probe");
      await pc.setLocalDescription(await pc.createOffer());
      const status = await gathered;
      const httpIps = (report.network.results || []).filter(item => item.status === "measured").map(item => item.ip);
      report.webrtc = {status, candidates, errors,
        public_candidate_comparison: candidates.filter(item => item.address_class === "public_candidate")
          .map(item => ({address: item.address, comparison: !httpIps.length ? "http_exit_not_measured" :
            httpIps.includes(item.address) ? "same_as_observed_http" : "different_from_observed_http"})),
        note: "Candidate differences need routing evidence. No candidates does not prove no bypass."};
    } finally { clearTimeout(timer); pc.close(); }
  }

  try { await localProbe(); }
  catch (error) { report.local = failed("local", error); }
  if (options.network !== false) {
    try { await networkProbe(); }
    catch (error) { report.network = failed("network", error); }
  }
  if (options.webrtc !== false) {
    try { await webrtcProbe(); }
    catch (error) { report.webrtc = failed("webrtc", error); }
  }
  return report;
}
