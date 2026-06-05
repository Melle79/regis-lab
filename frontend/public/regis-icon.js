/**
 * Homelab Regis-Lab Custom Icon
 * Exakt nach Original-SVG, als kombinierter Pfad für HA Custom Icons
 */
(function() {

  // Kombinierter Pfad aller Logo-Elemente (skaliert auf 24x24, Ursprung 12,12)
  // Äußerer Diamant (rotiertes Quadrat)
  const OUTER_DIAMOND = "M12,3.83 L20.17,12 L12,20.17 L3.83,12 Z";
  // Innerer Diamant  
  const INNER_DIAMOND = "M12,4.96 L19.04,12 L12,19.04 L4.96,12 Z";
  // Haus (Körper + Dach + Tür als ein Pfad)
  const HOUSE = "M12,7.2 L8.07,10.69 L8.07,15.49 L15.93,15.49 L15.93,10.69 Z M8.07,10.69 L12,7.2 L15.93,10.69 M10.69,12.87 L10.69,15.49 L13.31,15.49 L13.31,12.87 Z";
  // Eckpunkte (Kreise als kleine Rauten)
  const DOTS = "M12,3.3 L12.4,3.7 L12,4.1 L11.6,3.7 Z M20.7,12 L20.3,12.4 L19.9,12 L20.3,11.6 Z M12,20.7 L11.6,20.3 L12,19.9 L12.4,20.3 Z M3.3,12 L3.7,11.6 L4.1,12 L3.7,12.4 Z";

  const FULL_PATH = [OUTER_DIAMOND, INNER_DIAMOND, HOUSE, DOTS].join(" ");

  function register() {
    if (!window.customIcons) window.customIcons = {};
    window.customIcons["regis"] = {
      getIcon: function(name) {
        return { path: FULL_PATH, viewBox: "0 0 24 24" };
      }
    };
    window.dispatchEvent(new Event("hass-custom-icons-loaded"));
  }

  register();
  window.addEventListener("hass-custom-icons", register);
  document.addEventListener("DOMContentLoaded", register);
})();
