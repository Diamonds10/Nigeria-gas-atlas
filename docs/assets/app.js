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
    renewables: { colorVar: "--cat-renewables" },
    context: { colorVar: "--cat-context" }
  };
  var CAT_ORDER = ["resource", "infrastructure", "environmental", "demand", "connectivity", "renewables", "context"];

  var SHAPE_BY_SUB = {
    fields_oil: "circle",
    fields_gas: "diamond",
    fields_mixed: "hex",
    lng_terminals: "hex",
    power_plants: "square",
    refineries: "triangle",
    gas_infrastructure: "diamond",
    demand_centers: "diamond",
    rail_stations: "square",
    substations: "triangle",
    ports: "star",
    minigrids: "plus",
    settlements: "circle"
  };
  var LINEDASH_BY_SUB = {
    gas_pipelines: null,
    oil_pipelines: "6,5",
    roads: null,
    railways: "1,6",
    power_grid: "2,4"
  };
  var DEFAULT_ON = {
    fields_oil: true,
    fields_gas: true,
    fields_mixed: true,
    field_polygons_gas: false,
    field_polygons_mixed: false,
    gas_pipelines: true,
    oil_pipelines: true,
    lng_terminals: true,
    power_plants: true,
    refineries: true,
    gas_infrastructure: true,
    protected_areas: false,
    demand_centers: true,
    roads: false,
    railways: false,
    rail_stations: true,
    power_grid: false,
    substations: true,
    ports: true,
    minigrids: true,
    population_access: false,
    settlements: false
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
    financing_source: "Financing", source_url: "Source",
    field_type: "Field type", in_goget_fields: "Also in GOGET inventory",
    type: "Asset type", company: "Operator", location: "Location",
    design_cap: "Design capacity", date_of_co: "Commissioned",
    population_estimate: "Modelled population", settlement_count: "Settlement clusters",
    population_with_nightlight_signal: "Population with night-light signal",
    population_without_nightlight_signal: "Population without night-light signal",
    nightlight_population_share_pct: "Night-light population share (%)",
    total_buildings: "Mapped buildings", modeled_demand: "Modelled demand",
    population_weighted_distance_transmission_km: "Population-weighted transmission distance (km)",
    population_weighted_distance_gridlight_km: "Population-weighted grid-light distance (km)",
    settlement_name: "Settlement", population: "Modelled population",
    state_population_rank: "Population rank in state", num_buildings: "Mapped buildings",
    nightlight_signal: "Night-light signal",
    distance_to_existing_transmission_lines: "Distance to transmission (km)",
    distance_to_existing_hv_transmission_lines: "Distance to HV transmission (km)",
    distance_to_gridlight_targets: "Distance to grid-light target (km)",
    main_road_access: "Main-road access", dist_main_road_km: "Distance to main road (km)",
    has_education_facility: "Education facility signal", has_health_facility: "Health facility signal"
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

  var selectedState = "";
  var stateLayersByName = {};
  function stateStyle(feature) {
    var name = feature.properties && feature.properties.name;
    var selected = selectedState && name === selectedState;
    return {
      color: selected ? cssVar("--accent") : cssVar("--line"),
      weight: selected ? 2.8 : 1.4,
      fillColor: selected ? cssVar("--accent") : cssVar("--paper-100"),
      fillOpacity: selected ? 0.22 : 0.35
    };
  }

  var statesLayer = L.geoJSON(ATLAS.states, {
    style: stateStyle,
    onEachFeature: function (feature, lyr) {
      var name = feature.properties && feature.properties.name;
      if (!name) return;
      stateLayersByName[name] = lyr;
      lyr.bindTooltip(name, { permanent: true, direction: "center", className: "state-label", interactive: false });
      lyr.on("click", function () { selectState(name, true); });
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
          if (subKey === "population_access") {
            var population = Number(feature.properties.population_estimate || 0);
            var radius = Math.max(3, Math.min(12, 2 + Math.log10(Math.max(population, 1))));
            var contextMarker = L.circleMarker(latlng, {
              radius: radius,
              color: cssVar(catColorVar),
              weight: 0.8,
              fillColor: cssVar(catColorVar),
              fillOpacity: 0.48
            });
            contextMarker._ngraContextGrid = true;
            return contextMarker;
          }
          var filled = isOperating(feature.properties);
          var marker = L.marker(latlng, { icon: divIcon(shape, cssVar(catColorVar), filled) });
          marker._ngraFilled = filled;
          return marker;
        },
        onEachFeature: function (feature, lyr) {
          lyr.bindPopup(popupHtml(sub.label, catColorVar, feature.properties), { maxWidth: 300 });
          var lbl = titleOf(feature.properties);
          if (lbl && subKey !== "population_access") {
            allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
          }
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
          if (lbl && lbl !== "Untitled asset") allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
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
          if (lbl) allFeaturesIndex.push({ label: lbl, subKey: subKey, catKey: catKey, subLabel: sub.label, layer: lyr, feature: feature });
        }
      });
    }
    var children = [];
    layer.eachLayer(function (child) { children.push(child); });
    return { layer: layer, children: children };
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
        leafletLayer: built.layer, children: built.children,
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
            if (lyr._ngraContextGrid && lyr.setStyle) {
              lyr.setStyle({ color: catColor, fillColor: catColor });
            } else if (lyr.setIcon) {
              lyr.setIcon(divIcon(shape, catColor, lyr._ngraFilled));
            }
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
    statesLayer.setStyle(stateStyle);
  }

  // ---------------- Panel UI ----------------
  var listEl = document.getElementById("category-list");
  var CAT_LABELS = { resource: "Resource", infrastructure: "Infrastructure", environmental: "Environmental", demand: "Demand", connectivity: "Connectivity", renewables: "Renewables", context: "People & Access" };

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
        '<span class="scount" data-sub-count="' + subKey + '">' + sub.data.features.length.toLocaleString() + '</span>';
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
      var entry = registry[k];
      var filteredCount = entry.children.reduce(function (sum, child) {
        return sum + (entry.leafletLayer.hasLayer(child) ? 1 : 0);
      }, 0);
      var countEl = document.querySelector('[data-sub-count="' + k + '"]');
      if (countEl) countEl.textContent = filteredCount === entry.count
        ? entry.count.toLocaleString()
        : filteredCount.toLocaleString() + "/" + entry.count.toLocaleString();
      if (map.hasLayer(entry.leafletLayer)) n += filteredCount;
    });
    document.getElementById("stat-visible").textContent = n.toLocaleString();
  }
  updateVisibleStat();

  // ---------------- State intelligence ----------------
  var stateSelect = document.getElementById("state-select");
  var stateProfileEl = document.getElementById("state-profile");
  var downloadStateButton = document.getElementById("download-state");
  var copyStateLinkButton = document.getElementById("copy-state-link");
  var stateNames = Object.keys(ATLAS.state_profiles || {}).filter(function (name) { return name !== "Nigeria"; }).sort();

  stateNames.forEach(function (name) {
    var option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    stateSelect.appendChild(option);
  });

  function formatNumber(value, maximumFractionDigits) {
    return Number(value || 0).toLocaleString(undefined, {
      maximumFractionDigits: maximumFractionDigits === undefined ? 0 : maximumFractionDigits
    });
  }

  function profileMetric(value, label) {
    return '<div class="profile-metric"><strong>' + formatNumber(value) + '</strong><span>' + escapeHtml(label) + '</span></div>';
  }

  function renderStateProfile() {
    var profileName = selectedState || "Nigeria";
    var profile = ATLAS.state_profiles[profileName];
    if (!profile) return;
    var counts = profile.counts;
    var capacity = profile.capacity;
    var peopleAccess = profile.people_access || {};
    var scopeLabel = selectedState ? "records intersecting state" : "national public-map records";
    var capacityBits = [];
    if (capacity.power_mw) capacityBits.push("<strong>" + formatNumber(capacity.power_mw, 1) + " MW</strong> reported power");
    if (capacity.minigrid_kw) capacityBits.push("<strong>" + formatNumber(capacity.minigrid_kw, 1) + " kW</strong> mini-grid");
    if (capacity.refinery_bpd) capacityBits.push("<strong>" + formatNumber(capacity.refinery_bpd) + " bpd</strong> refinery");

    stateProfileEl.innerHTML =
      '<div class="profile-title-row"><h3>' + escapeHtml(profileName) + '</h3><span>' + formatNumber(profile.mapped_records) + " " + escapeHtml(scopeLabel) + '</span></div>' +
      '<div class="profile-metrics">' +
        profileMetric(peopleAccess.worldpop_population_2025, "Population (WorldPop 2025)") +
        profileMetric(peopleAccess.settlement_count, "Settlement clusters") +
        profileMetric(peopleAccess.nightlight_population_share_pct, "Population with night-light signal (%)") +
        profileMetric(counts.power_plants, "Power-plant units") +
        profileMetric(counts.substations, "Substations") +
        profileMetric(counts.demand_centers, "Demand centres") +
        profileMetric(counts.minigrids, "Mini-grids") +
        profileMetric(counts.fields_oil + counts.fields_gas + counts.fields_mixed, "Oil & gas fields") +
        profileMetric(counts.ports, "Ports & terminals") +
      '</div>' +
      (capacityBits.length ? '<div class="capacity-strip">' + capacityBits.join(" · ") + '</div>' : "") +
      '<p class="profile-note">Population totals are WorldPop 2025 estimates. Settlement and night-light measures come from the World Bank DRE Atlas; night-light is a screening signal, not a measured household electricity-access rate. Lines and protected areas are counted where display geometry intersects the state.</p>';
    updateDownloadLabel();
  }

  function updateDownloadLabel() {
    var filtersActive = statusFilter && (statusFilter.value !== "all" || timeFilterEnabled.checked);
    var scope = selectedState ? "state" : "national";
    downloadStateButton.textContent = "Download " + (filtersActive ? "filtered " : "") + scope + " GeoJSON";
  }

  function selectState(name, fitBounds) {
    if (name && !ATLAS.state_profiles[name]) return;
    selectedState = name || "";
    stateSelect.value = selectedState;
    statesLayer.setStyle(stateStyle);
    if (selectedState && stateLayersByName[selectedState]) {
      if (fitBounds) map.fitBounds(stateLayersByName[selectedState].getBounds(), { padding: [24, 24] });
    } else if (fitBounds) {
      map.fitBounds(NIGERIA_BOUNDS);
    }
    renderStateProfile();

    var url = new URL(window.location.href);
    if (selectedState) url.searchParams.set("state", selectedState);
    else url.searchParams.delete("state");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  }

  stateSelect.addEventListener("change", function () {
    selectState(stateSelect.value, true);
  });

  function selectedGeoJSON() {
    var output = {
      type: "FeatureCollection",
      name: selectedState || "Nigeria",
      atlas_release: ATLAS.release,
      atlas_selection: {
        state: selectedState || null,
        status_group: statusFilter && statusFilter.value !== "all" ? statusFilter.value : null,
        year_cutoff: timeFilterEnabled && timeFilterEnabled.checked ? Number(yearCutoff.value) : null,
        time_semantics: ATLAS.filters.temporal.semantics
      },
      features: []
    };
    CAT_ORDER.forEach(function (catKey) {
      var category = ATLAS.layers[catKey];
      Object.keys(category.sublayers).forEach(function (subKey) {
        category.sublayers[subKey].data.features.forEach(function (sourceFeature) {
          var memberships = sourceFeature.properties._states || [];
          if (selectedState && memberships.indexOf(selectedState) === -1) return;
          if (!featureMatches(sourceFeature)) return;
          var item = JSON.parse(JSON.stringify(sourceFeature));
          item.properties.atlas_category = category.label;
          item.properties.atlas_layer = category.sublayers[subKey].label;
          item.properties.atlas_states = item.properties._states;
          delete item.properties._states;
          output.features.push(item);
        });
      });
    });
    return output;
  }

  downloadStateButton.addEventListener("click", function () {
    var data = JSON.stringify(selectedGeoJSON());
    var blob = new Blob([data], { type: "application/geo+json" });
    var href = URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    var slug = (selectedState || "nigeria").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    anchor.href = href;
    anchor.download = "nigeria-infrastructure-atlas-" + slug + "-v" + ATLAS.release.version + ".geojson";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
  });

  copyStateLinkButton.addEventListener("click", function () {
    var original = copyStateLinkButton.textContent;
    function showResult(label) {
      copyStateLinkButton.textContent = label;
      window.setTimeout(function () { copyStateLinkButton.textContent = original; }, 1400);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(window.location.href).then(function () { showResult("Copied"); });
    } else {
      var temporary = document.createElement("textarea");
      temporary.value = window.location.href;
      document.body.appendChild(temporary);
      temporary.select();
      document.execCommand("copy");
      temporary.remove();
      showResult("Copied");
    }
  });

  var initialState = new URLSearchParams(window.location.search).get("state") || "";
  selectState(initialState, Boolean(initialState));

  // ---------------- Status and time filters ----------------
  var statusFilter = document.getElementById("status-filter");
  var timeFilterEnabled = document.getElementById("time-filter-enabled");
  var timeFilterControls = document.getElementById("time-filter-controls");
  var yearCutoff = document.getElementById("year-cutoff");
  var yearCutoffOutput = document.getElementById("year-cutoff-output");
  var filterSummary = document.getElementById("filter-summary");
  var resetFiltersButton = document.getElementById("reset-filters");
  var temporal = ATLAS.filters.temporal;
  var statusCounts = ATLAS.filters.status_groups;

  Array.prototype.forEach.call(statusFilter.options, function (option) {
    if (option.value !== "all") {
      option.textContent += " (" + formatNumber(statusCounts[option.value]) + ")";
    }
  });
  yearCutoff.min = temporal.minimum_year;
  yearCutoff.max = temporal.maximum_year;
  yearCutoff.value = temporal.maximum_year;
  yearCutoffOutput.textContent = yearCutoff.value;

  function featureMatches(feature) {
    feature = feature || {};
    var props = feature.properties || {};
    if (statusFilter.value !== "all" && props._status_group !== statusFilter.value) return false;
    if (timeFilterEnabled.checked) {
      if (!props._year || Number(props._year) > Number(yearCutoff.value)) return false;
    }
    return true;
  }

  function syncFilterUrl() {
    var url = new URL(window.location.href);
    if (statusFilter.value !== "all") url.searchParams.set("status", statusFilter.value);
    else url.searchParams.delete("status");
    if (timeFilterEnabled.checked) url.searchParams.set("year", yearCutoff.value);
    else url.searchParams.delete("year");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  }

  function applyFilters(updateUrl) {
    var matchedRecords = 0;
    Object.keys(registry).forEach(function (subKey) {
      var entry = registry[subKey];
      entry.children.forEach(function (child) {
        var matches = featureMatches(child.feature);
        var included = entry.leafletLayer.hasLayer(child);
        if (matches && !included) entry.leafletLayer.addLayer(child);
        else if (!matches && included) entry.leafletLayer.removeLayer(child);
        if (matches) matchedRecords += 1;
      });
    });
    timeFilterControls.setAttribute("aria-disabled", timeFilterEnabled.checked ? "false" : "true");
    yearCutoff.disabled = !timeFilterEnabled.checked;
    yearCutoffOutput.textContent = yearCutoff.value;
    var summary = formatNumber(matchedRecords) + " records match";
    if (timeFilterEnabled.checked) summary += " · dated through " + yearCutoff.value;
    filterSummary.textContent = summary;
    updateDownloadLabel();
    updateVisibleStat();
    if (updateUrl) syncFilterUrl();
  }

  statusFilter.addEventListener("change", function () { applyFilters(true); });
  timeFilterEnabled.addEventListener("change", function () { applyFilters(true); });
  yearCutoff.addEventListener("input", function () {
    yearCutoffOutput.textContent = yearCutoff.value;
    applyFilters(true);
  });
  resetFiltersButton.addEventListener("click", function () {
    statusFilter.value = "all";
    timeFilterEnabled.checked = false;
    yearCutoff.value = temporal.maximum_year;
    applyFilters(true);
  });

  var initialParams = new URLSearchParams(window.location.search);
  var initialStatus = initialParams.get("status");
  if (initialStatus && statusCounts[initialStatus] !== undefined) statusFilter.value = initialStatus;
  var initialYear = Number(initialParams.get("year"));
  if (initialYear >= temporal.minimum_year && initialYear <= temporal.maximum_year) {
    timeFilterEnabled.checked = true;
    yearCutoff.value = initialYear;
  }
  applyFilters(false);

  // ---------------- Data catalogue ----------------
  var catalogueDialog = document.getElementById("data-catalogue");
  var catalogueButton = document.getElementById("catalogue-button");
  var catalogueClose = document.getElementById("catalogue-close");
  var catalogueSearch = document.getElementById("catalogue-search");
  var catalogueGrid = document.getElementById("catalogue-grid");
  var catalogueSummary = document.getElementById("catalogue-summary");

  function catalogueCard(item) {
    return (
      '<article class="catalogue-card">' +
        '<div class="catalogue-card-head"><h3>' + escapeHtml(item.label) + '</h3><span class="quality-badge quality-' + escapeAttr(item.quality.toLowerCase()) + '" title="' + escapeAttr(item.quality_note) + '">' + escapeHtml(item.quality) + '</span></div>' +
        '<div class="catalogue-category">' + escapeHtml(item.category_label) + ' · ' + formatNumber(item.record_count) + ' records</div>' +
        '<p class="catalogue-description">' + escapeHtml(item.description) + '</p>' +
        '<dl class="catalogue-facts">' +
          '<div><dt>Source</dt><dd>' + escapeHtml(item.source) + '</dd></div>' +
          '<div><dt>Accessed</dt><dd>' + escapeHtml(item.source_date) + '</dd></div>' +
          '<div><dt>Reuse</dt><dd>' + escapeHtml(item.license) + '</dd></div>' +
        '</dl>' +
        '<p class="quality-note"><strong>Quality ' + escapeHtml(item.quality) + ':</strong> ' + escapeHtml(item.quality_note) + '</p>' +
        '<a class="download-link" href="' + escapeAttr(item.download_url) + '" target="_blank" rel="noopener">Download processed CSV ↗</a>' +
      '</article>'
    );
  }

  function renderCatalogue(query) {
    var normalized = (query || "").trim().toLowerCase();
    var items = (ATLAS.catalogue || []).filter(function (item) {
      if (!normalized) return true;
      return [item.label, item.category_label, item.source, item.description, item.license]
        .join(" ").toLowerCase().indexOf(normalized) !== -1;
    });
    catalogueGrid.innerHTML = items.map(catalogueCard).join("");
    var records = items.reduce(function (sum, item) { return sum + item.record_count; }, 0);
    catalogueSummary.textContent = items.length + " datasets · " + formatNumber(records) + " map records";
  }

  catalogueButton.addEventListener("click", function () {
    renderCatalogue(catalogueSearch.value);
    if (catalogueDialog.showModal) catalogueDialog.showModal();
    else catalogueDialog.setAttribute("open", "");
    catalogueSearch.focus();
  });
  catalogueClose.addEventListener("click", function () { catalogueDialog.close(); });
  catalogueDialog.addEventListener("click", function (event) {
    if (event.target === catalogueDialog) catalogueDialog.close();
  });
  catalogueSearch.addEventListener("input", function () { renderCatalogue(catalogueSearch.value); });
  renderCatalogue("");

  // ---------------- Search ----------------
  var searchInput = document.getElementById("search-input");
  var searchResults = document.getElementById("search-results");
  searchInput.addEventListener("input", function () {
    var q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.classList.remove("open"); searchResults.innerHTML = ""; return; }
    var matches = allFeaturesIndex.filter(function (item) {
      return item.label.toLowerCase().indexOf(q) !== -1 && featureMatches(item.feature);
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
