#include <Adafruit_NeoPixel.h>

// Define the pin where the ARGB signal is connected
#define ARGB_PIN 6

// Define the number of LEDs (fans * LEDs per fan)
// RI-C12C-S fans typically have 12 LEDs each
#define NUM_LEDS 24  // 2 fans * 12 LEDs each

// Create NeoPixel object
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, ARGB_PIN, NEO_GRB + NEO_KHZ800);

// Serial command buffer
String inputString = "";
bool stringComplete = false;

// Current effect state
enum Effect { NONE, RAINBOW, BREATHE, CHASE, STATIC };
Effect currentEffect = NONE;
uint32_t currentColor = 0;
int currentBrightness = 100;

// Effect timing variables
unsigned long lastUpdate = 0;
uint16_t rainbowCounter = 0;
uint16_t breatheCounter = 0;
uint8_t chasePosition = 0;

void setup() {
  // Initialize serial communication with error checking
  Serial.begin(9600);  // Using standard 9600 baud for better compatibility
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }
  
  // Clear any garbage from serial buffer
  while (Serial.available() > 0) {
    Serial.read();
  }
  
  // Initialize NeoPixel strip
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  strip.setBrightness(currentBrightness);
  
  printWelcomeMessage();
}

void loop() {
  // Check for serial commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Handle continuous effects - they run forever until changed
  handleEffects();
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    // Only accept printable ASCII characters
    if (isPrintable(inChar)) {
      inputString += inChar;
    }
    
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) {
        stringComplete = true;
        return; // Exit immediately to process the command
      }
    }
  }
}

void printWelcomeMessage() {
  Serial.println("\n=== ARGB Fan Controller ===");
  Serial.println("Connected to 2 RI-C12C-S fans (24 LEDs total)");
  Serial.println("Pin: D6, Baud: 9600");
  Serial.println("Type 'help' for available commands");
  Serial.println("============================\n");
}

void processCommand(String command) {
  command.trim();
  command.toLowerCase();
  
  if (command.length() == 0) return;
  
  // Split command into parts
  int firstSpace = command.indexOf(' ');
  String cmd = firstSpace == -1 ? command : command.substring(0, firstSpace);
  String args = firstSpace == -1 ? "" : command.substring(firstSpace + 1);
  
  if (cmd == "set") {
    handleSetCommand(args);
  } 
  else if (cmd == "effect") {
    handleEffectCommand(args);
  }
  else if (cmd == "get") {
    handleGetCommand(args);
  }
  else if (cmd == "test") {
    runTestPattern();
  }
  else if (cmd == "save") {
    Serial.println("OK: Settings saved");
  }
  else if (cmd == "reset") {
    resetToDefaults();
  }
  else if (cmd == "help" || cmd == "?") {
    printHelp();
  }
  else if (cmd == "clear" || cmd == "cls") {
    // Simulate clearing by sending newlines
    for (int i = 0; i < 50; i++) {
      Serial.println();
    }
    printWelcomeMessage();
  }
  else {
    Serial.println("ERROR: Unknown command '" + cmd + "'");
    Serial.println("Type 'help' for available commands");
  }
}

void printHelp() {
  Serial.println("\n=== Available Commands ===");
  Serial.println("set color <r> <g> <b>        - Set solid color (0-255 each)");
  Serial.println("set color #RRGGBB            - Set solid color (hex code)");
  Serial.println("set brightness <value>       - Set brightness (0-255)");
  Serial.println("effect rainbow               - Continuous rainbow effect");
  Serial.println("effect breathe <r> <g> <b>   - Continuous breathing effect");
  Serial.println("effect breathe #RRGGBB       - Continuous breathing (hex)");
  Serial.println("effect chase <r> <g> <b>     - Continuous chase effect");
  Serial.println("effect chase #RRGGBB         - Continuous chase (hex)");
  Serial.println("effect static                - Static color (no animation)");
  Serial.println("effect off                   - Turn off all LEDs");
  Serial.println("get status                   - Show current settings");
  Serial.println("get help                     - Show this help");
  Serial.println("test                         - Run LED test pattern");
  Serial.println("save                         - Save current settings");
  Serial.println("reset                        - Reset to defaults");
  Serial.println("clear                        - Clear screen");
  Serial.println("");
  Serial.println("Hex Code Examples:");
  Serial.println("  set color #ff0000          // Red");
  Serial.println("  set color #00ff00          // Green");
  Serial.println("  set color #0000ff          // Blue");
  Serial.println("  set color #ffffff          // White");
  Serial.println("  effect breathe #ff00ff     // Magenta breathing");
  Serial.println("============================\n");
}

void handleSetCommand(String args) {
  int spacePos = args.indexOf(' ');
  String subcmd = spacePos == -1 ? args : args.substring(0, spacePos);
  String params = spacePos == -1 ? "" : args.substring(spacePos + 1);
  
  if (subcmd == "color") {
    if (params.startsWith("#")) {
      // Hex code format
      uint32_t hexColor = parseHexColor(params);
      if (hexColor != 0xFFFFFFFF) { // Valid hex color
        currentColor = hexColor;
        setAllPixels(currentColor);
        strip.show();
        currentEffect = STATIC;
        
        // Convert back to hex for confirmation
        char hexStr[8];
        sprintf(hexStr, "#%06X", (unsigned int)(currentColor & 0xFFFFFF));
        Serial.println("OK: Color set to " + String(hexStr));
      } else {
        Serial.println("ERROR: Invalid hex format. Use #RRGGBB");
        Serial.println("Example: set color #ff0000");
      }
    } else {
      // RGB format
      int r, g, b;
      if (sscanf(params.c_str(), "%d %d %d", &r, &g, &b) == 3) {
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        currentColor = strip.Color(r, g, b);
        setAllPixels(currentColor);
        strip.show();
        currentEffect = STATIC;
        
        Serial.println("OK: Color set to RGB(" + String(r) + ", " + String(g) + ", " + String(b) + ")");
      } else {
        Serial.println("ERROR: Usage: set color <r> <g> <b> OR set color #RRGGBB");
        Serial.println("Examples: set color 255 0 0 OR set color #ff0000");
      }
    }
  }
  else if (subcmd == "brightness") {
    int brightness;
    if (sscanf(params.c_str(), "%d", &brightness) == 1) {
      brightness = constrain(brightness, 0, 255);
      currentBrightness = brightness;
      strip.setBrightness(brightness);
      strip.show();
      Serial.println("OK: Brightness set to " + String(brightness));
    } else {
      Serial.println("ERROR: Usage: set brightness <value>");
      Serial.println("Example: set brightness 150");
    }
  }
  else {
    Serial.println("ERROR: Unknown set command '" + subcmd + "'");
  }
}

void handleEffectCommand(String args) {
  int spacePos = args.indexOf(' ');
  String effect = spacePos == -1 ? args : args.substring(0, spacePos);
  String params = spacePos == -1 ? "" : args.substring(spacePos + 1);
  
  if (effect == "rainbow") {
    currentEffect = RAINBOW;
    Serial.println("OK: Rainbow effect started (runs until changed)");
  }
  else if (effect == "breathe") {
    if (params.startsWith("#")) {
      // Hex code format
      uint32_t hexColor = parseHexColor(params);
      if (hexColor != 0xFFFFFFFF) {
        currentColor = hexColor;
        currentEffect = BREATHE;
        breatheCounter = 0;
        
        char hexStr[8];
        sprintf(hexStr, "#%06X", (unsigned int)(currentColor & 0xFFFFFF));
        Serial.println("OK: Breathing effect started with " + String(hexStr));
      } else {
        Serial.println("ERROR: Invalid hex format. Use #RRGGBB");
      }
    } else {
      // RGB format
      int r, g, b;
      if (sscanf(params.c_str(), "%d %d %d", &r, &g, &b) == 3) {
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        currentColor = strip.Color(r, g, b);
        currentEffect = BREATHE;
        breatheCounter = 0;
        Serial.println("OK: Breathing effect started with RGB(" + String(r) + ", " + String(g) + ", " + String(b) + ")");
      } else {
        Serial.println("ERROR: Usage: effect breathe <r> <g> <b> OR effect breathe #RRGGBB");
        Serial.println("Examples: effect breathe 255 0 0 OR effect breathe #ff0000");
      }
    }
  }
  else if (effect == "chase") {
    if (params.startsWith("#")) {
      // Hex code format
      uint32_t hexColor = parseHexColor(params);
      if (hexColor != 0xFFFFFFFF) {
        currentColor = hexColor;
        currentEffect = CHASE;
        chasePosition = 0;
        
        char hexStr[8];
        sprintf(hexStr, "#%06X", (unsigned int)(currentColor & 0xFFFFFF));
        Serial.println("OK: Chase effect started with " + String(hexStr));
      } else {
        Serial.println("ERROR: Invalid hex format. Use #RRGGBB");
      }
    } else {
      // RGB format
      int r, g, b;
      if (sscanf(params.c_str(), "%d %d %d", &r, &g, &b) == 3) {
        r = constrain(r, 0, 255);
        g = constrain(g, 0, 255);
        b = constrain(b, 0, 255);
        
        currentColor = strip.Color(r, g, b);
        currentEffect = CHASE;
        chasePosition = 0;
        Serial.println("OK: Chase effect started with RGB(" + String(r) + ", " + String(g) + ", " + String(b) + ")");
      } else {
        Serial.println("ERROR: Usage: effect chase <r> <g> <b> OR effect chase #RRGGBB");
        Serial.println("Examples: effect chase 0 0 255 OR effect chase #0000ff");
      }
    }
  }
  else if (effect == "static") {
    currentEffect = STATIC;
    setAllPixels(currentColor);
    strip.show();
    Serial.println("OK: Static color mode");
  }
  else if (effect == "off") {
    currentEffect = NONE;
    strip.clear();
    strip.show();
    Serial.println("OK: All LEDs turned off");
  }
  else {
    Serial.println("ERROR: Unknown effect '" + effect + "'");
  }
}

uint32_t parseHexColor(String hexStr) {
  // Remove # if present
  if (hexStr.startsWith("#")) {
    hexStr = hexStr.substring(1);
  }
  
  // Check if valid hex string (6 characters)
  if (hexStr.length() != 6) {
    return 0xFFFFFFFF; // Invalid
  }
  
  // Convert to uppercase for consistency
  hexStr.toUpperCase();
  
  // Check if all characters are valid hex digits
  for (int i = 0; i < 6; i++) {
    char c = hexStr[i];
    if (!((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F'))) {
      return 0xFFFFFFFF; // Invalid character
    }
  }
  
  // Parse hex string
  long hexValue = strtol(hexStr.c_str(), NULL, 16);
  
  // Extract RGB components
  uint8_t r = (hexValue >> 16) & 0xFF;
  uint8_t g = (hexValue >> 8) & 0xFF;
  uint8_t b = hexValue & 0xFF;
  
  return strip.Color(r, g, b);
}

void handleGetCommand(String args) {
  if (args == "status") {
    Serial.println("\n=== Current Status ===");
    Serial.println("Brightness: " + String(currentBrightness));
    Serial.print("Effect: ");
    switch(currentEffect) {
      case NONE: Serial.println("OFF"); break;
      case RAINBOW: Serial.println("Rainbow (continuous)"); break;
      case BREATHE: Serial.println("Breathing (continuous)"); break;
      case CHASE: Serial.println("Chase (continuous)"); break;
      case STATIC: Serial.println("Static Color"); break;
    }
    
    // Show current color in both RGB and hex format
    uint8_t r = (currentColor >> 16) & 0xFF;
    uint8_t g = (currentColor >> 8) & 0xFF;
    uint8_t b = currentColor & 0xFF;
    char hexStr[8];
    sprintf(hexStr, "#%02X%02X%02X", r, g, b);
    
    Serial.println("Current Color: RGB(" + String(r) + ", " + String(g) + ", " + String(b) + ") " + String(hexStr));
    Serial.println("LEDs: " + String(NUM_LEDS));
    Serial.println("=====================");
  }
  else if (args == "help") {
    printHelp();
  }
  else {
    Serial.println("ERROR: Unknown get command '" + args + "'");
  }
}

void handleEffects() {
  unsigned long currentMillis = millis();
  
  // Update effects every 30ms for smooth animation
  if (currentMillis - lastUpdate < 30) return;
  lastUpdate = currentMillis;
  
  switch(currentEffect) {
    case RAINBOW:
      for(int i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + rainbowCounter) & 255));
      }
      strip.show();
      rainbowCounter = (rainbowCounter + 1) % 256;
      break;
      
    case BREATHE:
      {
        float intensity = (exp(sin(breatheCounter * 0.1)) - 0.3678) / 2.3504;
        uint32_t color = dimColor(currentColor, intensity);
        setAllPixels(color);
        strip.show();
        breatheCounter++;
      }
      break;
      
    case CHASE:
      strip.clear();
      // Create a chase with 4 LEDs
      for(int i = 0; i < 4; i++) {
        int pos = (chasePosition + i) % strip.numPixels();
        strip.setPixelColor(pos, currentColor);
      }
      strip.show();
      chasePosition = (chasePosition + 1) % strip.numPixels();
      break;
      
    case STATIC:
    case NONE:
      // No continuous updates needed - effect persists until changed
      break;
  }
}

void setAllPixels(uint32_t color) {
  for(int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
  }
}

uint32_t dimColor(uint32_t color, float intensity) {
  uint8_t r = (uint8_t)(color >> 16);
  uint8_t g = (uint8_t)(color >> 8);
  uint8_t b = (uint8_t)color;
  
  r = (uint8_t)(r * intensity);
  g = (uint8_t)(g * intensity);
  b = (uint8_t)(b * intensity);
  
  return strip.Color(r, g, b);
}

void runTestPattern() {
  Serial.println("Running test pattern...");
  Effect previousEffect = currentEffect;
  currentEffect = NONE;
  
  // Test individual colors using hex codes
  String testColors[] = {
    "#ff0000", // Red
    "#00ff00", // Green
    "#0000ff", // Blue
    "#ffffff", // White
    "#ff00ff", // Magenta
    "#ffff00", // Yellow
    "#00ffff"  // Cyan
  };
  
  for (String hexColor : testColors) {
    uint32_t color = parseHexColor(hexColor);
    setAllPixels(color);
    strip.show();
    Serial.println("Testing: " + hexColor);
    delay(800);
  }
  
  // Restore previous effect
  currentEffect = previousEffect;
  if (currentEffect != NONE) {
    Serial.println("Restoring previous effect...");
  }
  Serial.println("Test pattern completed");
}

void resetToDefaults() {
  currentEffect = NONE;
  currentBrightness = 100;
  currentColor = strip.Color(255, 255, 255); // White
  strip.setBrightness(currentBrightness);
  strip.clear();
  strip.show();
  Serial.println("OK: Reset to defaults (white)");
}

// Input a value 0 to 255 to get a color value.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}