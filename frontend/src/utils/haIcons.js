/**
 * HA Icon-Logik — bildet Domain + Device-Class + State auf MDI-Icons ab
 */

const BINARY_SENSOR_ICONS = {
  battery:          { on: 'mdi:battery-alert',        off: 'mdi:battery' },
  battery_charging: { on: 'mdi:battery-charging',     off: 'mdi:battery' },
  carbon_monoxide:  { on: 'mdi:smoke-detector-alert', off: 'mdi:smoke-detector' },
  cold:             { on: 'mdi:snowflake',             off: 'mdi:thermometer' },
  connectivity:     { on: 'mdi:check-network',         off: 'mdi:close-network' },
  door:             { on: 'mdi:door-open',             off: 'mdi:door-closed' },
  garage_door:      { on: 'mdi:garage-open',           off: 'mdi:garage' },
  gas:              { on: 'mdi:gas-cylinder',          off: 'mdi:gas-cylinder' },
  heat:             { on: 'mdi:fire',                  off: 'mdi:thermometer' },
  light:            { on: 'mdi:brightness-7',          off: 'mdi:brightness-5' },
  lock:             { on: 'mdi:lock-open',             off: 'mdi:lock' },
  moisture:         { on: 'mdi:water',                 off: 'mdi:water-off' },
  motion:           { on: 'mdi:motion-sensor',         off: 'mdi:motion-sensor-off' },
  moving:           { on: 'mdi:motion',                off: 'mdi:motion-sensor-off' },
  occupancy:        { on: 'mdi:home',                  off: 'mdi:home-outline' },
  opening:          { on: 'mdi:square',                off: 'mdi:square-outline' },
  plug:             { on: 'mdi:power-plug',            off: 'mdi:power-plug-off' },
  power:            { on: 'mdi:flash',                 off: 'mdi:flash-off' },
  presence:         { on: 'mdi:home',                  off: 'mdi:home-outline' },
  problem:          { on: 'mdi:alert-circle',          off: 'mdi:check-circle' },
  running:          { on: 'mdi:play',                  off: 'mdi:stop' },
  safety:           { on: 'mdi:alert-circle',          off: 'mdi:check-circle' },
  smoke:            { on: 'mdi:smoke-detector-alert',  off: 'mdi:smoke-detector' },
  sound:            { on: 'mdi:music-note',            off: 'mdi:music-note-off' },
  tamper:           { on: 'mdi:alert-circle',          off: 'mdi:check-circle' },
  update:           { on: 'mdi:package-up',            off: 'mdi:package' },
  vibration:        { on: 'mdi:vibrate',               off: 'mdi:vibrate-off' },
  window:           { on: 'mdi:window-open',           off: 'mdi:window-closed' },
}

const SENSOR_ICONS = {
  apparent_power:           'mdi:flash',
  aqi:                      'mdi:air-filter',
  atmospheric_pressure:     'mdi:gauge',
  battery:                  'mdi:battery',
  carbon_dioxide:           'mdi:molecule-co2',
  carbon_monoxide:          'mdi:molecule-co',
  current:                  'mdi:current-ac',
  data_rate:                'mdi:transmission-tower',
  data_size:                'mdi:database',
  date:                     'mdi:calendar',
  distance:                 'mdi:ruler',
  duration:                 'mdi:progress-clock',
  energy:                   'mdi:lightning-bolt',
  frequency:                'mdi:sine-wave',
  gas:                      'mdi:gas-cylinder',
  humidity:                 'mdi:water-percent',
  illuminance:              'mdi:brightness-5',
  moisture:                 'mdi:water-percent',
  monetary:                 'mdi:cash',
  pm1:                      'mdi:air-filter',
  pm10:                     'mdi:air-filter',
  pm25:                     'mdi:air-filter',
  power:                    'mdi:flash',
  power_factor:             'mdi:angle-acute',
  precipitation:            'mdi:weather-rainy',
  precipitation_intensity:  'mdi:weather-pouring',
  pressure:                 'mdi:gauge',
  reactive_power:           'mdi:flash',
  signal_strength:          'mdi:wifi',
  sound_pressure:           'mdi:microphone',
  speed:                    'mdi:speedometer',
  temperature:              'mdi:thermometer',
  timestamp:                'mdi:clock',
  voltage:                  'mdi:sine-wave',
  volume:                   'mdi:car-coolant-level',
  water:                    'mdi:water',
  weight:                   'mdi:weight',
  wind_speed:               'mdi:weather-windy',
}

const COVER_ICONS = {
  awning:  { open: 'mdi:awning-outline',         closed: 'mdi:awning' },
  blind:   { open: 'mdi:blinds-open',            closed: 'mdi:blinds' },
  curtain: { open: 'mdi:curtains',               closed: 'mdi:curtains-closed' },
  door:    { open: 'mdi:door-open',              closed: 'mdi:door-closed' },
  garage:  { open: 'mdi:garage-open',            closed: 'mdi:garage' },
  gate:    { open: 'mdi:gate-open',              closed: 'mdi:gate' },
  shade:   { open: 'mdi:roller-shade',           closed: 'mdi:roller-shade-closed' },
  shutter: { open: 'mdi:window-shutter-open',    closed: 'mdi:window-shutter' },
  window:  { open: 'mdi:window-open',            closed: 'mdi:window-closed' },
}

const DOMAIN_ICONS = {
  alarm_control_panel: 'mdi:shield-home',
  assist_satellite:    'mdi:assistant',
  automation:          'mdi:robot',
  binary_sensor:       'mdi:radiobox-marked',
  button:              'mdi:gesture-tap-button',
  calendar:            'mdi:calendar',
  camera:              'mdi:cctv',
  climate:             'mdi:thermostat',
  counter:             'mdi:counter',
  cover:               'mdi:window-shutter',
  device_tracker:      'mdi:map-marker',
  event:               'mdi:bell',
  fan:                 'mdi:fan',
  group:               'mdi:google-circles-communities',
  humidifier:          'mdi:air-humidifier',
  input_boolean:       'mdi:toggle-switch-outline',
  input_button:        'mdi:gesture-tap-button',
  input_datetime:      'mdi:calendar-clock',
  input_number:        'mdi:ray-vertex',
  input_select:        'mdi:format-list-bulleted',
  input_text:          'mdi:form-textbox',
  lawn_mower:          'mdi:robot-mower',
  light:               'mdi:lightbulb',
  lock:                'mdi:lock',
  media_player:        'mdi:speaker',
  number:              'mdi:ray-vertex',
  person:              'mdi:account',
  remote:              'mdi:remote',
  scene:               'mdi:palette',
  schedule:            'mdi:calendar-clock',
  script:              'mdi:script-text',
  select:              'mdi:format-list-bulleted',
  sensor:              'mdi:gauge',
  siren:               'mdi:bell',
  switch:              'mdi:toggle-switch',
  timer:               'mdi:timer-outline',
  todo:                'mdi:clipboard-list',
  update:              'mdi:package-up',
  vacuum:              'mdi:robot-vacuum',
  valve:               'mdi:pipe-valve',
  water_heater:        'mdi:water-boiler',
  weather:             'mdi:weather-partly-cloudy',
}

const WEATHER_ICONS = {
  'clear-night':     'mdi:weather-night',
  'cloudy':          'mdi:weather-cloudy',
  'exceptional':     'mdi:alert-circle-outline',
  'fog':             'mdi:weather-fog',
  'hail':            'mdi:weather-hail',
  'lightning':       'mdi:weather-lightning',
  'lightning-rainy': 'mdi:weather-lightning-rainy',
  'partlycloudy':    'mdi:weather-partly-cloudy',
  'pouring':         'mdi:weather-pouring',
  'rainy':           'mdi:weather-rainy',
  'snowy':           'mdi:weather-snowy',
  'snowy-rainy':     'mdi:weather-snowy-rainy',
  'sunny':           'mdi:weather-sunny',
  'windy':           'mdi:weather-windy',
  'windy-variant':   'mdi:weather-windy-variant',
}

export function getEntityIcon(entity, overrideIcon = null) {
  if (overrideIcon) return overrideIcon
  if (entity.attributes?.icon) return entity.attributes.icon

  const domain = entity.entity_id.split('.')[0]
  const state  = entity.state
  const dc     = entity.attributes?.device_class

  switch (domain) {
    case 'light':
      return state === 'on' ? 'mdi:lightbulb' : 'mdi:lightbulb-outline'

    case 'switch':
    case 'input_boolean':
      return state === 'on' ? 'mdi:toggle-switch' : 'mdi:toggle-switch-off-outline'

    case 'binary_sensor': {
      const icons = BINARY_SENSOR_ICONS[dc]
      if (icons) return state === 'on' ? icons.on : icons.off
      return state === 'on' ? 'mdi:radiobox-marked' : 'mdi:radiobox-blank'
    }

    case 'sensor': {
      if (dc && SENSOR_ICONS[dc]) return SENSOR_ICONS[dc]
      const unit = entity.attributes?.unit_of_measurement
      if (unit === '°C' || unit === '°F') return 'mdi:thermometer'
      if (unit === '%' && dc === 'humidity') return 'mdi:water-percent'
      if (unit === 'W' || unit === 'kW')    return 'mdi:flash'
      if (unit === 'Wh' || unit === 'kWh')  return 'mdi:lightning-bolt'
      if (unit === 'V')  return 'mdi:sine-wave'
      if (unit === 'A')  return 'mdi:current-ac'
      if (unit === 'lx') return 'mdi:brightness-5'
      if (unit === 'ppm') return 'mdi:molecule-co2'
      return 'mdi:gauge'
    }

    case 'cover': {
      const icons = COVER_ICONS[dc] || { open: 'mdi:window-shutter-open', closed: 'mdi:window-shutter' }
      return state === 'open' ? icons.open : icons.closed
    }

    case 'fan':
      return state === 'on' ? 'mdi:fan' : 'mdi:fan-off'

    case 'media_player': {
      const mt = entity.attributes?.media_content_type
      if (mt === 'music') return 'mdi:music'
      if (mt === 'tvshow' || mt === 'video') return 'mdi:television-play'
      return state === 'playing' ? 'mdi:speaker-play' : 'mdi:speaker'
    }

    case 'climate': {
      const hvac = entity.attributes?.hvac_action
      if (hvac === 'heating') return 'mdi:fire'
      if (hvac === 'cooling') return 'mdi:snowflake'
      if (state === 'off') return 'mdi:thermostat-auto'
      return 'mdi:thermostat'
    }

    case 'lock':
      return state === 'locked' ? 'mdi:lock' : 'mdi:lock-open'

    case 'alarm_control_panel':
      if (state === 'disarmed')   return 'mdi:shield-off'
      if (state === 'armed_away') return 'mdi:shield-lock'
      if (state === 'armed_home') return 'mdi:shield-home'
      if (state === 'triggered')  return 'mdi:shield-alert'
      return 'mdi:shield-home'

    case 'vacuum':
      return state === 'cleaning' ? 'mdi:robot-vacuum' : 'mdi:robot-vacuum-alert'

    case 'person':
    case 'device_tracker':
      return state === 'home' ? 'mdi:home-account' : 'mdi:account'

    case 'weather':
      return WEATHER_ICONS[state] || 'mdi:weather-partly-cloudy'
  }

  return DOMAIN_ICONS[domain] || 'mdi:help-circle'
}

export function getEntityColor(entity) {
  const domain = entity.entity_id.split('.')[0]
  const state  = entity.state
  const dc     = entity.attributes?.device_class

  if (state === 'unavailable' || state === 'unknown') return 'var(--muted)'

  if (state === 'on') {
    if (domain === 'light')   return 'var(--amber)'
    if (['motion','occupancy','presence'].includes(dc)) return 'var(--amber)'
    if (['smoke','gas','carbon_monoxide','moisture'].includes(dc)) return 'var(--red)'
    return 'var(--green)'
  }

  if (domain === 'alarm_control_panel') {
    if (state === 'triggered') return 'var(--red)'
    if (state === 'disarmed')  return 'var(--green)'
    return 'var(--amber)'
  }

  if (domain === 'climate') {
    const hvac = entity.attributes?.hvac_action
    if (hvac === 'heating') return 'var(--amber)'
    if (hvac === 'cooling') return 'var(--accent)'
  }

  if (dc === 'battery') {
    const level = parseInt(state)
    if (level < 20) return 'var(--red)'
    if (level < 50) return 'var(--amber)'
    return 'var(--green)'
  }

  return 'var(--muted)'
}
