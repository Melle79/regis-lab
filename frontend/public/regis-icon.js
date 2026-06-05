/**
 * Regis-Lab Custom Icon Provider for Home Assistant
 */
(function() {
  const ICON_PATH = "M12,2 L21.5,12 L12,22 L2.5,12 Z M12,4.5 L19,12 L12,19.5 L5,12 Z M12,7 L8,10.5 L8,16.5 L16,16.5 L16,10.5 Z M8,10.5 L12,7 L16,10.5 M10.5,13 L10.5,16.5 L13.5,16.5 L13.5,13 Z";

  function register() {
    if (!window.customIcons) window.customIcons = {};
    window.customIcons["regis"] = {
      getIcon: async function(name) {
        return { path: ICON_PATH };
      }
    };
    // HA Custom Icons Event
    window.dispatchEvent(new CustomEvent("hass-custom-icons-loaded"));
    console.log("[Regis-Lab] Custom icon registered");
  }

  // Mehrfach versuchen
  register();
  window.addEventListener("hass-custom-icons", register);
  window.addEventListener("load", register);
  setTimeout(register, 1000);
  setTimeout(register, 3000);
})();
