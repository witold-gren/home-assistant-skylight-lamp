/*
 * skylight-lamp-card - Lovelace card for the Skylight Lamp integration.
 *
 * Looks like the manual page of the SLcontrol app: mode buttons, the colour
 * palette (rows A-F, columns 1-10, drawn in the app's colours) and the
 * intensity slider. One file, no build step, ES2017.
 *
 *   type: custom:skylight-lamp-card
 *   entity: light.entriq60      # optional, the first Skylight lamp by default
 *   title: Akwarium             # optional, false hides the header
 *
 * The other entities (mode, colour, intensity) are found on the same device.
 */
(function () {
  "use strict";

  var CARD_VERSION = "0.1.0";
  var DOMAIN = "skylight_lamp";
  var ROWS = "ABCDEF";

  // Same as COLOUR_RGB in colours.py (how SLcontrol draws the colours).
  var COLOURS = [
    "bac4fa", "c9d7fc", "d5e7fd", "e5f5fe", "f2fef7", "edfee7", "ecfed5", "ebfec7", "e8fe98", "d9fe58",
    "bab7fa", "c6c9fb", "d2d8fc", "e6ecfd", "fefefe", "fcffed", "faffd9", "fcfec7", "fdff99", "ebfe53",
    "b7a4f9", "c8c1fa", "d7d1fb", "ece5fd", "fdf3fb", "fdf5ec", "fef9ce", "fdf3c6", "fdf297", "ffff54",
    "c191f8", "c9b8fa", "dac6fb", "eedefd", "fbe8f8", "fceee3", "fbebcd", "fbe5c5", "fae495", "fcee4f",
    "cc85f8", "ceadfa", "debffb", "efd2fc", "f9dafc", "fae2eb", "f9dad3", "f8d7cf", "f8d8a6", "f8d748",
    "d26bf7", "db9af9", "ebb7fa", "f6c5fb", "f7cffc", "f8d3f3", "f7cbe2", "f6c7d8", "f6c8b3", "f5c242"
  ];

  var MODES = ["schedule", "manual", "demo", "off"];

  var TEXTS = {
    en: { intensity: "Intensity", noLamp: "No Skylight lamp found", unavailable: "Lamp unavailable" },
    pl: { intensity: "Intensywność", noLamp: "Nie znaleziono lampy Skylight", unavailable: "Lampa niedostępna" }
  };

  function key(index) {
    return ROWS.charAt(Math.floor(index / 10)).toLowerCase() + ((index % 10) + 1);
  }

  var STYLE =
    ":host{display:block}" +
    "ha-card{padding:16px}" +
    ".head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:12px}" +
    ".title{font-size:1.2em;font-weight:500}" +
    ".mode{color:var(--secondary-text-color);font-size:.9em}" +
    ".modes{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:14px}" +
    ".modes button{border:1px solid var(--divider-color);border-radius:8px;padding:8px 4px;cursor:pointer;" +
    "background:var(--secondary-background-color);color:var(--primary-text-color);font:inherit;font-size:.9em;" +
    "touch-action:manipulation}" +
    ".modes button.on{background:var(--primary-color);border-color:var(--primary-color);" +
    "color:var(--text-primary-color,#fff)}" +
    ".grid{display:grid;grid-template-columns:16px repeat(10,1fr);gap:3px;align-items:center}" +
    ".lbl{font-size:.75em;color:var(--secondary-text-color);text-align:center}" +
    ".cell{height:30px;border-radius:4px;cursor:pointer;border:2px solid transparent;box-sizing:border-box;" +
    "padding:0;touch-action:manipulation}" +
    ".cell.sel{border-color:var(--primary-text-color);box-shadow:0 0 0 1px var(--card-background-color,#fff) inset}" +
    ".grid.inactive .cell.sel{border-style:dashed}" +
    ".name{display:flex;align-items:center;gap:8px;margin:12px 0 4px;min-height:22px}" +
    ".swatch{width:22px;height:22px;border-radius:4px;border:1px solid var(--divider-color);flex:none}" +
    ".slider{display:flex;align-items:center;gap:10px;margin-top:10px}" +
    ".slider span{font-size:.9em;color:var(--secondary-text-color);min-width:44px;text-align:right}" +
    ".slider input{flex:1;accent-color:var(--primary-color)}" +
    ".msg{color:var(--secondary-text-color)}";

  function findEntities(hass, lightId) {
    var entities = hass.entities || {};
    if (!lightId) {
      lightId = Object.keys(entities).filter(function (id) {
        return id.indexOf("light.") === 0 && entities[id].platform === DOMAIN;
      })[0];
    }
    var light = lightId && entities[lightId];
    if (!light) return null;
    var found = { light: lightId };
    Object.keys(entities).forEach(function (id) {
      var entry = entities[id];
      if (entry.platform === DOMAIN && entry.device_id === light.device_id && entry.translation_key) {
        found[entry.translation_key] = id;
      }
    });
    return found;
  }

  // The class is built only at registration time, from the CURRENT
  // window.HTMLElement - see registerCard().
  function createCardClass() {
    return class SkylightLampCard extends window.HTMLElement {
      setConfig(config) {
        this._config = config || {};
        this._built = false;
        if (this._hass) this._render();
      }

      set hass(hass) {
        this._hass = hass;
        this._render();
      }

      _t(name) {
        var lang = (this._hass && this._hass.language || "en").split("-")[0];
        return (TEXTS[lang] || TEXTS.en)[name];
      }

      _call(domain, service, entityId, data) {
        var payload = Object.assign({ entity_id: entityId }, data || {});
        this._hass.callService(domain, service, payload);
      }

      _build() {
        var self = this;
        if (!this.shadowRoot) this.attachShadow({ mode: "open" });
        var root = this.shadowRoot;
        root.innerHTML = "";
        var style = document.createElement("style");
        style.textContent = STYLE;
        root.appendChild(style);
        var card = document.createElement("ha-card");
        root.appendChild(card);
        this._card = card;

        var head = document.createElement("div");
        head.className = "head";
        this._title = document.createElement("div");
        this._title.className = "title";
        this._mode = document.createElement("div");
        this._mode.className = "mode";
        head.appendChild(this._title);
        head.appendChild(this._mode);
        card.appendChild(head);
        this._head = head;

        var modes = document.createElement("div");
        modes.className = "modes";
        this._modeButtons = {};
        MODES.forEach(function (option) {
          var button = document.createElement("button");
          button.addEventListener("click", function () {
            self._call("select", "select_option", self._ids.mode, { option: option });
          });
          modes.appendChild(button);
          self._modeButtons[option] = button;
        });
        card.appendChild(modes);

        var grid = document.createElement("div");
        grid.className = "grid";
        grid.appendChild(document.createElement("span"));
        for (var c = 1; c <= 10; c++) {
          var col = document.createElement("span");
          col.className = "lbl";
          col.textContent = c;
          grid.appendChild(col);
        }
        this._cells = [];
        for (var r = 0; r < 6; r++) {
          var row = document.createElement("span");
          row.className = "lbl";
          row.textContent = ROWS.charAt(r);
          grid.appendChild(row);
          for (var i = r * 10; i < r * 10 + 10; i++) {
            var cell = document.createElement("button");
            cell.className = "cell";
            cell.style.background = "#" + COLOURS[i];
            cell.addEventListener("click", this._pick.bind(this, key(i)));
            grid.appendChild(cell);
            this._cells.push(cell);
          }
        }
        card.appendChild(grid);
        this._grid = grid;

        var name = document.createElement("div");
        name.className = "name";
        this._swatch = document.createElement("span");
        this._swatch.className = "swatch";
        this._name = document.createElement("span");
        name.appendChild(this._swatch);
        name.appendChild(this._name);
        card.appendChild(name);

        var slider = document.createElement("div");
        slider.className = "slider";
        this._sliderLabel = document.createElement("label");
        this._slider = document.createElement("input");
        this._slider.type = "range";
        this._slider.min = "0";
        this._slider.max = "100";
        this._slider.step = "1";
        this._sliderValue = document.createElement("span");
        this._slider.addEventListener("input", function () {
          self._dragging = true;
          self._sliderValue.textContent = self._slider.value + " %";
        });
        this._slider.addEventListener("change", function () {
          self._dragging = false;
          self._call("number", "set_value", self._ids.intensity, { value: Number(self._slider.value) });
        });
        slider.appendChild(this._sliderLabel);
        slider.appendChild(this._slider);
        slider.appendChild(this._sliderValue);
        card.appendChild(slider);

        this._built = true;
      }

      _pick(option) {
        if (this._ids && this._ids.colour) {
          this._call("select", "select_option", this._ids.colour, { option: option });
        }
      }

      _message(text) {
        if (!this.shadowRoot) this.attachShadow({ mode: "open" });
        this._built = false;
        this.shadowRoot.innerHTML = "<style>" + STYLE + "</style><ha-card><div class=\"msg\"></div></ha-card>";
        this.shadowRoot.querySelector(".msg").textContent = text;
      }

      _render() {
        var hass = this._hass;
        if (!hass || !this._config) return;
        var ids = findEntities(hass, this._config.entity);
        if (!ids || !ids.mode || !ids.colour) {
          this._message(this._t("noLamp"));
          return;
        }
        this._ids = ids;
        var light = hass.states[ids.light];
        var mode = hass.states[ids.mode];
        var colour = hass.states[ids.colour];
        var intensity = ids.intensity && hass.states[ids.intensity];
        if (!light || !mode || !colour || mode.state === "unavailable") {
          this._message(this._t("unavailable"));
          return;
        }
        if (!this._built) this._build();

        var title = this._config.title;
        this._head.style.display = title === false ? "none" : "";
        this._title.textContent = title || light.attributes.friendly_name || "";
        this._mode.textContent = hass.formatEntityState ? hass.formatEntityState(mode) : mode.state;

        var self = this;
        MODES.forEach(function (option) {
          var button = self._modeButtons[option];
          button.textContent = hass.formatEntityState ? hass.formatEntityState(mode, option) : option;
          button.className = mode.state === option ? "on" : "";
        });

        var selected = -1;
        this._cells.forEach(function (cell, index) {
          var option = key(index);
          cell.title = hass.formatEntityState ? hass.formatEntityState(colour, option) : option.toUpperCase();
          cell.className = option === colour.state ? "cell sel" : "cell";
          if (option === colour.state) selected = index;
        });
        this._grid.className = mode.state === "manual" ? "grid" : "grid inactive";
        this._swatch.style.background = selected >= 0 ? "#" + COLOURS[selected] : "transparent";
        this._name.textContent = hass.formatEntityState ? hass.formatEntityState(colour) : colour.state;

        this._sliderLabel.textContent = this._t("intensity");
        this._slider.disabled = !intensity;
        if (intensity && !this._dragging) {
          var value = Math.round(Number(intensity.state));
          if (!isNaN(value)) {
            this._slider.value = String(value);
            this._sliderValue.textContent = value + " %";
          }
        }
      }

      getCardSize() {
        return 6;
      }

      getGridOptions() {
        return { columns: 12, min_columns: 6 };
      }

      static getStubConfig() {
        return {};
      }
    };
  }

  // HA 2026.9.4+ loads extra modules (add_extra_js_url) in the FIRST script of
  // the page, before the frontend installs its scoped CustomElementRegistry
  // polyfill (replaces window.customElements and window.HTMLElement). A card
  // defined right away lands in the old registry: "Custom element doesn't
  // exist". So wait until the frontend has defined <home-assistant>, then
  // build the class and register it. Older HA: same path, or after 30 s.
  function registerCard() {
    var registry = window.customElements;
    if (registry.get("skylight-lamp-card")) return;
    registry.define("skylight-lamp-card", createCardClass());
    window.customCards = window.customCards || [];
    window.customCards.push({
      type: "skylight-lamp-card",
      name: "Skylight Lamp",
      description: "Mode, colour palette and intensity of a Skylight lamp, like in SLcontrol.",
      documentationURL: "https://github.com/witold-gren/home-assistant-skylight-lamp"
    });
    console.info("%c SKYLIGHT-LAMP-CARD %c " + CARD_VERSION + " ", "background:#2e7d32;color:#fff", "");
  }

  (function waitForFrontend(attempt) {
    if (window.customElements.get("home-assistant") || attempt >= 600) {
      registerCard();
      return;
    }
    setTimeout(function () { waitForFrontend(attempt + 1); }, 50);
  })(0);
})();
