(function () {
  "use strict";

  var loadingEl = document.getElementById("loading");

  fetch("./assets/atlas_data.json")
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(runApp)
    .catch(function (err) {
      if (loadingEl) {
        loadingEl.querySelector(".loading-text").textContent = "Couldn't load atlas data — " + err.message;
      }
    });

  function runApp(ATLAS) {
  if (loadingEl) loadingEl.remove();

  var root = document.documentElement;
  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  // ---------------- Theme ----------------
  var themeBtn = document.getElementById("theme-toggle");
  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  themeBtn.addEventListener("click", function () {
    var next = currentTheme() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    themeBtn.textContent = next === "dark" ? "◑" : "◐";
    refreshAllLayerColors();
  });
  themeBtn.textContent = currentTheme() === "dark" ? "◑" : "◐";

  // ---------------- Category / sublayer meta ----------------
  var CAT_META = {
    resource: { colorVar: "--cat-resource" },
    infrastructure: { colorVar: "--cat-infrastructure" },
    environmental: { colorVar: "--cat-environmental" },
    demand: { colorVar: "--cat-demand" },
    connectivity: { colorVar: "--cat-connectivity" },
    renewables: { colorVar: "--cat-renewables" }
  };
  var CAT_ORDER = ["resource", "infrastructure", "environmental", "demand", "connectivity", "renewables"];

  var SHAPE_BY_SUB = {
    fields: "circle",
    lng_terminals: "hex",
    power_plants: "square",
    refineries: "triangle",
    demand_centers: "diamond",
    rail_stations: "square",
    substations: "triangle",
    ports: "star",
    minigrids: "plus"
  };
  var LINEDASH_BY_SUB = {
    gas_pipelines: null,
    oil_pipelines: "6,5",
    roads: null,
    railways: "1,6",
    power_grid: "2,4"
  };
  var DEFAULT_ON = {
    fields: true,
    gas_pipelines: true,
    oil_pipelines: true,
    lng_terminals: true,
    power_plants: true,
    refineries: true,
    protected_areas: false,
    demand_centers: true,
    roads: false,
    railways: false,
    rail_stations: true,
    power_grid: false,
    substations: true,
    ports: true,
    minigrids: true
  };

  var STATUS_MAP = {
    operating: "good", active: "good", "in use": "good",
    construction: "warning", "in development": "warning", "pre-construction": "warning",
    proposed: "serious", planned: "serious", announced: "serious", discovered: "serious",
    mothballed: "critical", cancelled: "critical", shelved: "critical", "shut in": "critical", retired: "critical"
  };

  // ---------------- SVG glyph builder ----------------
  // filled=true (operating/unknown status): solid category-color fill.
  // filled=false (non-operating: construction/proposed/mothballed/etc.):
  // hollow outline only, same hue, so category identity is never lost --
  // status reads as "weight" (solid vs open) rather than a second color.
  function shapeSvg(shape, color, size, filled) {
    size = size || 13;
    var s = size, h = size / 2;
    var inner = "";
    var fillValue = filled === false ? "none" : color;
    var strokeValue = filled === false ? color : "rgba(0,0,0,0.35)";
    var strokeWidth = filled === false ? "1.6" : "1";
    switch (shape) {
      case "square":
        inner = '<rect x="2" y="2" width="' + (s-4) + '" height="' + (s-4) + '" rx="1.5" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
        break;
      case "triangle":
        inner = '<polygon points="' + h + ',2 ' + (s-2) + ',' + (s-2) + ' 2,' + (s-2) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "diamond":
        inner = '<polygon points="' + h + ',1 ' + (s-1) + ',' + h + ' ' + h + ',' + (s-1) + ' 1,' + h + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "hex":
        var pts = [];
        for (var i = 0; i < 6; i++) {
          var ang = Math.PI / 180 * (60 * i - 30);
          pts.push((h + (h - 1.5) * Math.cos(ang)).toFixed(1) + "," + (h + (h - 1.5) * Math.sin(ang)).toFixed(1));
        }
        inner = '<polygon points="' + pts.join(" ") + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "star":
        var spts = [];
        for (var k = 0; k < 10; k++) {
          var r = k % 2 === 0 ? h - 1 : (h - 1) * 0.45;
          var a = Math.PI / 180 * (36 * k - 90);
          spts.push((h + r * Math.cos(a)).toFixed(1) + "," + (h + r * Math.sin(a)).toFixed(1));
        }
        inner = '<polygon points="' + spts.join(" ") + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      case "plus":
        var arm = s * 0.2;
        inner = '<path d="M ' + (h-arm) + ' 2 L ' + (h+arm) + ' 2 L ' + (h+arm) + ' ' + (h-arm) + ' L ' + (s-2) + ' ' + (h-arm) + ' L ' + (s-2) + ' ' + (h+arm) + ' L ' + (h+arm) + ' ' + (h+arm) + ' L ' + (h+arm) + ' ' + (s-2) + ' L ' + (h-arm) + ' ' + (s-2) + ' L ' + (h-arm) + ' ' + (h+arm) + ' L 2 ' + (h+arm) + ' L 2 ' + (h-arm) + ' L ' + (h-arm) + ' ' + (h-arm) + ' Z" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '" stroke-linejoin="round"/>';
        break;
      default:
        inner = '<circle cx="' + h + '" cy="' + h + '" r="' + (h - 2) + '" fill="' + fillValue + '" stroke="' + strokeValue + '" stroke-width="' + strokeWidth + '"/>';
    }
    return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 ' + s + ' ' + s + '" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
  }

  function divIcon(shape, color, filled) {
    return L.divIcon({
      html: shapeSvg(shape, color, 14, filled),
      className: "atlas-marker",
      iconSize: [14, 14],
      iconAnchor: [7, 7],
      popupAnchor: [0, -7]
    });
  }

  // Resolves a feature's status field to whether it should render as
  // "operating" (solid marker) or not (hollow marker). Layers with no status
  // field at all default to solid, since there's nothing to distinguish.
  function isOperating(props) {
    var raw = (props.status || props.STATUS || "").toString().toLowerCase();
    if (!raw) return true;
    if (raw.indexOf("operat") !== -1 || raw.indexOf("active") !== -1 || raw.indexOf("in use") !== -1) return true;
    return false;
  }

  // ---------------- Popup builder ----------------
  var FIELD_LABELS = {
    project: "Project", status: "Status", operator: "Operator", owner: "Owner",
    fuel_type: "Fuel type", discovery_year: "Discovered", start_year: "Start year",
    parent: "Operator/Owner", capacity: "Capacity", capacity_units: "Units",
    unit: "Unit", province: "State", technology: "Technology",
    capacity_bpd: "Capacity (bpd)", commissioned_year: "Commissioned", state: "State",
    NAME: "Name", DESIG_ENG: "Designation", IUCN_CAT: "IUCN category",
    GIS_AREA: "Area (km²)", STATUS: "Status", STATUS_YR: "Since", GOV_TYPE: "Governance",
    demand_center: "Site", category: "Category", state_or_region: "State/Region", notes: "Notes",
    highway: "Road class", name: "Name", ref: "Ref", surface: "Surface", lanes: "Lanes",
    railway: "Type", gauge: "Gauge", power: "Type", voltage: "Voltage",
    PORT_NAME: "Port", HARBORSIZE: "Harbor size", HARBORTYPE: "Harbor type",
    CARGOWHARF: "Cargo wharf", CRANEFIXED: "Fixed crane", RAILWAY: "Rail service", MAX_VESSEL: "Max vessel size",
    asset_name: "Site", lga: "LGA", capacity_kw: "Capacity (kW)", customers_served: "Customers served",
    financing_source: "Financing", source_url: "Source"
  };
  var SKIP_IN_ROWS = { project: 1, url: 1, NAME: 1, demand_center: 1, name: 1, PORT_NAME: 1, status: 1, STATUS: 1, asset_name: 1, source_url: 1 };

  function titleOf(props) {
    return props._label || props.project || props.NAME || props.demand_center || props.name || props.PORT_NAME || props.asset_name || "Untitled asset";
  }
  function statusOf(props) {
    var raw = (props.status || props.STATUS || "").toString().toLowerCase();
    for (var key in STATUS_MAP) { if (raw.indexOf(key) !== -1) return { raw: props.status || props.STATUS, level: STATUS_MAP[key] }; }
    return raw ? { raw: props.status || props.STATUS, level: null } : null;
  }

  function popupHtml(sublayerLabel, catColorVar, props) {
    var title = titleOf(props);
    var st = statusOf(props);
    var html = '<div class="popup-card">';
    html += '<div class="p-eyebrow" style="color:var(' + catColorVar + ')">' + sublayerLabel + '</div>';
    html += '<div class="p-title">' + escapeHtml(title) + '</div>';
    if (st) {
      var lvl = st.level;
      var color = lvl ? "var(--status-" + lvl + ")" : "var(--text-muted)";
      html += '<div class="p-status" style="background:color-mix(in srgb, ' + color + ' 16%, transparent); color:' + color + '"><span class="dot" style="background:' + color + '"></span>' + escapeHtml(st.raw) + '</div>';
    }
    html += '<div class="p-rows">';
    var keys = Object.keys(props).filter(function (k) { return !SKIP_IN_ROWS[k] && k.charAt(0) !== "_" && props[k] !== null && props[k] !== undefined && props[k] !== ""; });
    keys.forEach(function (k) {
      var label = FIELD_LABELS[k] || k;
      var val = props[k];
      html += '<div class="p-row"><span class="p-k">' + escapeHtml(label) + '</span><span class="p-v">' + escapeHtml(String(val)) + '</span></div>';
    });
    html += '</div>';
    var link = props.url || props.source_url;
    if (link) {
      html += '<a class="p-link" href="' + escapeAttr(link) + '" target="_blank" rel="noopener">View source ↗</a>';
    }
    html += '</div>';
    return html;
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }
  function escapeAttr(s) { return escapeHtml(s); }

  // ---------------- Map init ----------------
  var map = L.map("map", { zoomControl: false, minZoom: 5, maxZoom: 16, attributionControl: false });
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.control.attribution({ position: "bottomleft", prefix: false }).addTo(map)
    .addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a>');
  var NIGERIA_BOUNDS = [[3.9, 2.5], [14.0, 14.8]];
  map.fitBounds(NIGERIA_BOUNDS);

  var TILE_URLS = {
    light: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
  };
  var tileLayer = L.tileLayer(TILE_URLS[currentTheme() === "dark" ? "dark" : "light"], {
    maxZoom: 20,
    subdomains: "abcd"
  }).addTo(map);

  var statesLayer = L.geoJSON(ATLAS.states, {
    style: function () {
      return { color: cssVar("--line"), weight: 1.4, fillColor: cssVar("--paper-100"), fillOpacity: 0.35 };
    },
    onEachFeature: function (feature, lyr) {
      var name = feature.properties && feature.properties.name;
      if (!name) return;
      lyr.bindTooltip(name, { permanent: true, direction: "center", className: "state-label", interactive: false });
    }
  }).addTo(map);
  statesLayer.bringToBack();
  tileLayer.bringToBack();

  // ---------------- Click highlight (pin drop) ----------------
  function pinIconHtml() {
    var accent = cssVar("--accent");
    return (
      '<div class="highlight-pin">' +
        '<div class="pulse-ring"></div>' +
        '<div class="pin-body">' +
          '<svg width="34" height="46" viewBox="0 0 34 46" xmlns="http://www.w3.org/2000/svg">' +
            '<path d="M17 1 C9.8 1 4 6.8 4 14 C4 24 17 45 17 45 C17 45 30 24 30 14 C30 6.8 24.2 1 17 1 Z" fill="' + accent + '" stroke="rgba(0,0,0,0.3)" stroke-width="1"/>' +
            '<circle cx="17" cy="14" r="5.5" fill="#fff"/>' +
          '</svg>' +
        '</div>' +
      '</div>'
    );
  }
  var highlightMarker = L.marker([0, 0], {
    icon: L.divIcon({ html: pinIconHtml(), className: "highlight-pin-wrap", iconSize: [34, 46], iconAnchor: [17, 45] }),
    interactive: false,
    keyboard: false,
    zIndexOffset: 1000
  });
  map.on("popupopen", function (e) {
    var latlng = e.popup.getLatLng();
    if (!latlng) return;
    highlightMarker.setIcon(L.divIcon({ html: pinIconHtml(), className: "highlight-pin-wrap", iconSize: [34, 46], iconAnchor: [17, 45] }));
    highlightMarker.setLatLng(latlng);
    if (!map.hasLayer(highlightMarker)) highlightMarker.addTo(map);
  });
  map.on("popupclose", function () {
    if (map.hasLayer(highlightMarker)) map.removeLayer(highlightMarker);
  });

  // ---------------- Build layers ----------------
  var registry = {}; // subKey -> { leafletLayer, catKey, meta, count }
  var allFeaturesIndex = []; // for search: {label, subKey, catKey, feature, latlng}

  function lineStyle(catColor, subKey) {
    var dash = LINEDASH_BY_SUB[subKey];
    var weight = subKey === "roads" ? 2 : subKey === "power_grid" ? 1.4 : 2.2;
    return { color: catColor, weight: weight, opacity: 0.85, dashArray: dash || null, lineCap: "round" };
  }

  function buildSublayer(catKey, subKey, sub) {
    var catColorVar = CAT_META[catKey].colorVar;
    var catColor = cssVar(catColorVar);
    var geomType = sub.geomType;
    var layer;

    if (geomType === "point") {
      var shape = SHAPE_BY_SUB[subKey] || "circle";
      layer = L.geoJSON(sub.data, {
        pointToLayer: function (feature, latlng) {
          var filled = isOperating(feature.properties);
          var marker = L.marker(latlng, { icon: divIcon(shape, cssVar(catColorVar), filled) });
          marker._ngraFilled = filled;
          return marker;
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, catColorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl) allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr });
        }
      });
    } else if (geomType === "line") {
      layer = L.geoJSON(sub.data, {
        style: function () { return lineStyle(catColor, subKey); },
        // Guards against any stray Point feature inside a line-typed sublayer --
        // without this, Leaflet silently falls back to its (unstyled, broken-
        // image) default marker icon instead of using our design system.
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, { icon: divIcon("circle", catColor) });
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, catColorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl && lbl !== "Untitled asset") allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr });
        }
      });
    } else {
      layer = L.geoJSON(sub.data, {
        style: function () {
          return { color: catColor, weight: 1.2, opacity: 0.8, fillColor: catColor, fillOpacity: 0.18 };
        },
        // Same guard as above -- WDPA in particular mixes polygon boundaries
        // with point-only records (protected areas with no mapped footprint).
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, { icon: divIcon("circle", catColor) });
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, catColorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl) allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr });
        }
      });
    }
    return { layer: layer, getMarker: null, refresh: null };
  }

  var totalFeatures = 0;
  CAT_ORDER.forEach(function (catKey) {
    var cat = ATLAS.layers[catKey];
    if (!cat) return;
    Object.keys(cat.sublayers).forEach(function (subKey) {
      var sub = cat.sublayers[subKey];
      var count = sub.data.features.length;
      totalFeatures += count;
      var built = buildSublayer(catKey, subKey, sub);
      registry[subKey] = {
        leafletLayer: built.layer, getMarker: built.getMarker, refresh: built.refresh,
        catKey: catKey, geomType: sub.geomType, label: sub.label, count: count
      };
      if (DEFAULT_ON[subKey]) built.layer.addTo(map);
    });
  });
  document.getElementById("stat-total").textContent = totalFeatures.toLocaleString();

  function refreshAllLayerColors() {
    tileLayer.setUrl(TILE_URLS[currentTheme() === "dark" ? "dark" : "light"]);
    // rebuild point icons & line styles to match new theme's CSS vars
    CAT_ORDER.forEach(function (catKey) {
      var cat = ATLAS.layers[catKey];
      if (!cat) return;
      Object.keys(cat.sublayers).forEach(function (subKey) {
        var entry = registry[subKey];
        if (!entry) return;
        var catColor = cssVar(CAT_META[catKey].colorVar);
        if (entry.geomType === "point") {
          var shape = SHAPE_BY_SUB[subKey] || "circle";
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr.setIcon) lyr.setIcon(divIcon(shape, catColor, lyr._ngraFilled));
          });
        } else if (entry.geomType === "line") {
          entry.leafletLayer.setStyle(lineStyle(catColor, subKey));
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr.setIcon) lyr.setIcon(divIcon("circle", catColor));
          });
        } else {
          entry.leafletLayer.setStyle({ color: catColor, fillColor: catColor });
          entry.leafletLayer.eachLayer(function (lyr) {
            if (lyr.setIcon) lyr.setIcon(divIcon("circle", catColor));
          });
        }
      });
    });
    statesLayer.setStyle({ color: cssVar("--line"), fillColor: cssVar("--paper-100") });
  }

  // ---------------- Panel UI ----------------
  var listEl = document.getElementById("category-list");
  var CAT_LABELS = { resource: "Resource", infrastructure: "Infrastructure", environmental: "Environmental", demand: "Demand", connectivity: "Connectivity", renewables: "Renewables" };

  CAT_ORDER.forEach(function (catKey) {
    var cat = ATLAS.layers[catKey];
    if (!cat) return;
    var group = document.createElement("div");
    group.className = "category-group";
    var subKeys = Object.keys(cat.sublayers);
    var catCount = subKeys.reduce(function (s, k) { return s + cat.sublayers[k].data.features.length; }, 0);

    var head = document.createElement("div");
    head.className = "category-head";
    head.innerHTML =
      '<span class="swatch" style="background:var(' + CAT_META[catKey].colorVar + ')"></span>' +
      '<span class="cname">' + CAT_LABELS[catKey] + '</span>' +
      '<span class="ccount">' + catCount.toLocaleString() + '</span>' +
      '<svg class="chev" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>';
    head.addEventListener("click", function () { group.classList.toggle("collapsed"); });
    group.appendChild(head);

    var subWrap = document.createElement("div");
    subWrap.className = "sublayers";
    subKeys.forEach(function (subKey) {
      var sub = cat.sublayers[subKey];
      var row = document.createElement("label");
      row.className = "sub-row";
      var glyphHtml = sub.geomType === "point"
        ? shapeSvg(SHAPE_BY_SUB[subKey] || "circle", cssVar(CAT_META[catKey].colorVar), 12)
        : sub.geomType === "line"
          ? '<svg width="16" height="12" viewBox="0 0 16 12"><line x1="1" y1="6" x2="15" y2="6" stroke="' + cssVar(CAT_META[catKey].colorVar) + '" stroke-width="2.4" stroke-dasharray="' + (LINEDASH_BY_SUB[subKey] || "") + '" stroke-linecap="round"/></svg>'
          : '<svg width="14" height="12" viewBox="0 0 14 12"><rect x="1" y="1" width="12" height="10" rx="2" fill="' + cssVar(CAT_META[catKey].colorVar) + '" opacity="0.35" stroke="' + cssVar(CAT_META[catKey].colorVar) + '" stroke-width="1.3"/></svg>';
      row.innerHTML =
        '<input type="checkbox" ' + (DEFAULT_ON[subKey] ? "checked" : "") + ' data-sub="' + subKey + '"/>' +
        '<span class="glyph">' + glyphHtml + '</span>' +
        '<span class="sname">' + sub.label + '</span>' +
        '<span class="scount">' + sub.data.features.length.toLocaleString() + '</span>';
      subWrap.appendChild(row);
      row.querySelector("input").addEventListener("change", function (e) {
        var entry = registry[subKey];
        if (e.target.checked) { entry.leafletLayer.addTo(map); } else { map.removeLayer(entry.leafletLayer); }
        updateVisibleStat();
      });
    });
    group.appendChild(subWrap);
    listEl.appendChild(group);
  });

  function updateVisibleStat() {
    var n = 0;
    Object.keys(registry).forEach(function (k) {
      if (map.hasLayer(registry[k].leafletLayer)) n += registry[k].count;
    });
    document.getElementById("stat-visible").textContent = n.toLocaleString();
  }
  updateVisibleStat();

  // ---------------- Search ----------------
  var searchInput = document.getElementById("search-input");
  var searchResults = document.getElementById("search-results");
  searchInput.addEventListener("input", function () {
    var q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.classList.remove("open"); searchResults.innerHTML = ""; return; }
    var matches = allFeaturesIndex.filter(function (item) {
      return item.label.toLowerCase().indexOf(q) !== -1;
    }).slice(0, 8);
    if (!matches.length) {
      searchResults.innerHTML = '<div class="result">No matches</div>';
    } else {
      searchResults.innerHTML = matches.map(function (m, i) {
        return '<div class="result" data-idx="' + i + '"><span>' + escapeHtml(m.label) + '</span><span class="r-cat">' + m.subLabel + '</span></div>';
      }).join("");
      Array.prototype.forEach.call(searchResults.querySelectorAll(".result"), function (el, i) {
        el.addEventListener("click", function () {
          var m = matches[i];
          var entry = registry[m.subKey];
          if (!map.hasLayer(entry.leafletLayer)) {
            entry.leafletLayer.addTo(map);
            var cb = document.querySelector('input[data-sub="' + m.subKey + '"]');
            if (cb) cb.checked = true;
            updateVisibleStat();
          }
          var target = m.layer.getBounds ? m.layer.getBounds() : m.layer.getLatLng();
          if (target && target.isValid && target.isValid()) map.fitBounds(target.pad ? target.pad(2) : target, { maxZoom: 11 });
          else if (m.layer.getLatLng) map.setView(m.layer.getLatLng(), 11);
          m.layer.openPopup();
          searchResults.classList.remove("open");
          searchInput.value = m.label;
        });
      });
    }
    searchResults.classList.add("open");
  });
  document.addEventListener("click", function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.classList.remove("open");
  });
  } // end runApp
})();
