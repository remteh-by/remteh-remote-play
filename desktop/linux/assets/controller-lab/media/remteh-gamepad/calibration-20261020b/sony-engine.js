import {preserveOriginal,requireFlashPermit,permanentWrite,createBaselineGate,confirmPowerCycle} from './service-mode.js';
/*! DualShock Tools — MIT, Copyright (c) 2024 the_al. RemTeh headless adapter. See LICENSE.txt. */
/**
* Race a promise against a timeout. USB feature/output transfers on a genuine
* controller complete in milliseconds; some clones ignore reports they don't
* implement, leaving the transfer to hang until the OS timeout (seconds).
* @param {Promise} promise - The transfer promise
* @param {number} timeoutMs - Reject after this many ms (0 disables)
* @param {string} label - Description used in the timeout error
*/
async function withTimeout(promise, timeoutMs, label) {
  if (!timeoutMs) return await promise;
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer);
  }
}

/**
* Base Controller class that provides common functionality for all controller types
*/
class BaseController {
  constructor(device) {
    this.device = device;
    this.model = "undefined"; // to be set by subclasses
    this.finetuneMaxValue; // to be set by subclasses
  }

  getModel() {
    return this.model;
  }

  /**
  * Get the underlying HID device
  * @returns {HIDDevice} The HID device
  */
  getDevice() {
    return this.device;
  }

  getInputConfig() {
    throw new Error('getInputConfig() must be implemented by subclass');
  }

  /**
   * Get the maximum value for finetune data
   * @returns {number} Maximum value for finetune adjustments
   */
  getFinetuneMaxValue() {
    if(!this.finetuneMaxValue) throw new Error('getFinetuneMaxValue() must be implemented by subclass');
    return this.finetuneMaxValue;
  }

  getNumberOfSticks() {
    return 0;
  }

  /**
  * Set input report handler
  * @param {Function} handler Input report handler function
  */
  setInputReportHandler(handler) {
    this.device.oninputreport = handler;
  }

  /**
  * Allocate request buffer with proper size based on device feature reports
  * @param {number} id Report ID
  * @param {Array} data Data array to include in the request
  * @returns {Uint8Array} Allocated request buffer
  */
  alloc_req(id, data = []) {
    // Windows can split a report into several items/collections. reportCount
    // belongs to one item and is a count of fields, not a byte length.
    const collections = [...(this.device.collections ?? [])];
    const reports = [];
    for (let i = 0; i < collections.length; i++) {
      const collection = collections[i];
      collections.push(...(collection.children ?? []));
      reports.push(...(collection.featureReports ?? []).filter(report => report.reportId === id));
    }
    const lengths = reports.map(report => Math.ceil((report.items ?? []).reduce((bits, item) =>
      bits + (item.reportSize ?? 8) * item.reportCount, 0) / 8));
    const length = lengths.length ? Math.max(...lengths) : data.length;
    if (!Number.isInteger(length) || length < data.length || length > 4096) {
      throw new Error('hid_report_descriptor_invalid');
    }
    const out = new Uint8Array(length);
    out.set(data);
    return out;
  }

  /**
  * Send feature report to device
  * @param {number} reportId Report ID
  * @param {ArrayBuffer|Array} data Data to send (if Array, will be processed through allocReq)
  */
  async sendFeatureReport(reportId, data) {
    // If data is an array, use allocReq to create proper buffer
    if (Array.isArray(data)) {
      data = this.alloc_req(reportId, data);
    }

    try {
      return await withTimeout(this.device.sendFeatureReport(reportId, data), 5000, 'sendFeatureReport');
    } catch (error) {
      // HID doesn't throw proper Errors with stack (stack is "name: message") so generate a new stack here
      throw new Error(error.stack);
    }
  }

  /**
  * Receive feature report from device.
  * @param {number} reportId Report ID
  * @param {number} timeoutMs Optional: reject if no response within this many
  *   ms. Off by default; used for probing reports a clone may ignore (which
  *   would otherwise hang the USB control transfer until the OS timeout).
  */
  async receiveFeatureReport(reportId, timeoutMs = 5000) {
    return await withTimeout(
      this.device.receiveFeatureReport(reportId),
      timeoutMs,
      `receiveFeatureReport(0x${reportId.toString(16)})`);
  }

  /**
  * Close the HID device connection
  */
  async close() {
    if (this.device?.opened) {
      await this.device.close();
    }
  }

  /**
  * Get the serial number of the device
  * @returns {Promise<string>} The device serial number
  */
  async getSerialNumber() {
    throw new Error('getSerialNumber() must be implemented by subclass');
  }

  // Abstract methods that must be implemented by subclasses
  async getInfo() {
    throw new Error('getInfo() must be implemented by subclass');
  }

  async flash(progressCallback = null) {
    requireFlashPermit(this);
    throw new Error('flash() must be implemented by subclass');
  }

  async reset() {
    throw new Error('reset() must be implemented by subclass');
  }

  async nvsLock() {
    throw new Error('nvsLock() must be implemented by subclass');
  }

  async nvsUnlock() {
    throw new Error('nvsUnlock() must be implemented by subclass');
  }

  async calibrateSticksBegin() {
    throw new Error('calibrateSticksBegin() must be implemented by subclass');
  }

  async calibrateSticksEnd() {
    throw new Error('calibrateSticksEnd() must be implemented by subclass');
  }

  async calibrateSticksSample() {
    throw new Error('calibrateSticksSample() must be implemented by subclass');
  }

  async calibrateRangeBegin() {
    throw new Error('calibrateRangeBegin() must be implemented by subclass');
  }

  async calibrateRangeEnd() {
    throw new Error('calibrateRangeEnd() must be implemented by subclass');
  }

  parseDeviceSpecificInputs(data) {
    return {};
  }

  parseBatteryStatus(data) {
    throw new Error('parseBatteryStatus() must be implemented by subclass');
  }
  
  async setAdaptiveTrigger(left, right) {
    // Default no-op implementation for controllers that don't support adaptive triggers
    return { success: true, message: "This controller does not support adaptive triggers" };
  }

  async setVibration(heavyLeft = 0, lightRight = 0) {
    // Default no-op implementation for controllers that don't support vibration
    return { success: true, message: "This controller does not support vibration" };
  }

  async setAdaptiveTriggerPreset(config) {
    // Default no-op implementation for controllers that don't support adaptive trigger presets
    return { success: true, message: "This controller does not support adaptive trigger presets" };
  }

  async setSpeakerTone(output = 'speaker') {
    // Default no-op implementation for controllers that don't support speaker audio
    if (callback) callback({ success: true, message: "This controller does not support speaker audio" });
    return { success: true, message: "This controller does not support speaker audio" };
  }

  async resetLights() {
    // Default no-op implementation for controllers that don't support controllable lights
    return { success: true, message: "This controller does not support controllable lights" };
  }

  async setMuteLed(mode) {
    // Default no-op implementation for controllers that don't support mute LED
    return { success: true, message: "This controller does not support mute LED" };
  }

  async setLightbarColor(r, g, b) {
    // Default no-op implementation for controllers that don't support lightbar colors
    return { success: true, message: "This controller does not support lightbar colors" };
  }

  async setPlayerIndicator(pattern) {
    // Default no-op implementation for controllers that don't support player indicators
    return { success: true, message: "This controller does not support player indicators" };
  }

  /**
   * Get the list of supported quick tests for this controller
   * @returns {Array<string>} Array of supported test types
   */
  getSupportedQuickTests() {
    // Default implementation - supports all tests
    return ['usb', 'buttons', 'trackpad', 'imu', 'adaptive', 'haptic', 'lights', 'speaker', 'headphone', 'microphone'];
  }
}

/**
* Utility functions for DualShock controller operations
*/

/**
* Sleep for specified milliseconds
* @param {number} ms Milliseconds to sleep
* @returns {Promise} Promise that resolves after the specified time
*/
async function sleep(ms) {
  await new Promise(r => setTimeout(r, ms));
}

/**
* Convert buffer to hexadecimal string
* @param {ArrayBuffer} buffer Buffer to convert
* @returns {string} Hexadecimal string representation
*/
function buf2hex(buffer) {
  return [...new Uint8Array(buffer)].map(x => x.toString(16).padStart(2, '0')).join('');
}

/**
* Convert decimal to 16-bit hexadecimal string
* @param {number} i Decimal number
* @returns {string} 4-character uppercase hex string
*/
function dec2hex(i) {
  return (i + 0x10000).toString(16).substr(-4).toUpperCase();
}

/**
* Convert decimal to 32-bit hexadecimal string
* @param {number} i Decimal number
* @returns {string} 8-character uppercase hex string
*/
function dec2hex32(i) {
  return (i + 0x100000000).toString(16).substr(-8).toUpperCase();
}

/**
* Convert decimal to 8-bit hexadecimal string
* @param {number} i Decimal number
* @returns {string} 2-character uppercase hex string
*/
function dec2hex8(i) {
  return (i + 0x100).toString(16).substr(-2).toUpperCase();
}

/**
* Format MAC address from DataView
* @returns {string} Formatted MAC address (XX:XX:XX:XX:XX:XX)
*/
function format_mac_from_view(view, start_index_inclusive) {
  const bytes = [];
  for (let i = 0; i < 6; i++) {
    const idx = start_index_inclusive + (5 - i);
    bytes.push(dec2hex8(view.getUint8(idx, false)));
  }
  return bytes.join(":");
}

/**
* Reverse a string (for ASCII strings only, not UTF)
* @param {string} s String to reverse
* @returns {string} Reversed string
*/
function reverse_str(s) {
  return s.split('').reverse().join('');
}

let la = () => {};

const l = text => text;

// DS4 Button mapping configuration
const DS4_BUTTON_MAP = [
  { name: 'up', byte: 4, mask: 0x0 }, // Dpad handled separately
  { name: 'right', byte: 4, mask: 0x1 },
  { name: 'down', byte: 4, mask: 0x2 },
  { name: 'left', byte: 4, mask: 0x3 },
  { name: 'square', byte: 4, mask: 0x10, svg: 'Square' },
  { name: 'cross', byte: 4, mask: 0x20, svg: 'Cross' },
  { name: 'circle', byte: 4, mask: 0x40, svg: 'Circle' },
  { name: 'triangle', byte: 4, mask: 0x80, svg: 'Triangle' },
  { name: 'l1', byte: 5, mask: 0x01, svg: 'L1' },
  { name: 'l2', byte: 5, mask: 0x04, svg: 'L2' }, // analog handled separately
  { name: 'r1', byte: 5, mask: 0x02, svg: 'R1' },
  { name: 'r2', byte: 5, mask: 0x08, svg: 'R2' }, // analog handled separately
  { name: 'create', byte: 5, mask: 0x10, svg: 'Create' },
  { name: 'options', byte: 5, mask: 0x20, svg: 'Options' },
  { name: 'l3', byte: 5, mask: 0x40, svg: 'L3' },
  { name: 'r3', byte: 5, mask: 0x80, svg: 'R3' },
  { name: 'ps', byte: 6, mask: 0x01, svg: 'PS' },
  { name: 'touchpad', byte: 6, mask: 0x02, svg: 'Trackpad' },
  // No mute button on DS4
];

// DS4 Input processing configuration
const DS4_INPUT_CONFIG = {
  buttonMap: DS4_BUTTON_MAP,
  dpadByte: 4,
  l2AnalogByte: 7,
  r2AnalogByte: 8,
  imuOffset: 12, // bytes 9-10 timestamp, 11 battery, 12-17 gyro, 18-23 accel
  touchpadOffset: 34,
};

// DS4 Output Report Constants
const DS4_OUTPUT_REPORT = {
  USB_REPORT_ID: 0x05,
  BT_REPORT_ID: 0x11,
};

const DS4_VALID_FLAG0 = {
  RUMBLE: 0x01,           // Bit 0 for rumble motors
  LED: 0x02,              // Bit 1 for LED control
  LED_BLINK: 0x04,        // Bit 2 for LED blink control
};

// Basic DS4 Output Structure for vibration and LED control
class DS4OutputStruct {
  constructor(currentState = null) {
    // Create a 32-byte buffer for DS4 output report (USB)
    this.buffer = new ArrayBuffer(31);
    this.view = new DataView(this.buffer);

    // Control flags
    this.validFlag0 = currentState?.validFlag0 || 0;
    this.validFlag1 = currentState?.validFlag1 || 0;

    // Vibration motors
    this.rumbleRight = currentState?.rumbleRight || 0;
    this.rumbleLeft = currentState?.rumbleLeft || 0;

    // LED control
    this.ledRed = currentState?.ledRed || 0;
    this.ledGreen = currentState?.ledGreen || 0;
    this.ledBlue = currentState?.ledBlue || 0;

    // LED timing
    this.ledFlashOn = currentState?.ledFlashOn || 0;
    this.ledFlashOff = currentState?.ledFlashOff || 0;
  }

  // Pack the data into the output buffer
  pack() {
    // Based on DS4 output report structure
    // Byte 0-2: Valid flags and padding
    this.view.setUint8(0, this.validFlag0);
    this.view.setUint8(1, this.validFlag1);
    this.view.setUint8(2, 0x00);

    // Byte 3-4: Rumble motors
    this.view.setUint8(3, this.rumbleRight);
    this.view.setUint8(4, this.rumbleLeft);

    // Bytes 5-7: LED RGB
    this.view.setUint8(5, this.ledRed);
    this.view.setUint8(6, this.ledGreen);
    this.view.setUint8(7, this.ledBlue);

    // Bytes 8-9: LED flash timing
    this.view.setUint8(8, this.ledFlashOn);
    this.view.setUint8(9, this.ledFlashOff);

    return this.buffer;
  }
}

/**
* DualShock 4 Controller implementation
*/
class DS4Controller extends BaseController {
  constructor(device) {
    super(device);
    this.model = "DS4";

    // Initialize current output state to track controller settings
    this.currentOutputState = {
      validFlag0: 0,
      validFlag1: 0,
      rumbleRight: 0,
      rumbleLeft: 0,
      ledRed: 0,
      ledGreen: 0,
      ledBlue: 0,
      ledFlashOn: 0,
      ledFlashOff: 0,
    };
  }

  getInputConfig() {
    return DS4_INPUT_CONFIG;
  }

  async getSerialNumber() {
    return await this.getBdAddr();
  }

  async getInfo() {
    // Device-only: collect info and return a common structure; do not touch the DOM
    try {
      let deviceTypeText = l("unknown");
      let is_clone = false;

      const view = await this.receiveFeatureReport(0xa3);

      const cmd = view.getUint8(0, true);

      if(cmd != 0xa3 || view.buffer.byteLength < 49) {
        if(view.buffer.byteLength != 49) {
          deviceTypeText = l("clone");
          is_clone = true;
        }
      }

      const k1 = new TextDecoder().decode(view.buffer.slice(1, 0x10)).replace(/\0/g, '');
      const k2 = new TextDecoder().decode(view.buffer.slice(0x10, 0x20)).replace(/\0/g, '');

      const hw_ver_major = view.getUint16(0x21, true);
      const hw_ver_minor = view.getUint16(0x23, true);
      const sw_ver_major = view.getUint32(0x25, true);
      const sw_ver_minor = view.getUint16(0x25+4, true);
      try {
        if(!is_clone) {
          // If this feature report succeeds, it's an original device. A
          // genuine controller answers instantly; a clone that ignores it
          // would otherwise hang, so use a short timeout.
          await this.receiveFeatureReport(0x81, 1000);
          deviceTypeText = l("original");
        }
      } catch(e) {
        la("clone");
        is_clone = true;
        deviceTypeText = l("clone");
      }

      const hw_version = `${dec2hex(hw_ver_major)}:${dec2hex(hw_ver_minor)}`;
      const sw_version = `${dec2hex(sw_ver_major)}:${dec2hex(sw_ver_minor)}`;
      const infoItems = [
        { key: l("Build Date"), value: `${k1} ${k2}`, cat: "fw" },
        { key: l("HW Version"), value: hw_version, cat: "hw" },
        { key: l("SW Version"), value: sw_version, cat: "fw" },
        { key: l("Device Type"), value: deviceTypeText, cat: "hw", severity: is_clone ? 'danger' : undefined },
      ];

      const board_model = this.hwToBoardModel(hw_ver_minor);

      // Clones don't implement these reports, so reading them only stacks up
      // more timeouts - skip them once the device is known to be a clone.
      let bd_addr = null;
      let nv = null;
      if(!is_clone) {
        bd_addr = await this.getBdAddr();

        // Add Board Model (UI will append the info icon)
        infoItems.push({ key: l("Board Model"), value: board_model, cat: "hw", addInfoIcon: 'board', copyable: true });
        infoItems.push({ key: l("Bluetooth Address"), value: bd_addr, cat: "hw" });

        nv = await this.queryNvStatus();
      }

      const rare = this.isRare(hw_ver_minor);
      const disable_bits = is_clone ? 1 : 0; // 1: clone

      la("ds4_get_info", { hw_version, board_model, bd_addr, is_clone });  // Collect Bluetooth address for analytics

      return { ok: true, infoItems, nv, disable_bits, rare };
    } catch(error) {
      // Return error but do not touch DOM
      return { ok: false, error, disable_bits: 1 };
    }
  }

  async flash(progressCallback = null) {
    requireFlashPermit(this);
    try {
      const unlockRes = await this.nvsUnlock();
      if (!unlockRes?.ok) throw new Error('NVS unlock failed');
      const lockRes = await this.nvsLock();
      if(!lockRes.ok) throw (lockRes.error || new Error("NVS lock failed"));

      return { success: true, message: l("Changes saved successfully") };
    } catch(error) {
      throw new Error(l("Error while saving changes"), { cause: error });
    }
  }

  async reset() {
    try {
      await this.sendFeatureReport(0xa0, [4,1,0]);
    } catch(error) {
    }
  }

  async nvsLock() {
    // la("ds4_nvlock");
    try {
      await this.sendFeatureReport(0xa0, [10,1,0]);
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async nvsUnlock() {
    // la("ds4_nvunlock");
    try {
      await this.sendFeatureReport(0xa0, [10,2,0x3e,0x71,0x7f,0x89]);
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async getBdAddr() {
    const view = await this.receiveFeatureReport(0x12);
    return format_mac_from_view(view, 1);
  }

  async calibrateRangeBegin() {
    try {
      // Begin
      await this.sendFeatureReport(0x90, [1,1,2]);
      await sleep(200);

      // Assert
      const data = await this.receiveFeatureReport(0x91);
      const data2 = await this.receiveFeatureReport(0x92);
      const [d1, d2] = [data, data2].map(v => v.buffer.byteLength == 4 ? v.getUint32(0, false) : undefined);
      if(d1 != 0x91010201 || d2 != 0x920102ff) {
        la("ds4_calibrate_range_begin_failed", {"d1": d1, "d2": d2});
        return {
          ok: false,
          error: new Error(`Stick range calibration begin failed: ${d1}, ${d2}`),
          code: 1, d1, d2
        };
      }
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateRangeEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x90, [2,1,2]);
      await sleep(200);

      const data = await this.receiveFeatureReport(0x91);
      const data2 = await this.receiveFeatureReport(0x92);
      const [d1, d2] = [data, data2].map(v => v.getUint32(0, false));
      if(d1 != 0x91010202 || d2 != 0x92010201) {
        la("ds4_calibrate_range_end_failed", {"d1": d1, "d2": d2});
        return { ok: false, code: 3, d1, d2 };
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateSticksBegin() {
    try {
      // Begin
      await this.sendFeatureReport(0x90, [1,1,1]);
      await sleep(200);

      // Assert
      const data = await this.receiveFeatureReport(0x91);
      const data2 = await this.receiveFeatureReport(0x92);
      const [d1, d2] = [data, data2].map(v => v.buffer.byteLength == 4 ? v.getUint32(0, false) : undefined);
      if(d1 != 0x91010101 || d2 != 0x920101ff) {
        la("ds4_calibrate_sticks_begin_failed", {"d1": d1, "d2": d2});
        return {
          ok: false,
          error: new Error(`Stick center calibration begin failed: ${d1}, ${d2}`),
          code: 1, d1, d2,
        };
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateSticksSample() {
    try {
      // Sample
      await this.sendFeatureReport(0x90, [3,1,1]);
      await sleep(200);

      // Assert
      const data = await this.receiveFeatureReport(0x91);
      const data2 = await this.receiveFeatureReport(0x92);
      if(data.getUint32(0, false) != 0x91010101 || data2.getUint32(0, false) != 0x920101ff) {
        const [d1, d2] = [data, data2].map(v => dec2hex32(v.getUint32(0, false)));
        la("ds4_calibrate_sticks_sample_failed", {"d1": d1, "d2": d2});
        return { ok: false, code: 2, d1, d2 };
      }
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateSticksEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x90, [2,1,1]);
      await sleep(200);

      const data = await this.receiveFeatureReport(0x91);
      const data2 = await this.receiveFeatureReport(0x92);
      if(data.getUint32(0, false) != 0x91010102 || data2.getUint32(0, false) != 0x92010101) {
        const [d1, d2] = [data, data2].map(v => dec2hex32(v.getUint32(0, false)));
        la("ds4_calibrate_sticks_end_failed", {"d1": d1, "d2": d2});
        return { ok: false, code: 3, d1, d2 };
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async queryNvStatus() {
    try {
      await this.sendFeatureReport(0x08, [0xff,0, 12]);
      const data = await this.receiveFeatureReport(0x11);
      const ret = data.getUint8(1, false);
      const res = { device: 'ds4', code: ret };
      switch(ret) {
        case 1:
          return { ...res, status: 'locked', locked: true, mode: 'temporary' };
        case 0:
          return { ...res, status: 'unlocked', locked: false, mode: 'permanent' };
        default:
          return { ...res, status: 'unknown', locked: null };
      }
    } catch (error) {
      return { device: 'ds4', status: 'error', locked: null, code: 2, error };
    }
  }

  hwToBoardModel(hw_ver) {
    const a = hw_ver >> 8;
    if(a == 0x31) {
      return "JDM-001";
    } else if(a == 0x43) {
      return "JDM-011";
    } else if(a == 0x54) {
      return "JDM-030";
    } else if(a >= 0x64 && a <= 0x74) {
      return "JDM-040";
    } else if((a > 0x80 && a < 0x84) || a == 0x93) {
      return "JDM-020";
    } else if(a == 0xa4 || a == 0x90 || a == 0xa0) {
      return "JDM-050";
    } else if(a == 0xb0) {
      return "JDM-055 (Scuf?)";
    } else if(a == 0xb4) {
      return "JDM-055";
    } else {
      if(this.isRare(hw_ver))
        return "WOW!";
      return l("Unknown");
    }
  }

  isRare(hw_ver) {
    const a = hw_ver >> 8;
    const b = a >> 4;
    return ((b == 7 && a > 0x74) || (b == 9 && a != 0x93 && a != 0x90));
  }

  /**
  * Parse DS4 battery status from input data
  */
  parseBatteryStatus(data) {
    const bat = data.getUint8(29); // DS4 battery byte is at position 29

    // DS4: bat_data = low 4 bits, bat_status = bit 4
    const bat_data = bat & 0x0f;
    const bat_status = (bat >> 4) & 1;
    const cable_connected = bat_status === 1;

    let charge_level = 0;
    let is_charging = false;
    let is_error = false;

    if (cable_connected) {
      if (bat_data < 10) {
        charge_level = Math.min(bat_data * 10 + 5, 100);
        is_charging = true;
      } else if (bat_data === 10) {
        charge_level = 100;
        is_charging = true;
      } else if (bat_data === 11) {
        charge_level = 100; // Fully charged
      } else {
        charge_level = 0;
        is_error = true;
      }
    } else {
      // On battery power
      charge_level = bat_data < 10 ? bat_data * 10 + 5 : 100;
    }

    return { charge_level, cable_connected, is_charging, is_error };
  }

  /**
   * Send output report to the DS4 controller
   * @param {ArrayBuffer} data - The output report data
   */
  async sendOutputReport(data, reason = "") {
    if (!this.device?.opened) {
      throw new Error('Device is not opened');
    }
    try {
      console.log(`Sending output report${ reason ? ` to ${reason}` : '' }:`, DS4_OUTPUT_REPORT.USB_REPORT_ID, buf2hex(data));
      await withTimeout(this.device.sendReport(DS4_OUTPUT_REPORT.USB_REPORT_ID, new Uint8Array(data)), 5000, 'sendReport');
    } catch (error) {
      throw new Error(`Failed to send output report: ${error.message}`);
    }
  }

  /**
   * Update the current output state with values from an OutputStruct
   * @param {DS4OutputStruct} outputStruct - The output structure to copy state from
   */
  updateCurrentOutputState(outputStruct) {
    this.currentOutputState = { ...outputStruct };
  }

  /**
   * Get a copy of the current output state
   * @returns {Object} A copy of the current output state
   */
  getCurrentOutputState() {
    return { ...this.currentOutputState };
  }

  /**
   * Initialize the current output state when the controller is first connected.
   * This method sets up reasonable defaults for the DS4 controller.
   */
  async initializeCurrentOutputState() {
    try {
      // Reset all output state to known defaults
      this.currentOutputState = {
        ...this.getCurrentOutputState(),
        validFlag0: DS4_VALID_FLAG0.RUMBLE | DS4_VALID_FLAG0.LED,
        ledRed: 0,
        ledGreen: 0,
        ledBlue: 255, // Default to blue
        ledFlashOn: 0,
        ledFlashOff: 0
      };

      // Send a "reset" output report to ensure the controller is in a known state
      const resetOutputStruct = new DS4OutputStruct(this.currentOutputState);
      await this.sendOutputReport(resetOutputStruct.pack(), 'init default states');

      // Update our state to reflect what we just sent
      this.updateCurrentOutputState(resetOutputStruct);
    } catch (error) {
      console.warn("Failed to initialize DS4 output state:", error);
      // Even if the reset fails, we still have the default state initialized
    }
  }

  /**
   * Set vibration motors for haptic feedback
   * @param {number} heavyLeft - Left motor intensity (0-255)
   * @param {number} lightRight - Right motor intensity (0-255)
   */
  async setVibration(heavyLeft = 0, lightRight = 0) {
    try {
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS4OutputStruct({
        ...this.currentOutputState,
        rumbleLeft: Math.max(0, Math.min(255, heavyLeft)),
        rumbleRight: Math.max(0, Math.min(255, lightRight)),
        validFlag0: validFlag0 | DS4_VALID_FLAG0.RUMBLE,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set vibration');
      outputStruct.validFlag0 &= ~DS4_VALID_FLAG0.RUMBLE;

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);

      return { success: true, message: "Vibration set successfully" };
    } catch (error) {
      throw new Error("Failed to set vibration", { cause: error });
    }
  }

  /**
   * Set lightbar color
   * @param {number} red - Red component (0-255)
   * @param {number} green - Green component (0-255)
   * @param {number} blue - Blue component (0-255)
   */
  async setLightbarColor(red = 0, green = 0, blue = 0) {
    try {
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS4OutputStruct({
        ...this.currentOutputState,
        ledRed: Math.max(0, Math.min(255, red)),
        ledGreen: Math.max(0, Math.min(255, green)),
        ledBlue: Math.max(0, Math.min(255, blue)),
        validFlag0: validFlag0 | DS4_VALID_FLAG0.LED,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set lightbar color');
      outputStruct.validFlag0 &= ~DS4_VALID_FLAG0.LED;

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set lightbar color", { cause: error });
    }
  }

  /** Turn the DS4 lightbar fully off in one output report. */
  async resetLights() {
    try {
      const outputStruct = new DS4OutputStruct({
        ...this.currentOutputState,
        ledRed: 0,
        ledGreen: 0,
        ledBlue: 0,
        ledFlashOn: 0,
        ledFlashOff: 0,
        validFlag0: this.currentOutputState.validFlag0 | DS4_VALID_FLAG0.LED | DS4_VALID_FLAG0.LED_BLINK,
      });
      await this.sendOutputReport(outputStruct.pack(), 'reset lights');
      outputStruct.validFlag0 &= ~(DS4_VALID_FLAG0.LED | DS4_VALID_FLAG0.LED_BLINK);
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to reset lights", { cause: error });
    }
  }

  /**
   * Set lightbar blink pattern
   * @param {number} red - Red component (0-255)
   * @param {number} green - Green component (0-255)
   * @param {number} blue - Blue component (0-255)
   * @param {number} flashOn - On duration in deciseconds (0-255)
   * @param {number} flashOff - Off duration in deciseconds (0-255)
   */
  async setLightbarBlink(red = 0, green = 0, blue = 0, flashOn = 0, flashOff = 0) {
    try {
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS4OutputStruct({
        ...this.currentOutputState,
        ledRed: Math.max(0, Math.min(255, red)),
        ledGreen: Math.max(0, Math.min(255, green)),
        ledBlue: Math.max(0, Math.min(255, blue)),
        ledFlashOn: Math.max(0, Math.min(255, flashOn)),
        ledFlashOff: Math.max(0, Math.min(255, flashOff)),
        validFlag0: validFlag0 | DS4_VALID_FLAG0.LED | DS4_VALID_FLAG0.LED_BLINK,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set lightbar blink');
      outputStruct.validFlag0 &= ~(DS4_VALID_FLAG0.LED | DS4_VALID_FLAG0.LED_BLINK);

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set lightbar blink", { cause: error });
    }
  }

  /**
   * Set speaker tone for audio output through the controller's headphone jack
   * Note: DS4 only supports playing sound through headphones connected to the controller.
   * The built-in speaker is not supported. DS4 audio is a standard USB audio device,
   * not controlled via HID output reports.
   * @param {string} output - Audio output destination: "headphones" only (throws error if "speaker")
   * @throws {Error} If output is set to "speaker" (not supported on DS4)
   */
  async setSpeakerTone(output = "speaker") {
    // Throw error if trying to use the built-in speaker
    if (output === "speaker") {
      throw new Error("DS4 does not support playing sound through the built-in speaker. Only 'headphones' output is supported.");
    }

    // DS4 speaker works as a standard USB audio device (class-compliant)
    // It cannot be controlled through HID output reports like DS5

    // Create Web Audio Context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    // Try to get microphone permission to see device labels
    let hasPermission = false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      hasPermission = true;
    } catch (error) {
      throw new Error('Microphone permission required to enumerate audio devices', { cause: error });
    }

    // Check if we have access to audio devices and setSinkId support
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioOutputs = devices.filter(device => device.kind === 'audiooutput');

      // Look for DualShock 4 audio device
      const ds4AudioDevice = audioOutputs.find(device =>
        device.label && /wireless controller|dualshock|sony/i.test(device.label)
      );

      // Create audio elements for tone generation
      const oscillator = audioContext.createOscillator();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, audioContext.currentTime);

      // Configure volume envelope (fade in/out to avoid clicks)
      // Use max volume for better audibility
      const gainNode = audioContext.createGain();
      gainNode.gain.setValueAtTime(0, audioContext.currentTime);
      gainNode.gain.linearRampToValueAtTime(1, audioContext.currentTime + 0.05);
      gainNode.gain.linearRampToValueAtTime(1, audioContext.currentTime + 0.5);
      gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.25);

      // Connect audio graph
      oscillator.connect(gainNode);

      let audioElement = null;

      // If DS4 audio device is found and setSinkId is supported, route to it
      if (ds4AudioDevice && typeof HTMLMediaElement !== 'undefined' && HTMLMediaElement.prototype.setSinkId) {
        try {
          // Create a MediaStreamDestination to capture the audio
          const streamDestination = audioContext.createMediaStreamDestination();
          gainNode.connect(streamDestination);

          // Create an audio element to play the stream
          audioElement = new Audio();
          audioElement.autoplay = false;
          audioElement.volume = 1.0; // Max volume

          // Set the audio output to the DS4 speaker BEFORE setting srcObject
          await audioElement.setSinkId(ds4AudioDevice.deviceId);
          audioElement.srcObject = streamDestination.stream;

          // Play the audio element FIRST
          await audioElement.play();

          // THEN start the oscillator (so the stream is already being consumed)
          oscillator.start();
          oscillator.stop(audioContext.currentTime + 0.8);
        } catch (error) {
          throw new Error('Could not set DS4 as audio sink', { cause: error });
        }
      }

      // Clean up audio context and element after tone completes
      setTimeout(() => {
        if (audioElement) {
          audioElement.pause();
          audioElement.srcObject = null;
        }
        if (audioContext.state !== 'closed') {
          audioContext.close();
        }
      }, 1000);
    } else {
      throw new Error('WebRTC getUserMedia API or mediaDevices enumeration not available.');
    }
  }

  getNumberOfSticks() {
    return 2;
  }

  /**
   * Get the list of supported quick tests for DS4 controller
   * DS4 does not support adaptive triggers, speaker, or microphone
   * @returns {Array<string>} Array of supported test types
   */
  getSupportedQuickTests() {
    return ['usb', 'buttons', 'imu', 'trackpad', 'haptic', 'lights', 'headphone'];
  }
}

// DS5 Button mapping configuration
const DS5_BUTTON_MAP = [
  { name: 'up', byte: 7, mask: 0x0 }, // Dpad handled separately
  { name: 'right', byte: 7, mask: 0x1 },
  { name: 'down', byte: 7, mask: 0x2 },
  { name: 'left', byte: 7, mask: 0x3 },
  { name: 'square', byte: 7, mask: 0x10, svg: 'Square' },
  { name: 'cross', byte: 7, mask: 0x20, svg: 'Cross' },
  { name: 'circle', byte: 7, mask: 0x40, svg: 'Circle' },
  { name: 'triangle', byte: 7, mask: 0x80, svg: 'Triangle' },
  { name: 'l1', byte: 8, mask: 0x01, svg: 'L1' },
  { name: 'l2', byte: 4, mask: 0xff }, // analog handled separately
  { name: 'r1', byte: 8, mask: 0x02, svg: 'R1' },
  { name: 'r2', byte: 5, mask: 0xff }, // analog handled separately
  { name: 'create', byte: 8, mask: 0x10, svg: 'Create' },
  { name: 'options', byte: 8, mask: 0x20, svg: 'Options' },
  { name: 'l3', byte: 8, mask: 0x40, svg: 'L3' },
  { name: 'r3', byte: 8, mask: 0x80, svg: 'R3' },
  { name: 'ps', byte: 9, mask: 0x01, svg: 'PS' },
  { name: 'touchpad', byte: 9, mask: 0x02, svg: 'Trackpad' },
  { name: 'mute', byte: 9, mask: 0x04, svg: 'Mute' },
];

// DS5 Input processing configuration
const DS5_INPUT_CONFIG = {
  buttonMap: DS5_BUTTON_MAP,
  dpadByte: 7,
  l2AnalogByte: 4,
  r2AnalogByte: 5,
  imuOffset: 15,
  touchpadOffset: 32,
};

// DS5 Adaptive Trigger Effect Modes
const DS5_TRIGGER_EFFECT_MODE = {
  OFF: 0x05,           // Documented HID "off" effect
  RESISTANCE: 0x21,    // Documented zone feedback effect
  TRIGGER: 0x25,       // Documented weapon/single-trigger effect
  VIBRATION: 0x26,     // Documented zone vibration effect
};

// DS5 Output Report Constants
const DS5_OUTPUT_REPORT = {
  USB_REPORT_ID: 0x02,
  BT_REPORT_ID: 0x31,
};

const DS5_VALID_FLAG0 = {
  RIGHT_VIBRATION: 0x01,  // Bit 0 for right vibration motor
  LEFT_VIBRATION: 0x02,   // Bit 1 for left vibration motor
  LEFT_TRIGGER: 0x04,     // Bit 2 for left adaptive trigger
  RIGHT_TRIGGER: 0x08,    // Bit 3 for right adaptive trigger
  HEADPHONE_VOLUME: 0x10, // Bit 4 for headphone volume control
  SPEAKER_VOLUME: 0x20,   // Bit 5 for speaker volume control
  MIC_VOLUME: 0x40,       // Bit 6 for microphone volume control
  AUDIO_CONTROL: 0x80,    // Bit 7 for audio control
};

const DS5_VALID_FLAG1 = {
  MUTE_LED: 0x01,          // Bit 0 for mute LED control
  POWER_SAVE_MUTE: 0x02,   // Bit 1 for power-save mute control
  LIGHTBAR_COLOR: 0x04,    // Bit 2 for lightbar color control
  RESERVED_BIT_3: 0x08,    // Bit 3 (reserved)
  PLAYER_INDICATOR: 0x10,  // Bit 4 for player indicator LED control
  HAPTIC_LOW_PASS_FILTER: 0x20,
  VIBRATION_ATTENUATION: 0x40,
  AUDIO_CONTROL2: 0x80,     // Bit 7 enables the secondary audio-control byte
};

const DS5_VALID_FLAG2 = {
  LED_BRIGHTNESS: 0x01,
  LIGHTBAR_SETUP: 0x02,
};

// Basic DS5 Output Structure for adaptive trigger control
class DS5OutputStruct {
  constructor(currentState = null) {
    // Create a 47-byte buffer for DS5 output report (USB)
    this.buffer = new ArrayBuffer(47);
    this.view = new DataView(this.buffer);

    // Control flags
    this.validFlag0 = currentState.validFlag0 || 0;
    this.validFlag1 = currentState.validFlag1 || 0;
    this.validFlag2 = currentState.validFlag2 || 0;

    // Vibration motors
    this.bcVibrationRight = currentState.bcVibrationRight || 0;
    this.bcVibrationLeft = currentState.bcVibrationLeft || 0;

    // Audio control
    this.headphoneVolume = currentState.headphoneVolume || 0;
    this.speakerVolume = currentState.speakerVolume || 0;
    this.micVolume = currentState.micVolume || 0;
    this.audioControl = currentState.audioControl || 0;
    this.audioControl2 = currentState.audioControl2 || 0;

    // LED and indicator control
    this.muteLedControl = currentState.muteLedControl || 0;
    this.powerSaveMuteControl = currentState.powerSaveMuteControl || 0;
    this.lightbarSetup = currentState.lightbarSetup || 0;
    this.ledBrightness = currentState.ledBrightness || 0;
    this.playerIndicator = currentState.playerIndicator || 0;
    this.ledCRed = currentState.ledCRed || 0;
    this.ledCGreen = currentState.ledCGreen || 0;
    this.ledCBlue = currentState.ledCBlue || 0;

    // Adaptive trigger parameters
    this.adaptiveTriggerLeftMode = currentState.adaptiveTriggerLeftMode || 0;
    this.adaptiveTriggerLeftParams = Array.from(
      currentState.adaptiveTriggerLeftParams || [
        currentState.adaptiveTriggerLeftParam0 || 0,
        currentState.adaptiveTriggerLeftParam1 || 0,
        currentState.adaptiveTriggerLeftParam2 || 0,
      ],
      value => Math.max(0, Math.min(255, Number(value) || 0)),
    ).slice(0, 10);
    while (this.adaptiveTriggerLeftParams.length < 10) this.adaptiveTriggerLeftParams.push(0);

    this.adaptiveTriggerRightMode = currentState.adaptiveTriggerRightMode || 0;
    this.adaptiveTriggerRightParams = Array.from(
      currentState.adaptiveTriggerRightParams || [
        currentState.adaptiveTriggerRightParam0 || 0,
        currentState.adaptiveTriggerRightParam1 || 0,
        currentState.adaptiveTriggerRightParam2 || 0,
      ],
      value => Math.max(0, Math.min(255, Number(value) || 0)),
    ).slice(0, 10);
    while (this.adaptiveTriggerRightParams.length < 10) this.adaptiveTriggerRightParams.push(0);

    // Haptic feedback
    this.hapticVolume = currentState.hapticVolume || 0;
  }

  // Pack the data into the output buffer
  pack() {
    // Based on DS5 output report structure from HID descriptor
    // Byte 0-1: Control flags (16-bit little endian)
    this.view.setUint16(0, (this.validFlag1 << 8) | this.validFlag0, true);

    // Byte 2-3: Vibration motors
    this.view.setUint8(2, this.bcVibrationRight);
    this.view.setUint8(3, this.bcVibrationLeft);

    // Bytes 4-7: Audio control (reserved for now)
    this.view.setUint8(4, this.headphoneVolume);
    this.view.setUint8(5, this.speakerVolume);
    this.view.setUint8(6, this.micVolume);
    this.view.setUint8(7, this.audioControl);

    // Byte 8: Mute LED control
    this.view.setUint8(8, this.muteLedControl);

    // Byte 9: Reserved
    this.view.setUint8(9, 0);

    // Bytes 10-20: Right adaptive trigger
    this.view.setUint8(10, this.adaptiveTriggerRightMode);
    this.adaptiveTriggerRightParams.forEach((value, index) => this.view.setUint8(11 + index, value));

    // Bytes 21-31: Left adaptive trigger
    this.view.setUint8(21, this.adaptiveTriggerLeftMode);
    this.adaptiveTriggerLeftParams.forEach((value, index) => this.view.setUint8(22 + index, value));

    // Bytes 32-41: timestamp/power/audio/lightbar setup
    for (let i = 32; i <= 41; i++) {
      this.view.setUint8(i, 0);
    }

    // Byte 37 is the secondary audio-control byte. Byte 38 is the third
    // valid-flags byte; byte 42 is LED brightness.
    this.view.setUint8(37, this.audioControl2);
    this.view.setUint8(38, this.validFlag2);
    this.view.setUint8(42, this.ledBrightness);

    // Byte 43: Player LED indicator
    this.view.setUint8(43, this.playerIndicator);

    // Bytes 44-46: Lightbar RGB
    this.view.setUint8(44, this.ledCRed);
    this.view.setUint8(45, this.ledCGreen);
    this.view.setUint8(46, this.ledCBlue);

    return this.buffer;
  }
}

// Encode the three documented DualSense adaptive-trigger effects into the
// native 11-byte block (mode plus ten parameters). Zone strengths occupy
// three bits each and vibration frequency is parameter 9 / block byte 9.
function encodeDS5TriggerEffect(effect = { mode: 'off' }) {
  const mode = effect?.mode ?? 'off';
  const empty = () => Array(10).fill(0);
  if (mode === 'off') return { mode: DS5_TRIGGER_EFFECT_MODE.OFF, params: empty() };

  const strength = Math.max(1, Math.min(8, Math.round(Number(effect.strength) || 1)));
  if (mode === 'single') {
    const start = Math.max(2, Math.min(7, Math.round(Number(effect.start) || 2)));
    const end = Math.max(start + 1, Math.min(8, Math.round(Number(effect.end) || start + 1)));
    const zones = (1 << start) | (1 << end);
    const params = empty();
    params[0] = zones & 0xff;
    params[1] = (zones >>> 8) & 0xff;
    params[2] = (strength - 1) & 0x07;
    return { mode: DS5_TRIGGER_EFFECT_MODE.TRIGGER, params };
  }

  if (mode === 'resistance' || mode === 'machinegun' || mode === 'auto') {
    const start = Math.max(0, Math.min(9, Math.round(Number(effect.start) || 0)));
    let activeZones = 0;
    let packedStrength = 0;
    for (let zone = start; zone < 10; zone++) {
      activeZones |= 1 << zone;
      packedStrength |= ((strength - 1) & 0x07) << (3 * zone);
    }
    const params = empty();
    params[0] = activeZones & 0xff;
    params[1] = (activeZones >>> 8) & 0xff;
    params[2] = packedStrength & 0xff;
    params[3] = (packedStrength >>> 8) & 0xff;
    params[4] = (packedStrength >>> 16) & 0xff;
    params[5] = (packedStrength >>> 24) & 0xff;
    if (mode !== 'resistance') params[8] = Math.max(1, Math.min(255, Math.round(Number(effect.frequency) || 1)));
    return {
      mode: mode === 'resistance' ? DS5_TRIGGER_EFFECT_MODE.RESISTANCE : DS5_TRIGGER_EFFECT_MODE.VIBRATION,
      params,
    };
  }
  throw new Error(`Unsupported adaptive trigger mode: ${mode}`);
}

function ds5_color(serialNumber) {
  // Color is obtained by the 5th and 6th characters of the serial number
  // e.g. A12305xxx0000000 -> '05' -> Starlight Blue
  const colorMap = {
    '00': 'White',
    '01': 'Midnight Black',
    '02': 'Cosmic Red',
    '03': 'Nova Pink',
    '04': 'Galactic Purple',
    '05': 'Starlight Blue',
    '06': 'Grey Camouflage',
    '07': 'Volcanic Red',
    '08': 'Sterling Silver',
    '09': 'Cobalt Blue',
    '10': 'Chroma Teal',
    '11': 'Chroma Indigo',
    '12': 'Chroma Pearl',
    '13': 'HyperPop Techno Red',
    '14': 'HyperPop Remix Green',
    '15': 'HyperPop Rhythm Blue',
    '30': '30th Anniversary',
    'Z1': 'God of War Ragnarok',
    'Z2': 'Spider-Man 2',
    'Z3': 'Astro Bot',
    'Z4': 'Fortnite',
    'Z6': 'The Last of Us',
    'ZA': 'God of War 20th Anniversary',
    'ZB': 'Icon Blue Limited Edition',
    'ZC': 'Ghost of Yōtei Limited Edition',
    'ZD': 'Marathon Limited Edition',
    'ZE': 'Genshin Impact Limited Edition',
    'ZF': '007 First Light Limited Edition',
  };

  const colorCode = serialNumber.slice(4, 6);
  const colorName = colorMap[colorCode] || 'Unknown';
  return colorName;
}

/**
* DualSense (DS5) Controller implementation
*/
class DS5Controller extends BaseController {
  constructor(device) {
    super(device);
    this.model = "DS5";
    this.finetuneMaxValue = 65535; // 16-bit max value for DS5

    // Initialize current output state to track controller settings
    this.currentOutputState = {
      validFlag0: 0,
      validFlag1: 0,
      validFlag2: 0,
      bcVibrationRight: 0,
      bcVibrationLeft: 0,
      headphoneVolume: 0,
      speakerVolume: 0,
      micVolume: 0,
      audioControl: 0,
      audioControl2: 0,
      muteLedControl: 0,
      powerSaveMuteControl: 0,
      lightbarSetup: 0,
      ledBrightness: 0,
      playerIndicator: 0,
      ledCRed: 0,
      ledCGreen: 0,
      ledCBlue: 0,
      adaptiveTriggerLeftMode: 0,
      adaptiveTriggerLeftParams: Array(10).fill(0),
      adaptiveTriggerRightMode: 0,
      adaptiveTriggerRightParams: Array(10).fill(0),
      hapticVolume: 0
    };
    this.pcmAudioRouteState = null;
  }

  getInputConfig() {
    return DS5_INPUT_CONFIG;
  }

  async getSerialNumber() {
    return await this.getSystemInfo(1, 19, 17);
  }

  async getInfo() {
    return this._getInfo(false);
  }

  async _getInfo(is_edge) {
    // Device-only: collect info and return a common structure; do not touch the DOM
    try {

      const view = await this.receiveFeatureReport(0x20);

      const cmd = view.getUint8(0, true);
      if(cmd != 0x20 || view.buffer.byteLength != 64)
        return { ok: false, error: new Error("Invalid response for ds5_info") };

      const build_date = new TextDecoder().decode(view.buffer.slice(1, 1+11));
      const build_time = new TextDecoder().decode(view.buffer.slice(12, 20));

      const fwtype     = view.getUint16(20, true);
      const swseries   = view.getUint16(22, true);
      const hwinfo     = view.getUint32(24, true);
      const fwversion  = view.getUint32(28, true);

      const updversion = view.getUint16(44, true);
      const unk        = view.getUint8(46, true);

      const fwversion1 = view.getUint32(48, true);
      const fwversion2 = view.getUint32(52, true);
      const fwversion3 = view.getUint32(56, true);

      const serial_number = await this.getSystemInfo(1, 19, 17);
      const color = ds5_color(serial_number);
      const infoItems = [
        { key: l("Serial Number"), value: serial_number, cat: "hw", copyable: true },
        { key: l("MCU Unique ID"), value: await this.getSystemInfo(1, 9, 9, false), cat: "hw", isExtra: true, copyable: true },
        { key: l("PCBA ID"), value: reverse_str(await this.getSystemInfo(1, 17, 14)), cat: "hw", isExtra: true },
        { key: l("Battery Barcode"), value: await this.getSystemInfo(1, 24, 23), cat: "hw", isExtra: true, copyable: true },
        { key: l("VCM Left Barcode"), value: await this.getSystemInfo(1, 26, 16), cat: "hw", isExtra: true, copyable: true },
        { key: l("VCM Right Barcode"), value: await this.getSystemInfo(1, 28, 16), cat: "hw", isExtra: true, copyable: true },

        { key: l("Color"), value: l(color), cat: "hw", addInfoIcon: 'color', copyable: true },

        ...(is_edge ? [] : [{ key: l("Board Model"), value: this.hwToBoardModel(hwinfo), cat: "hw", addInfoIcon: 'board', copyable: true }]),

        { key: l("FW Build Date"), value: build_date + " " + build_time, cat: "fw" },
        { key: l("FW Type"), value: "0x" + dec2hex(fwtype), cat: "fw", isExtra: true },
        { key: l("FW Series"), value: "0x" + dec2hex(swseries), cat: "fw", isExtra: true },
        { key: l("HW Model"), value: "0x" + dec2hex32(hwinfo), cat: "hw", isExtra: true },
        { key: l("FW Version"), value: "0x" + dec2hex32(fwversion), cat: "fw", isExtra: true },
        { key: l("FW Update"), value: "0x" + dec2hex(updversion), cat: "fw", isExtra: true },
        { key: l("FW Update Info"), value: "0x" + dec2hex8(unk), cat: "fw", isExtra: true },
        { key: l("SBL FW Version"), value: "0x" + dec2hex32(fwversion1), cat: "fw", isExtra: true },
        { key: l("Venom FW Version"), value: "0x" + dec2hex32(fwversion2), cat: "fw", isExtra: true },
        { key: l("Spider FW Version"), value: "0x" + dec2hex32(fwversion3), cat: "fw", isExtra: true },

        { key: l("Touchpad ID"), value: await this.getSystemInfo(5, 2, 8, false), cat: "hw", isExtra: true, copyable: true },
        { key: l("Touchpad FW Version"), value: await this.getSystemInfo(5, 4, 8, false), cat: "fw", isExtra: true },
      ];

      const old_controller = build_date.search(/ 2020| 2021/);
      let disable_bits = 0;
      if(old_controller != -1) {
        la("ds5_info_error", {"r": "old"});
        disable_bits |= 2; // 2: outdated firmware
      }

      const nv = await this.queryNvStatus();
      const bd_addr = await this.getBdAddr();
      infoItems.push({ key: l("Bluetooth Address"), value: bd_addr, cat: "hw", isExtra: true });

      const pending_reboot = (nv?.status === 'pending_reboot');

      return { ok: true, infoItems, nv, disable_bits, pending_reboot };
    } catch(error) {
      return { ok: false, error, disable_bits: 1 };
    }
  }

  async flash(progressCallback = null) {
    requireFlashPermit(this);
    try {
      await this.nvsUnlock();
      const lockRes = await this.nvsLock();
      if(!lockRes.ok) throw (lockRes.error || new Error("NVS lock failed"));

      return { success: true, message: l("Changes saved successfully") };
    } catch(error) {
      throw new Error(l("Error while saving changes"), { cause: error });
    }
  }

  async reset() {
    try {
      await this.sendFeatureReport(0x80, [1,1]);
    } catch(error) {
    }
  }

  async nvsLock() {
    // la("ds5_nvlock");
    try {
      await this.sendFeatureReport(0x80, [3,1]);
      await this.receiveFeatureReport(0x81);
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async nvsUnlock() {
    // la("ds5_nvunlock");
    try {
      await this.sendFeatureReport(0x80, [3,2, 101, 50, 64, 12]);
      const data = await this.receiveFeatureReport(0x81);
    } catch(error) {
      await sleep(500);
      throw new Error(l("NVS Unlock failed"), { cause: error });
    }
  }

  async getBdAddr() {
    await this.sendFeatureReport(0x80, [9,2]);
    const data = await this.receiveFeatureReport(0x81);
    return format_mac_from_view(data, 4);
  }

  async getSystemInfo(base, num, length, decode = true) {
    await this.sendFeatureReport(128, [base,num]);
    const pcba_id = await this.receiveFeatureReport(129);
    if(pcba_id.getUint8(1) != base || pcba_id.getUint8(2) != num || pcba_id.getUint8(3) != 2) {
      return l("error");
    }
    if(decode)
      return new TextDecoder().decode(pcba_id.buffer.slice(4, 4+length));

    return buf2hex(pcba_id.buffer.slice(4, 4+length));
  }

  async calibrateSticksBegin() {
    try {
      // Begin
      await this.sendFeatureReport(0x82, [1,1,1]);

      // Assert
      const data = await this.receiveFeatureReport(0x83);
      if(data.getUint32(0, false) != 0x83010101) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_sticks_begin_failed", {"d1": d1});
        throw new Error(`Stick center calibration begin failed: ${d1}`);
      }
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateSticksSample() {
    try {
      // Sample
      await this.sendFeatureReport(0x82, [3,1,1]);

      // Assert
      const data = await this.receiveFeatureReport(0x83);
      if(data.getUint32(0, false) != 0x83010101) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_sticks_sample_failed", {"d1": d1});
        throw new Error(`Stick center calibration sample failed: ${d1}`);
      }
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateSticksEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x82, [2,1,1]);

      const data = await this.receiveFeatureReport(0x83);

      if(data.getUint32(0, false) != 0x83010102) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_sticks_failed", {"s": 3, "d1": d1});
        throw new Error(`Stick center calibration end failed: ${d1}`);
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateRangeBegin() {
    try {
      // Begin
      await this.sendFeatureReport(0x82, [1,1,2]);

      // Assert
      const data = await this.receiveFeatureReport(0x83);
      if(data.getUint32(0, false) != 0x83010201) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_range_begin_failed", {"d1": d1});
        throw new Error(`Stick range calibration begin failed: ${d1}`);
      }
      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateRangeEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x82, [2,1,2]);

      // Assert
      const data = await this.receiveFeatureReport(0x83);

      if(data.getUint32(0, false) != 0x83010202) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_range_end_failed", {"d1": d1});
        throw new Error(`Stick range calibration end failed: ${d1}`);
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async queryNvStatus() {
    try {
      await this.sendFeatureReport(0x80, [3,3]);
      const data = await this.receiveFeatureReport(0x81);
      const ret = data.getUint32(1, false);
      if (ret === 0x15010100) {
        return { device: 'ds5', status: 'pending_reboot', locked: null, code: 4, raw: ret };
      }
      if (ret === 0x03030201) {
        return { device: 'ds5', status: 'locked', locked: true, mode: 'temporary', code: 1, raw: ret };
      }
      if (ret === 0x03030200) {
        return { device: 'ds5', status: 'unlocked', locked: false, mode: 'permanent', code: 0, raw: ret };
      }
      if (ret === 1 || ret === 2) {
        return { device: 'ds5', status: 'unknown', locked: null, code: 2, raw: ret };
      }
      return { device: 'ds5', status: 'unknown', locked: null, code: ret, raw: ret };
    } catch (error) {
      return { device: 'ds5', status: 'error', locked: null, code: 2, error };
    }
  }

  hwToBoardModel(hw_ver) {
    const a = (hw_ver >> 8) & 0xff;
    if(a == 0x03) return "BDM-010";
    if(a == 0x04) return "BDM-020";
    if(a == 0x05) return "BDM-030";
    if(a == 0x06) return "BDM-040";
    if(a == 0x07 || a == 0x08) return "BDM-050";
    if(a == 0x09) return "BDM-060R";
    // TODO 0x10?
    if(a == 0x11) return "BDM-060M";
    // TODO 0x12?
    if(a == 0x13) return "BDM-060X";
    return l("Unknown");
  }

  async getInMemoryModuleData() {
    // DualSense
    await this.sendFeatureReport(0x80, [12, 2]);
    await sleep(100);
    const data = await this.receiveFeatureReport(0x81);
    const cmd = data.getUint8(0, true);
    const [p1, p2, p3] = [1, 2, 3].map(i => data.getUint8(i, true));

    if(cmd != 129 || p1 != 12 || (p2 != 2 && p2 != 4) || p3 != 2)
      return null;

    return Array.from({ length: 12 }, (_, i) => data.getUint16(4 + i * 2, true));
  }

  async writeFinetuneData(data) {
    const pkg = data.reduce((acc, val) => acc.concat([val & 0xff, val >> 8]), [12, 1]);
    await this.sendFeatureReport(0x80, pkg);
  }

  /**
   * Send output report to the DS5 controller
   * @param {ArrayBuffer} data - The output report data
   */
  async sendOutputReport(data, reason = "") {
    if (!this.device?.opened) {
      throw new Error('Device is not opened');
    }
    try {
      console.log(`Sending output report${ reason ? ` to ${reason}` : '' }:`, DS5_OUTPUT_REPORT.USB_REPORT_ID, buf2hex(data));
      await withTimeout(this.device.sendReport(DS5_OUTPUT_REPORT.USB_REPORT_ID, new Uint8Array(data)), 5000, 'sendReport');
    } catch (error) {
      throw new Error(`Failed to send output report: ${error.message}`);
    }
  }

  /**
   * Update the current output state with values from an OutputStruct
   * @param {DS5OutputStruct} outputStruct - The output structure to copy state from
   */
  updateCurrentOutputState(outputStruct) {
    this.currentOutputState = { ...outputStruct };
  }

  /**
   * Get a copy of the current output state
   * @returns {Object} A copy of the current output state
   */
  getCurrentOutputState() {
    return { ...this.currentOutputState };
  }

  /**
   * Initialize the current output state when the controller is first connected.
   * Since DS5 controllers don't provide a way to read the current output state,
   * this method sets up reasonable defaults and attempts to detect any current settings.
   */
  async initializeCurrentOutputState() {
    try {
      // Reset all output state to known defaults
      this.currentOutputState = {
        ...this.getCurrentOutputState(),
        validFlag1: 0b1111_0111,
        ledCRed: 0,
        ledCGreen: 0,
        ledCBlue: 255,
      };

      // Send a "reset" output report to ensure the controller is in a known state
      // This will turn off any existing effects and set the controller to defaults
      const resetOutputStruct = new DS5OutputStruct(this.currentOutputState);
      await this.sendOutputReport(resetOutputStruct.pack(), 'init default states');

      // Update our state to reflect what we just sent
      this.updateCurrentOutputState(resetOutputStruct);
    } catch (error) {
      console.warn("Failed to initialize DS5 output state:", error);
      // Even if the reset fails, we still have the default state initialized
    }
  }

  /**
   * Set left adaptive trigger to single-trigger mode
   */
  async setAdaptiveTrigger(left, right) {
    try {
      const leftEffect = encodeDS5TriggerEffect(left);
      const rightEffect = encodeDS5TriggerEffect(right);

      // Create output structure with current controller state
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        adaptiveTriggerLeftMode: leftEffect.mode,
        adaptiveTriggerLeftParams: leftEffect.params,
        adaptiveTriggerRightMode: rightEffect.mode,
        adaptiveTriggerRightParams: rightEffect.params,

        validFlag0: validFlag0 | DS5_VALID_FLAG0.LEFT_TRIGGER | DS5_VALID_FLAG0.RIGHT_TRIGGER,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set adaptive trigger mode');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.LEFT_TRIGGER | DS5_VALID_FLAG0.RIGHT_TRIGGER);

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);

      return { success: true };
    } catch (error) {
      throw new Error("Failed to set left adaptive trigger mode", { cause: error });
    }
  }

  /**
   * Set vibration motors for haptic feedback
   * @param {number} heavyLeft - Left motor intensity (0-255)
   * @param {number} lightRight - Right motor intensity (0-255)
   */
  async setVibration(heavyLeft = 0, lightRight = 0) {
    try {
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        bcVibrationLeft: Math.max(0, Math.min(255, heavyLeft)),
        bcVibrationRight: Math.max(0, Math.min(255, lightRight)),
        validFlag0: validFlag0 | DS5_VALID_FLAG0.LEFT_VIBRATION | DS5_VALID_FLAG0.RIGHT_VIBRATION, // Update both vibration motors
      });
      await this.sendOutputReport(outputStruct.pack(), 'set vibration');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.LEFT_VIBRATION | DS5_VALID_FLAG0.RIGHT_VIBRATION);

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set vibration", { cause: error });
    }
  }

  /**
   * Test speaker tone by controlling speaker volume and audio settings
   * This creates a brief audio feedback through the controller's speaker or headphones
   * @param {string} output - Audio output destination: "speaker" (default) or "headphones"
   */
  async setSpeakerTone(output = "speaker") {
    try {
      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        speakerVolume: 85,
        headphoneVolume: 55,
        validFlag0: validFlag0 | DS5_VALID_FLAG0.HEADPHONE_VOLUME | DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL,
      });
      await this.sendOutputReport(outputStruct.pack(), output === "headphones" ? 'play headphone tone' : 'play speaker tone');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.HEADPHONE_VOLUME | DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL);

      // Send feature reports to enable audio
      if (output === "headphones") {
        // Audio configuration command for headphones
        await this.sendFeatureReport(128, [6, 4, 0, 0, 0, 0, 4, 0, 6]);
        // Enable headphone tone
        await this.sendFeatureReport(128, [6, 2, 1, 1, 0]);
      } else {
        // Audio configuration command for speakers
        await this.sendFeatureReport(128, [6, 4, 0, 0, 8]);
        // Enable speaker tone
        await this.sendFeatureReport(128, [6, 2, 1, 1, 0]);
      }

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set speaker tone", { cause: error });
    }
  }

  /**
   * Route USB PCM front-right audio to the built-in DualSense speaker.
   * PCM transport remains the responsibility of the operating-system audio
   * device; this HID report only selects the controller's output path.
   */
  async setPcmAudioRoute(output = "speaker") {
    if (output !== "speaker") throw new Error("Unsupported PCM audio route");
    if (this.pcmAudioRouteState) throw new Error("PCM audio route is already active");

    const previous = {
      speakerVolume: this.currentOutputState.speakerVolume || 0,
      audioControl: this.currentOutputState.audioControl || 0,
      audioControl2: this.currentOutputState.audioControl2 || 0,
    };
    // Save before the transfer: if a USB completion is lost after the device
    // applied the report, cleanup can still restore the tracked prior state.
    this.pcmAudioRouteState = previous;
    try {
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        speakerVolume: 0x64,
        audioControl: 0x30,
        audioControl2: 0x02,
        validFlag0: this.currentOutputState.validFlag0
          | DS5_VALID_FLAG0.SPEAKER_VOLUME
          | DS5_VALID_FLAG0.AUDIO_CONTROL,
        validFlag1: this.currentOutputState.validFlag1 | DS5_VALID_FLAG1.AUDIO_CONTROL2,
      });
      await this.sendOutputReport(outputStruct.pack(), 'route USB PCM to speaker');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL);
      outputStruct.validFlag1 &= ~DS5_VALID_FLAG1.AUDIO_CONTROL2;
      this.updateCurrentOutputState(outputStruct);
      return { ...previous };
    } catch (error) {
      throw new Error("Failed to route PCM audio to speaker", { cause: error });
    }
  }

  /** Restore the tracked audio state captured by setPcmAudioRoute(). */
  async resetPcmAudioRoute() {
    const previous = this.pcmAudioRouteState;
    if (!previous) return { success: true };
    try {
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        ...previous,
        validFlag0: this.currentOutputState.validFlag0
          | DS5_VALID_FLAG0.SPEAKER_VOLUME
          | DS5_VALID_FLAG0.AUDIO_CONTROL,
        validFlag1: this.currentOutputState.validFlag1 | DS5_VALID_FLAG1.AUDIO_CONTROL2,
      });
      await this.sendOutputReport(outputStruct.pack(), 'restore PCM audio route');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL);
      outputStruct.validFlag1 &= ~DS5_VALID_FLAG1.AUDIO_CONTROL2;
      this.updateCurrentOutputState(outputStruct);
      this.pcmAudioRouteState = null;
      return { success: true };
    } catch (error) {
      throw new Error("Failed to restore PCM audio route", { cause: error });
    }
  }

  /**
   * Reset speaker settings to default (turn off speaker)
   */
  async resetSpeakerSettings() {
    try {
      // Disable speaker tone first via feature report
      await this.sendFeatureReport(128, [6, 2, 0, 1, 0]);

      const { validFlag0 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        speakerVolume: 0,
        validFlag0: validFlag0 | DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL,
      });
      // outputStruct.audioControl = 0x00;
      await this.sendOutputReport(outputStruct.pack(), 'stop speaker tone');
      outputStruct.validFlag0 &= ~(DS5_VALID_FLAG0.SPEAKER_VOLUME | DS5_VALID_FLAG0.AUDIO_CONTROL);

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to reset speaker settings", { cause: error });
    }
  }

  /**
   * Set lightbar color
   * @param {number} red - Red component (0-255)
   * @param {number} green - Green component (0-255)
   * @param {number} blue - Blue component (0-255)
   */
  async setLightbarColor(red = 0, green = 0, blue = 0) {
    try {
      const { validFlag1 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        ledCRed: Math.max(0, Math.min(255, red)),
        ledCGreen: Math.max(0, Math.min(255, green)),
        ledCBlue: Math.max(0, Math.min(255, blue)),
        validFlag1: validFlag1 | DS5_VALID_FLAG1.LIGHTBAR_COLOR,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set lightbar color');
      outputStruct.validFlag1 &= ~DS5_VALID_FLAG1.LIGHTBAR_COLOR;

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set lightbar color", { cause: error });
    }
  }

  /**
   * Set player indicator lights
   * @param {number} pattern - Player indicator pattern (0-31, each bit represents a light)
   */
  async setPlayerIndicator(pattern = 0) {
    try {
      const { validFlag1 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        playerIndicator: Math.max(0, Math.min(31, pattern)),
        validFlag1: validFlag1 | DS5_VALID_FLAG1.PLAYER_INDICATOR,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set player indicator');
      outputStruct.validFlag1 &= ~DS5_VALID_FLAG1.PLAYER_INDICATOR;

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set player indicator", { cause: error });
    }
  }

  /**
   * Set the controller's three-level LED brightness. RGB is additionally
   * scaled in the adapter so the public 10..100 control stays predictable.
   */
  async setLedBrightness(percent = 100) {
    try {
      const level = percent > 66 ? 0 : (percent > 33 ? 1 : 2);
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        ledBrightness: level,
        validFlag2: this.currentOutputState.validFlag2 | DS5_VALID_FLAG2.LED_BRIGHTNESS,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set LED brightness');
      outputStruct.validFlag2 &= ~DS5_VALID_FLAG2.LED_BRIGHTNESS;
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set LED brightness", { cause: error });
    }
  }

  /**
   * Reset lights to default state (turn off)
   */
  async resetLights() {
    try {
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        muteLedControl: 0,
        playerIndicator: 0,
        ledCRed: 0,
        ledCGreen: 0,
        ledCBlue: 0,
        ledBrightness: 0,
        validFlag1: this.currentOutputState.validFlag1
          | DS5_VALID_FLAG1.LIGHTBAR_COLOR
          | DS5_VALID_FLAG1.PLAYER_INDICATOR
          | DS5_VALID_FLAG1.MUTE_LED,
        validFlag2: this.currentOutputState.validFlag2 | DS5_VALID_FLAG2.LED_BRIGHTNESS,
      });
      await this.sendOutputReport(outputStruct.pack(), 'reset lights');
      outputStruct.validFlag1 &= ~(DS5_VALID_FLAG1.LIGHTBAR_COLOR | DS5_VALID_FLAG1.PLAYER_INDICATOR | DS5_VALID_FLAG1.MUTE_LED);
      outputStruct.validFlag2 &= ~DS5_VALID_FLAG2.LED_BRIGHTNESS;
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to reset lights", { cause: error });
    }
  }

  /**
   * Set mute button LED state
   * @param {number} state - Mute LED state (0 = off, 1 = solid, 2 = pulsing)
   */
  async setMuteLed(state = 0) {
    try {
      const { validFlag1 } = this.currentOutputState;
      const outputStruct = new DS5OutputStruct({
        ...this.currentOutputState,
        muteLedControl: Math.max(0, Math.min(2, state)),
        validFlag1: validFlag1 | DS5_VALID_FLAG1.MUTE_LED,
      });
      await this.sendOutputReport(outputStruct.pack(), 'set mute LED');
      outputStruct.validFlag1 &= ~DS5_VALID_FLAG1.MUTE_LED;

      // Update current state to reflect the changes
      this.updateCurrentOutputState(outputStruct);
    } catch (error) {
      throw new Error("Failed to set mute LED", { cause: error });
    }
  }

  getNumberOfSticks() {
    return 2;
  }

  /**
  * Parse DS5 battery status from input data
  */
  parseBatteryStatus(data) {
    const bat = data.getUint8(52); // DS5 battery byte is at position 52

    // DS5: bat_charge = low 4 bits, bat_status = high 4 bits
    const bat_charge = bat & 0x0f;
    const bat_status = bat >> 4;

    let charge_level = 0;
    let cable_connected = false;
    let is_charging = false;
    let is_error = false;

    switch (bat_status) {
      case 0:
        // On battery power
        charge_level = Math.min(bat_charge * 10 + 5, 100);
        break;
      case 1:
        // Charging
        charge_level = Math.min(bat_charge * 10 + 5, 100);
        is_charging = true;
        cable_connected = true;
        break;
      case 2:
        // Fully charged
        charge_level = 100;
        cable_connected = true;
        break;
      case 15:
        // Battery is flat
        charge_level = 0;
        is_charging = true;
        cable_connected = true;
        break;
      case 11: // not sure yet what this error means
      default:
        // Error state
        is_error = true;
        break;
    }

    return { charge_level, cable_connected, is_charging, is_error };
  }
}

/**
* DualSense Edge (DS5 Edge) Controller implementation
*/
class DS5EdgeController extends DS5Controller {
  constructor(device) {
    super(device);
    this.model = "DS5_Edge";
    this.finetuneMaxValue = 4095; // 12-bit max value for DS5 Edge
  }

  getInputConfig() {
    const ds5Map = super.getInputConfig();

    // DS5 Edge has extra buttons
    return {
      ...ds5Map,
      buttonMap: [
        ...ds5Map.buttonMap,
        { name: 'fn_left', byte: 9, mask: 0x10, svg: 'Fn_left' },
        { name: 'fn_right', byte: 9, mask: 0x20, svg: 'Fn_right' },
        { name: 'paddle_left', byte: 9, mask: 0x40, svg: 'Paddle_left' },
        { name: 'paddle_right', byte: 9, mask: 0x80, svg: 'Paddle_right' },
      ],
    }
  }

  async getInfo() {
    // DS5 Edge uses the same info structure as DS5 but with is_edge=true
    const result = await this._getInfo(true);

    if (result.ok) {
      // DS Edge extra module info
      const empty = Array(17).fill('\x00').join('');
      try {
        const sticks_barcode = (await this.getBarcode()).map(barcode => barcode === empty ? l("Unknown") : barcode);
        result.infoItems.push({ key: l("Left Module Barcode"), value: sticks_barcode[1], cat: "fw" });
        result.infoItems.push({ key: l("Right Module Barcode"), value: sticks_barcode[0], cat: "fw" });
      } catch(_e) {
        // ignore module read errors here
      }
    }

    return result;
  }

  parseDeviceSpecificInputs(data) {
    const triggerLevel = data.getUint8(49);
    return {
      l2_stop_slider: (triggerLevel >> 4) & 3,  // bits 4-5
      r2_stop_slider: triggerLevel >> 6,        // bits 6-7
    };
  }

  async flash(progressCallback = null) {
    requireFlashPermit(this);
    try {
      const ret = await this.flashModules(progressCallback);
      if(ret) {
        return { 
          success: true, 
          message: "<b>" + l("Changes saved successfully") + "</b>.<br><br>" + l("If the calibration is not stored permanently, please double-check the wirings of the hardware mod."),
          isHtml: true
        };
      }
    } catch(error) {
      throw new Error(l("Error while saving changes"), { cause: error });
    }
  }

  async getBarcode() {
    try {
      const td = new TextDecoder();
  
      await this.sendFeatureReport(0x80, [21,34,0]);
      await sleep(100);
  
      const r_data = await this.receiveFeatureReport(0x81);
      const r_bc = td.decode(r_data.buffer.slice(21, 21+17));
  
      await this.sendFeatureReport(0x80, [21,34,1]);
      await sleep(100);
  
      const l_data = await this.receiveFeatureReport(0x81);
      const l_bc = td.decode(l_data.buffer.slice(21, 21+17));
      return [l_bc, r_bc];
    } catch(error) {
      throw new Error(l("Cannot read module barcodes"), { cause: error });
    }
  }

  async unlockModule(i) {
    const m_name = i == 0 ? "left module" : "right module";

    await this.sendFeatureReport(0x80, [21, 6, i, 11]);
    await sleep(200);
    const ret = await this.waitUntilWritten([21, 6, 2]);
    if(!ret) {
      throw new Error(l("Cannot unlock") + " " + l(m_name));
    }
  }

  async lockModule(i) {
    const m_name = i == 0 ? "left module" : "right module";

    await this.sendFeatureReport(0x80, [21, 4, i, 8]);
    await sleep(200);
    const ret = await this.waitUntilWritten([21, 4, 2]);
    if(!ret) {
      throw new Error(l("Cannot lock") + " " + l(m_name));
    }
  }

  async storeDataInto(i) {
    const m_name = i == 0 ? "left module" : "right module";

    await this.sendFeatureReport(0x80, [21, 5, i]);
    await sleep(200);
    const ret = await this.waitUntilWritten([21, 3, 2]);
    if(!ret) {
      throw new Error(l("Cannot store data into") + " " + l(m_name));
    }
  }

  async flashModules(progressCallback) {
    requireFlashPermit(this);
    try {
      const progress = typeof progressCallback === 'function' ? progressCallback : () => {};
      progress(0);

      // Reload data, this ensures correctly writing data in the controller
      await sleep(100);
      progress(10);

      // Unlock modules
      await this.unlockModule(0);
      progress(15);
      await this.unlockModule(1);
      progress(30);

      // Unlock NVS
      await this.nvsUnlock();
      await sleep(50);
      progress(45);

      // This should trigger write into modules
      const data = await this.getInMemoryModuleData();
      await sleep(50);
      progress(60);
      await this.writeFinetuneData(data);

      // Extra delay
      await sleep(100);

      // Lock back modules
      await this.lockModule(0);
      progress(80);
      await this.lockModule(1);
      progress(100);

      // Lock back NVS
      await sleep(100);
      const lockRes = await this.nvsLock();
      if(!lockRes.ok) throw (lockRes.error || new Error("NVS lock failed"));

      await sleep(250);

      return true;
    } catch(error) {
      throw error;
    }
  }

  async waitUntilWritten(expected) {
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts) {
      const data = await this.receiveFeatureReport(0x81);

      // Check if all expected bytes match
      const allMatch = expected.every((expectedByte, i) => 
        data.getUint8(1 + i, true) === expectedByte
      );

      if (allMatch) {
        return true;
      }

      attempts++;
      await sleep(50);
    }

    return false;
  }

  async calibrateSticksEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x82, [2,1,1]);

      let data = await this.receiveFeatureReport(0x83);

      if(data.getUint32(0, false) != 0x83010101) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_sticks_failed", {"s": 3, d1});
        return { ok: false, code: 4, d1 };
      }

      await this.sendFeatureReport(0x82, [2,1,1]);
      data = await this.receiveFeatureReport(0x83);
      if(data.getUint32(0, false) != 0x83010103 && data.getUint32(0, false) != 0x83010312) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_sticks_failed", {"s": 3, d1});
        return { ok: false, code: 5, d1 };
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async calibrateRangeEnd() {
    try {
      // Write
      await this.sendFeatureReport(0x82, [2,1,2]);

      // Assert
      let data = await this.receiveFeatureReport(0x83);

      if(data.getUint32(0, false) != 0x83010201) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_range_end_failed", {d1});
        return { ok: false, code: 4, d1 };
      }

      await this.sendFeatureReport(0x82, [2,1,2]);
      data = await this.receiveFeatureReport(0x83);
      if(data.getUint32(0, false) != 0x83010203) {
        const d1 = dec2hex32(data.getUint32(0, false));
        la("ds5_calibrate_range_end_failed", {d1});
        return { ok: false, code: 5, d1 };
      }

      return { ok: true };
    } catch(error) {
      return { ok: false, error };
    }
  }

  async getInMemoryModuleData() {
    // DualSense Edge
    await this.sendFeatureReport(0x80, [12, 4]);
    await sleep(100);
    const data = await this.receiveFeatureReport(0x81);
    const cmd = data.getUint8(0, true);
    const [p1, p2, p3] = [1, 2, 3].map(i => data.getUint8(i, true));

    if(cmd != 129 || p1 != 12 || (p2 != 2 && p2 != 4) || p3 != 2)
      return null;

    return Array.from({ length: 12 }, (_, i) => data.getUint16(4 + i * 2, true));
  }

  async writeFinetuneData(data) {
    const pkg = data.reduce((acc, val) => acc.concat([val & 0xff, val >> 8]), [12, 1]);
    await this.sendFeatureReport(0x80, pkg);
  }

  getNumberOfSticks() {
    return 2;
  }

}

class InputDecoder {
  constructor(controller) {
    this.currentController = controller;
    
    this.has_changes_to_write = null; 
    this.inputHandler = () => {}; // Callback function for input processing

    // Button and stick states for UI updates
    this.button_states = {
      // e.g. 'square': false, 'cross': false, ...
      sticks: {
        left: {
          x: 0,
          y: 0
        },
        right: {
          x: 0,
          y: 0
        }
      }
    };

    // IMU state for gyro and accelerometer
    this.imuState = {
      gyro: {
        x: 0,
        y: 0,
        z: 0
      },
      accel: {
        x: 0,
        y: 0,
        z: 0
      }
    };

    // Touch points for touchpad input
    this.touchPoints = [];

    // Battery status tracking
    this.batteryStatus = {
      bat_txt: "",
      changed: false,
      charge_level: 0,
      cable_connected: false,
      is_charging: false,
      is_error: false
    };
    this._lastBatteryText = "";
  }

  _sticksChanged(current, newValues) {
    return current.left.x !== newValues.left.x || current.left.y !== newValues.left.y ||
    current.right.x !== newValues.right.x || current.right.y !== newValues.right.y;
  }

  /**
  * Helper function to check if IMU (gyro/accel) values have changed
  */
  _imuChanged(current, newValues) {
    return current.gyro.x !== newValues.gyro.x || current.gyro.y !== newValues.gyro.y || current.gyro.z !== newValues.gyro.z ||
    current.accel.x !== newValues.accel.x || current.accel.y !== newValues.accel.y || current.accel.z !== newValues.accel.z;
  }

  /**
  * Parse IMU (gyro and accelerometer) state changes
  * @param {DataView} data - Input data view
  * @param {number} imuOffset - Offset to IMU data
  * @returns {Object|null} IMU changes or null if no changes
  */
  _parseImuState(data, imuOffset) {
    if (imuOffset === undefined) return null; // device has no known IMU data
    const newIMU = this._parseIMUData(data, imuOffset);
    if (this._imuChanged(this.imuState, newIMU)) {
      this.imuState = newIMU;
      return newIMU;
    }
    return null;
  }

  /**
  * Generic button processing for DS4/DS5
  * Records button states and returns changes
  */
  _recordButtonStates(data, BUTTON_MAP, dpadByte, l2AnalogByte, r2AnalogByte, stickBytes) {
    const changes = {};

    // Stick positions: bytes 0-3 unless the device layout says otherwise;
    // axes without a byte (e.g. the missing second stick on VR2) read as 0
    const { lx, ly, rx, ry } = stickBytes ?? { lx: 0, ly: 1, rx: 2, ry: 3 };
    // Preserve every HID axis step; round only the visible labels.
    const readAxis = (byte) =>
      byte === undefined ? 0 : (data.getUint8(byte) - 127.5) / 127.5;

    const newSticks = {
      left: { x: readAxis(lx), y: readAxis(ly) },
      right: { x: readAxis(rx), y: readAxis(ry) }
    };

    if (this._sticksChanged(this.button_states.sticks, newSticks)) {
      this.button_states.sticks = newSticks;
      changes.sticks = newSticks;
    }

    // L2/R2 analog values (byte undefined = trigger not present on this device)
    [
      ['l2', l2AnalogByte],
      ['r2', r2AnalogByte]
    ].forEach(([name, byte]) => {
      if (byte === undefined) return;
      const val = data.getUint8(byte);
      const key = name + '_analog';
      if (val !== this.button_states[key]) {
        this.button_states[key] = val;
        changes[key] = val;
      }
    });

    // Dpad is a 4-bit hat value (dpadByte undefined = no dpad on this device)
    if (dpadByte !== undefined) {
      const hat = data.getUint8(dpadByte) & 0x0F;
      const dpad_map = {
        up:    (hat === 0 || hat === 1 || hat === 7),
        right: (hat === 1 || hat === 2 || hat === 3),
        down:  (hat === 3 || hat === 4 || hat === 5),
        left:  (hat === 5 || hat === 6 || hat === 7)
      };
      for (const dir of ['up', 'right', 'down', 'left']) {
        const pressed = dpad_map[dir];
        if (this.button_states[dir] !== pressed) {
          this.button_states[dir] = pressed;
          changes[dir] = pressed;
        }
      }
    }

    // Other buttons
    for (const btn of BUTTON_MAP) {
      if (['up', 'right', 'down', 'left'].includes(btn.name)) continue; // Dpad handled above
      const pressed = (data.getUint8(btn.byte) & btn.mask) !== 0;
      if (this.button_states[btn.name] !== pressed) {
        this.button_states[btn.name] = pressed;
        changes[btn.name] = pressed;
      }
    }

    // Handle the Edge controller's specific inputs
    const deviceSpecificInputs = this.currentController.parseDeviceSpecificInputs(data);
    Object.entries(deviceSpecificInputs).forEach(([key, value]) => {
      if(value !== this.button_states[key]) {
        this.button_states[key] = value;
        changes[key] = value;
      }
    });

    return changes;
  }

  /**
  * Process controller input data and call callback if set
  * This is the first part of the split process_controller_input function
  * @param {Object} inputData - The input data from the controller
  * @returns {Object} Changes object containing processed input data
  */
  processControllerInput(inputData) {
    const { data } = inputData;

    // Keep the latest raw report around for debug/inspection views
    this.lastRawInput = data;

    const inputConfig = this.currentController.getInputConfig();
    const { buttonMap, dpadByte, l2AnalogByte, r2AnalogByte, imuOffset } = inputConfig;
    const { touchpadOffset } = inputConfig;

    // Process button states using the device-specific configuration
    const changes = this._recordButtonStates(data, buttonMap, dpadByte, l2AnalogByte, r2AnalogByte, inputConfig.stickBytes);

    // Record IMU state if available
    const imuChanges = this._parseImuState(data, imuOffset);
    if (imuChanges) {
      changes.imu = imuChanges;
    }

    // Parse and store touch points if touchpad data is available
    if (touchpadOffset) {
      this.touchPoints = this._parseTouchPoints(data, touchpadOffset);
    }

    // Parse and store battery status
    this.batteryStatus = this._parseBatteryStatus(data);

    const result = {
      changes,
      inputConfig: { buttonMap },
      touchPoints: this.touchPoints,
      batteryStatus: this.batteryStatus,
    };

    this.inputHandler(result);
  }

  /**
  * Parse touch points from input data
  * @param {DataView} data - Input data view
  * @param {number} offset - Offset to touchpad data
  * @returns {Array} Array of touch points with {active, id, x, y} properties
  */
  _parseTouchPoints(data, offset) {
    // Returns array of up to 2 points: {active, id, x, y}
    const points = [];
    for (let i = 0; i < 2; i++) {
      const base = offset + i * 4;
      const arr = [];
      for (let j = 0; j < 4; j++) arr.push(data.getUint8(base + j));
      const b0 = data.getUint8(base);
      const active = (b0 & 0x80) === 0; // 0 = finger down, 1 = up
      const id = b0 & 0x7F;
      const b1 = data.getUint8(base + 1);
      const b2 = data.getUint8(base + 2);
      const b3 = data.getUint8(base + 3);
      // x: 12 bits, y: 12 bits
      const x = ((b2 & 0x0F) << 8) | b1;
      const y = (b3 << 4) | (b2 >> 4);
      points.push({ active, id, x, y });
    }
    return points;
  }

  /**
  * Parse battery status from input data
  */
  _parseBatteryStatus(data) {
    const batteryInfo = this.currentController.parseBatteryStatus(data);
    const bat_txt = this._batteryPercentToText(batteryInfo);

    const changed = bat_txt !== this._lastBatteryText;
    this._lastBatteryText = bat_txt;

    return { bat_txt, changed, ...batteryInfo };
  }

  /**
  * Parse IMU (gyro and accelerometer) data from input data
  * @param {DataView} data - Input data view
  * @param {number} imuOffset - Offset to IMU data
  * @returns {Object} IMU data with gyro and accel values
  */
  _parseIMUData(data, imuOffset) {
    // Nominal, uncalibrated sensitivities. In both DS4 and DS5 input reports
    // the gyroscope (pitch, yaw, roll) comes first, followed by the accelerometer.
    const GYRO_SENSITIVITY_LSB_PER_DPS = 14.31;
    const ACCEL_SENSITIVITY_LSB_PER_G = 8192.0;

    const [gyroX, gyroY, gyroZ] = [0, 2, 4]
      .map(i => data.getInt16(imuOffset + i, true))
      .map(v => v / GYRO_SENSITIVITY_LSB_PER_DPS);  // degrees per second
    const [accelX, accelY, accelZ] = [6, 8, 10]
      .map(i => data.getInt16(imuOffset + i, true))
      .map(v => v / ACCEL_SENSITIVITY_LSB_PER_G);   // g (should total ~1g at rest)

    return {
      gyro: {
        x: gyroX, y: gyroY, z: gyroZ
      },
      accel: {
        x: accelX, y: accelY, z: accelZ
      }
    };
  }

  /**
  * Convert battery percentage to display text with icons
  */
  _batteryPercentToText({charge_level, is_charging, is_error}) {
    if (is_error) {
      return '<font color="red">' + l("error") + '</font>';
    }

    const batteryIcons = [
      { threshold: 20, icon: 'fa-battery-empty' },
      { threshold: 40, icon: 'fa-battery-quarter' },
      { threshold: 60, icon: 'fa-battery-half' },
      { threshold: 80, icon: 'fa-battery-three-quarters' },
    ];

    const icon_txt = batteryIcons.find(item => charge_level < item.threshold)?.icon || 'fa-battery-full';
    const icon_full = `<i class="fa-solid ${icon_txt}"></i>`;
    const bolt_txt = is_charging ? '<i class="fa-solid fa-bolt"></i>' : '';
    return [`${charge_level}%`, icon_full, bolt_txt].join(' ');
  }

  /**
  * Get a bound input handler function that can be assigned to device.oninputreport
  * @returns {Function} Bound input handler function
  */
  getInputHandler() {
    return this.processControllerInput.bind(this);
  }
}

// RemTeh adapter. Protocol classes are pinned DualShock Tools (MIT, the_al).
const models = new Map([[0x05c4, DS4Controller], [0x09cc, DS4Controller], [0x0ce6, DS5Controller], [0x0df2, DS5EdgeController]]);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
function createSonyEngine({onFrame = () => {}, onState = () => {}} = {}) {
  const baselineGate=createBaselineGate();
  let tuning=null, manualCalibration=null, releaseLease=null, durableBackup=null;
  let device, controller, decoder, generation = 0, inputHandler, disconnectHandler, lastFrame, effectId = 0, activeCleanup = null, activeEffectDone = null, activeStop = null;
  const state = {connected: false, connecting: false, connectStage: null, busy: false, fault: false, mode: null, effect: null, dirty: false, saved: false, info: null, battery: null, lastInput: 0, nvLocked: false, revision: 0};
  const pendingOpens = new WeakSet();
  let grantedDevices=[];
  const hasInputReport = device => {
    const collections = [...(device.collections ?? [])];
    for (let i=0;i<collections.length;i++) {
      const collection=collections[i];
      if (collection.inputReports?.some(report=>report.reportId===1)) return true;
      collections.push(...(collection.children ?? []));
    }
    return false;
  };
  const isSonyInputDevice = d => d.vendorId===0x054c&&models.has(d.productId)&&hasInputReport(d);
  function refreshGranted(){
    if(!navigator.hid?.getDevices)return;
    void navigator.hid.getDevices().then(list=>{grantedDevices=list.filter(isSonyInputDevice);}).catch(()=>{grantedDevices=[];});
  }
  refreshGranted();
  const notify = () => onState({...state});
  const error = code => { throw new Error(code); };
  function guard() {
    if (!state.connected || !device?.opened || !controller) error('disconnected');
    if (state.fault) error('reconnect_required');
    if (!state.info?.verified) error('unsupported_device');
    if (!state.nvLocked) error('memory_unlocked');
    const b = state.battery;
    if (!b || performance.now() - state.lastInput > 2000 || !Number.isFinite(b.charge_level) || b.is_error) error('battery_unknown');
    if (b.charge_level < 30 && !b.is_charging) error('battery_low');
  }
  async function run(fn) {
    if (state.busy) error('busy');
    guard(); const own = generation;
    state.busy = true; notify();
    try {
      const result = await fn();
      if (generation !== own || !state.connected) error('disconnected');
      return result;
    } catch (e) {
      if (generation === own && !e.recovered) state.fault = true;
      throw e;
    } finally { if (generation === own) {state.busy = false; notify();} }
  }
  async function call(method) {
    if (!state.connected || !device?.opened) error('disconnected');
    const own = generation;
    const result = await controller[method]();
    if (own !== generation || !state.connected) error('disconnected');
    if (!result?.ok) error('protocol_failed');
    return result;
  }
  function receive(event) {
    if (event.reportId !== 1 || event.data.byteLength !== 63 || !decoder) return;
    try {
      decoder.processControllerInput(event);
      const b = decoder.button_states;
      state.lastInput = performance.now();
      state.battery = {...decoder.batteryStatus};
      const buttons = Object.fromEntries(Object.entries(b).filter(([, value]) => typeof value === 'boolean'));
      lastFrame = {connection:generation, axisBytes:Array.from({length:4},(_,i)=>event.data.getUint8(i)), axes: [b.sticks.left.x, b.sticks.left.y, b.sticks.right.x, b.sticks.right.y], buttons, triggers: [(b.l2_analog ?? 0) / 255, (b.r2_analog ?? 0) / 255], touch: decoder.touchPoints, imu: decoder.imuState, timestamp: state.lastInput};
      if (state.connected) onFrame(lastFrame);
    } catch { state.fault = true; notify(); }
  }
  async function disconnect() {
    if (state.busy && !activeEffectDone) error('busy');
    await stopEffects().catch(() => {});
    generation++;
    const old = device;
    if (old && inputHandler) old.removeEventListener('inputreport', inputHandler);
    if (disconnectHandler) navigator.hid?.removeEventListener('disconnect', disconnectHandler);
    if(releaseLease){releaseLease();releaseLease=null;}
    tuning=manualCalibration=durableBackup=null;device = controller = decoder = lastFrame = null;
    Object.assign(state, {connected:false, connecting:false, connectStage:null, busy:false, fault:false, mode:null, effect:null, dirty:false, saved:false, info:null, battery:null, lastInput:0, nvLocked:false, revision:0});
    notify();
    if (old?.opened) await old.close().catch(() => {});
    refreshGranted();
  }
  async function connect({choose=false}={}) {
    if (state.busy || state.connecting || state.connected) error('busy');
    // Reuse only one USB interface already authorized by the browser. Otherwise
    // open the native chooser directly in the click, before any await.
    const choice = !choose&&grantedDevices.length===1?Promise.resolve(grantedDevices):navigator.hid.requestDevice({filters: [...models.keys()].map(productId => ({vendorId:0x054c, productId}))});
    state.connecting = true; state.connectStage = 'choosing'; notify(); const own = ++generation;
    let cancelInputWait, armInputWait;
    try {
      const selectedDevices = await choice;
      if (!selectedDevices.length) error('cancelled');
      const candidates = selectedDevices.filter(isSonyInputDevice);
      if (candidates.length !== 1) error(candidates.length ? 'multiple_sony_interfaces' : 'sony_interface_unavailable');
      const selected = candidates[0];
      if (own !== generation) return;
      if (pendingOpens.has(selected)) error('hid_open_pending');
      const Model = models.get(selected.productId);
      if (selected.vendorId !== 0x054c || !Model) error('unsupported_device');
      device = selected; controller = new Model(device); decoder = new InputDecoder(controller);
      const first = new Promise((resolve, reject) => {
        let timer, settled = false;
        const inputDevice = device;
        const done = (err, event) => {
          if (settled) return;
          settled = true; clearTimeout(timer);
          inputDevice.removeEventListener('inputreport', probe);
          err ? reject(err) : resolve(event);
        };
        const probe = event => done(event.reportId !== 1 || event.data.byteLength !== 63 ? new Error('usb_required') : null, event);
        cancelInputWait = () => done(new Error('disconnected'));
        inputDevice.addEventListener('inputreport', probe);
        armInputWait = () => {if(!settled)timer = setTimeout(() => done(new Error('no_input')), 5000);};
      });
      // Observe rejection immediately even if opening the OS device takes longer.
      first.catch(() => {});
      state.connectStage = 'opening'; notify();
      pendingOpens.add(selected);
      const opening = (async () => {
        try {
          await selected.open();
          // An OS open can resolve after our deadline. Do not let that late
          // handle leak or be reused by a second connection in the meantime.
          if (own !== generation && selected.opened) await selected.close().catch(() => {});
        } finally { pendingOpens.delete(selected); }
      })();
      await withTimeout(opening, 8000, 'hid_open');
      if (own !== generation) return;
      state.connectStage = 'input'; notify(); armInputWait();
      const initial = await first;
      if (own !== generation) return;
      inputHandler = receive; device.addEventListener('inputreport', inputHandler); receive(initial);
      disconnectHandler = event => {
        if (event.device !== device) return;
        baselineGate.disconnected(state.info?.tuningId);
        // An effect keeps busy set until its serialized cleanup completes. Other
        // in-flight operations retain the prior hard-disconnect behavior so a
        // lost controller invalidates their connection generation immediately.
        if (!activeEffectDone) state.busy = false;
        void disconnect();
      };
      navigator.hid.addEventListener('disconnect', disconnectHandler);
      state.connectStage = 'information'; notify();
      const info = await controller.getInfo();
      if (own !== generation || !device?.opened) error('disconnected');
      const fields = {};
      for (const item of info.infoItems ?? []) {
        if (['SW Version','FW Version','FW Update','Board Model','HW Version','Build Date','FW Build Date','FW Type','FW Update Info','HW Model','Serial Number','Color'].includes(item.key)) fields[item.key] = String(item.value).replace(/\0/g, '').slice(0,120);
      }
      state.info = {model:controller.getModel(), name:device.productName, verified:info.ok === true && info.disable_bits === 0, blocked:info.disable_bits ?? 1, readable:info.ok === true, persistentSave:typeof controller.getInMemoryModuleData === 'function', fields, nv:info.nv?.status ?? 'unknown'};
      state.nvLocked = info.nv?.locked === true;
      state.info.tuningId=['DS5','DS5_Edge'].includes(controller.getModel())?await tuningIdentity(info):null;
      baselineGate.connected(state.info.tuningId);
      // Keep one writable session per physical controller on this origin.
      // The browser releases the lease when the tab closes. External programs and
      // old pages still require the parameter compare-and-swap checks below.
      if(state.info.tuningId && navigator.locks?.request){
        state.connectStage = 'lease'; notify();
        await new Promise((resolve,reject)=>{
          navigator.locks.request('remteh-calibration:'+state.info.tuningId,{ifAvailable:true},async lock=>{
            if(!lock){reject(new Error('controller_in_another_tab'));return;}
            if(own!==generation){reject(new Error('disconnected'));return;}
            await new Promise(release=>{releaseLease=release;resolve();});
          }).catch(reject);
        });
      }
      // Connection is read-only. Output tests start only after an explicit click.
      if (own !== generation) return;
      state.connected = true; state.connecting = false; state.connectStage = null; notify();
      if (lastFrame) onFrame(lastFrame);
    } catch (e) {
      if (own === generation) {state.busy = false; await disconnect();}
      throw e;
    } finally {
      cancelInputWait?.();
    }
  }
  async function checkMemory() {
    const own = generation;
    const nv = await controller.queryNvStatus();
    if (own !== generation || !state.connected) error('disconnected');
    state.nvLocked = nv?.locked === true; guard();
  }
  const tuneAxes=[[0,4,8],[1,5,9],[2,6,10],[3,7,11]];
  const validTune=v=>Array.isArray(v)&&v.length===12&&v.every(x=>Number.isInteger(x)&&x>=0&&x<=65535)&&tuneAxes.every(([a,b,c])=>v[c]-v[a]>=64&&v[b]-v[c]>=64);
  const sameTune=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===12&&b.length===12&&a.every((x,i)=>x===b[i]);
  const boundedTune=(v,o)=>validTune(v)&&validTune(o)&&tuneAxes.every(([a,b,c])=>Math.abs(v[c]-o[c])<=Math.min(o[c]-o[a],o[b]-o[c])*.08&&[a,b].every(k=>Math.abs(v[k]-o[k])<=Math.abs(o[k]-o[c])*.2));
  async function tuningIdentity(info){
    const item=(info.infoItems??[]).find(x=>x.key==='MCU Unique ID');
    const uid=String(item?.value??'').trim().replace(/^0x/i,'');
    if(!/^[0-9a-f]{16,40}$/i.test(uid)||/^(0+|f+)$/i.test(uid)||typeof crypto==='undefined'||!crypto.subtle)return null;
    const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode('remteh-ds5-tuning:'+uid.toLowerCase()));
    return Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
  }
  // Each operation captures the physical connection. No continuation can switch
  // to another controller after an unplug/reconnect while a report is in flight.
  function tuningIO(){
    const own=generation,ctrl=controller,dev=device;
    const check=()=>{if(own!==generation||controller!==ctrl||!state.connected||!dev?.opened)error('disconnected');};
    const read=async()=>{check();const value=await ctrl.getInMemoryModuleData();check();if(!validTune(value))error('tuning_read_failed');return [...value];};
    const lock=async()=>{check();const nv=await ctrl.queryNvStatus();check();state.nvLocked=nv?.locked===true;guard();};
    const write=async values=>{check();guard();await ctrl.writeFinetuneData([...values]);check();const readback=await read();if(!sameTune(values,readback))error('tuning_readback_failed');return readback;};
    return {own,ctrl,check,read,lock,write};
  }
  async function preserveBeforeCalibration(values,io) {
    if(!durableBackup){
      await baselineGate.require(state.info?.tuningId,confirmPowerCycle);io.check();
      if(!sameTune(values,await io.read()))error('tuning_external_change');
      durableBackup=preserveOriginal(state.info?.tuningId,values);
    }
  }
  async function beginTuning(restorePoint=null){
    if(state.mode)error('busy');
    if(state.info?.model!=='DS5'||!state.info?.tuningId)error('tuning_unavailable');
    return run(async()=>{
      const io=tuningIO();await io.lock();const current=await io.read();
      await preserveBeforeCalibration(current,io);
      const original=restorePoint?.parameters??current;
      if(restorePoint&&(restorePoint.identity!==state.info.tuningId||!boundedTune(current,original)))error('tuning_backup_mismatch');
      tuning={own:io.own,original:[...original],last:current,initialDirty:state.dirty,initialSaved:state.saved};state.mode='fine-tune';
      return {identity:state.info.tuningId,parameters:[...current],original:[...original],connection:generation,revision:state.revision};
    });
  }
  function tuningGuard(revision){
    if(state.mode!=='fine-tune'||!tuning||tuning.own!==generation)error('tuning_session_required');
    if(revision!==state.revision)error('tuning_revision_changed');
  }
  async function writeTuning(values,revision){
    tuningGuard(revision);
    if(!boundedTune(values,tuning.original))error('tuning_bounds');
    const session=tuning,previous=[...tuning.last],priorDirty=state.dirty,priorSaved=state.saved;
    return run(async()=>{
      const io=tuningIO();await io.lock();const actual=await io.read();if(!sameTune(actual,previous))error('tuning_external_change');
      if(sameTune(actual,values))return {parameters:actual,connection:generation,revision:state.revision};
      let attempted=false;
      try{attempted=true;await io.write(values);session.last=[...values];state.revision++;state.dirty=true;state.saved=false;}
      catch(cause){
        // Never unlock memory during a trial or rollback. Keep the durable backup
        // if the device has gone away; a different generation must not receive it.
        if(attempted)try{io.check();await io.lock();await io.write(previous);state.dirty=priorDirty;state.saved=priorSaved;const recovered=new Error('tuning_rolled_back');recovered.recovered=true;throw recovered;}catch(rollback){if(rollback.recovered)throw rollback;}
        throw cause;
      }
      return {parameters:[...session.last],connection:generation,revision:state.revision};
    });
  }
  async function restoreTuning(revision){tuningGuard(revision);return writeTuning(tuning.original,revision);}
  async function readTuning(){
    if(state.info?.model!=='DS5'||!state.info?.tuningId)error('tuning_unavailable');
    return run(async()=>{const io=tuningIO();await io.lock();return {identity:state.info.tuningId,parameters:await io.read(),connection:generation,revision:state.revision};});
  }
  async function saveTuning(evidence){
    tuningGuard(evidence?.revision);
    if(!state.dirty)error('no_changes');
    if(!evidence?.verified||evidence.connection!==generation||!sameTune(evidence.parameters,tuning.last))error('measurements_required');
    return run(async()=>{
      const io=tuningIO();await io.lock();const actual=await io.read();if(!sameTune(actual,tuning.last))error('tuning_external_change');
      guard();const result=await permanentWrite(io.ctrl,state.info?.tuningId,durableBackup,()=>{io.check();guard();return io.ctrl.flash();});io.check();if(!result?.success)error('flash_failed');
      await io.lock();if(!sameTune(await io.read(),actual))error('tuning_readback_failed');
      state.dirty=false;state.saved=true;
    });
  }
  function endTuning(){if(state.busy)error('busy');if(state.mode==='fine-tune'){state.mode=null;tuning=null;notify();}}
  async function beginManualCalibration(mode, method) {
    await checkMemory();
    const supportsCas = typeof controller?.getInMemoryModuleData === 'function';
    if (supportsCas) {
      const io=tuningIO(), actual=await io.read();
      await preserveBeforeCalibration(actual,io);
      if (manualCalibration && (manualCalibration.own!==generation || manualCalibration.revision!==state.revision || !sameTune(actual,manualCalibration.parameters))) error('tuning_external_change');
      manualCalibration={own:generation,revision:state.revision,parameters:actual};
    } else manualCalibration={own:generation,revision:state.revision,parameters:null};
    state.mode=mode;state.saved=false;await call(method);
  }
  async function finishManualCalibration(method) {
    await call(method);
    const supportsCas = typeof controller?.getInMemoryModuleData === 'function';
    const parameters=supportsCas?await tuningIO().read():null;
    state.mode=null;state.dirty=true;state.revision++;
    manualCalibration={own:generation,revision:state.revision,parameters};
  }
  async function beginCenter() {
    if (state.mode) error('busy');
    return run(() => beginManualCalibration('center','calibrateSticksBegin'));
  }
  async function sampleCenter() {
    if (state.mode !== 'center') error('wrong_mode');
    return run(() => call('calibrateSticksSample'));
  }
  async function endCenter() {
    if (state.mode !== 'center') error('wrong_mode');
    return run(async () => {await call('calibrateSticksSample'); await delay(200); await finishManualCalibration('calibrateSticksEnd');});
  }
  async function beginRange() {
    if (state.mode) error('busy');
    return run(() => beginManualCalibration('range','calibrateRangeBegin'));
  }
  async function endRange() {
    if (state.mode !== 'range') error('wrong_mode');
    return run(() => finishManualCalibration('calibrateRangeEnd'));
  }
  async function savePermanent(word, evidence) {
    // Evidence belongs to this connection and the latest temporary revision.
    if (word !== 'SAVE') error('confirmation_required');
    if (state.mode || !state.dirty) error('no_changes');
    if (!evidence || evidence.connection !== generation || evidence.revision !== state.revision || !evidence.before || !evidence.after) error('measurements_required');
    if (!manualCalibration || manualCalibration.own!==generation || manualCalibration.revision!==state.revision || !validTune(manualCalibration.parameters)) error('persistent_save_unverified');
    return run(async () => {
      // Compare all 12 in-memory parameters immediately before flash. An old
      // page or external tool cannot silently replace the measured candidate.
      const io=tuningIO();await io.lock();const actual=await io.read();
      if(!sameTune(actual,manualCalibration.parameters))error('tuning_external_change');
      guard();const result=await permanentWrite(io.ctrl,state.info?.tuningId,durableBackup,()=>{io.check();guard();return io.ctrl.flash();});io.check();
      if (!result?.success) error('flash_failed');
      await io.lock();if(!sameTune(await io.read(),actual))error('tuning_readback_failed');
      state.dirty=false; state.saved=true;
    });
  }
  async function autoCenter(isStable = () => false, progress = () => {}) {
    if (state.mode) error('busy');
    return run(async () => {
      await checkMemory();
      const supportsCas = typeof controller?.getInMemoryModuleData === 'function';
      if (supportsCas) {
        const io=tuningIO(), actual=await io.read();
        await preserveBeforeCalibration(actual,io);
        if (manualCalibration && (manualCalibration.own!==generation || manualCalibration.revision!==state.revision || !sameTune(actual,manualCalibration.parameters))) error('tuning_external_change');
        manualCalibration={own:generation,revision:state.revision,parameters:actual};
      } else manualCalibration={own:generation,revision:state.revision,parameters:null};
      if (!isStable()) error('sticks_moving');
      state.mode='auto-center'; state.saved=false;
      await call('calibrateSticksBegin');
      for (let i=0;i<5;i++) {
        await delay(100); guard();
        if (!isStable()) error('sticks_moving');
        await call('calibrateSticksSample'); progress((i+1)/5);
      }
      await finishManualCalibration('calibrateSticksEnd');
    });
  }
  function outputGuard() {
    if (!state.connected || !device?.opened || !controller) error('disconnected');
    if (state.fault) error('reconnect_required');
    if (!state.info?.readable || (state.info.blocked & 1)) error('unsupported_device');
    if (performance.now()-state.lastInput>2000) error('no_input');
    if (state.mode) error('busy');
  }
  async function stopEffects() {
    if(activeStop)return activeStop;
    effectId++;
    const cleanup=activeCleanup, done=activeEffectDone; activeCleanup=null;
    const stopping=(async()=>{
      let cleanupError=null;
      try {if (cleanup) await cleanup();} catch (cause) {cleanupError=cause;}
      if (done) await done.promise;
      if (cleanupError) throw cleanupError;
    })();
    activeStop=stopping;
    try{return await stopping;}
    finally{if(activeStop===stopping)activeStop=null;}
  }
  async function testEffect(type, options={}) {
    if (state.busy) error('busy');
    outputGuard();
    if (!options || typeof options !== 'object') error('invalid_effect_options');
    const own=generation, token=++effectId, ctrl=controller, dev=device;
    const wait=async ms=>{const until=performance.now()+ms;while(performance.now()<until){if(token!==effectId||own!==generation||!dev.opened)return false;await delay(Math.min(50,ms));}return token===effectId;};
    const off={mode:'off'};
    const model=ctrl.getModel();
    if (!['rumble','adaptive','speaker','speaker-audio','headphones','lights'].includes(type)) error('feature_unavailable');
    const isDS5=['DS5','DS5_Edge'].includes(model), isDS4=model==='DS4';
    if (['adaptive','speaker','speaker-audio','headphones'].includes(type) && !isDS5) error('feature_unavailable');
    if (type==='lights' && !isDS5 && !isDS4) error('feature_unavailable');
    const numberOption=(name,fallback,min,max)=>{
      const value=options[name]===undefined?fallback:options[name];
      if(typeof value!=='number'||!Number.isFinite(value)||value<min||value>max)error(`invalid_effect_${name}`);
      return value;
    };
    const side=options.side??'both';
    if(['rumble','adaptive'].includes(type)&&!['left','right','both'].includes(side))error('invalid_effect_side');
    const strength=['rumble','adaptive'].includes(type)?numberOption('strength',40,10,80):40;
    const motorValue=Math.round(strength*2.55);
    let mode=options.mode, pattern=options.pattern, duration=0, start=30, frequency=12, brightness=50, color=[0,102,255];
    if(type==='rumble'){
      pattern=pattern??'steady';
      if(!['steady','pulse','alternate','ramp'].includes(pattern))error('invalid_effect_mode');
      const defaults={steady:800,pulse:780,alternate:1500,ramp:1600};
      duration=numberOption('duration',defaults[pattern],100,5000);
    }
    if(type==='adaptive'){
      mode=mode??'single';
      if(!['resistance','single','machinegun'].includes(mode))error('invalid_effect_mode');
      start=numberOption('start',30,0,80);
      frequency=numberOption('frequency',12,1,30);
      duration=numberOption('duration',5000,1000,8000);
    }
    if(type==='lights'){
      if(mode!==undefined&&!['color','rgb','player','mute'].includes(mode))error('invalid_effect_mode');
      if(isDS4&&mode!==undefined&&!['color','rgb'].includes(mode))error('feature_unavailable');
      brightness=numberOption('brightness',50,10,100);
      duration=numberOption('duration',mode===undefined?1950:1500,100,8000);
      const colorText=options.color??'#0066ff';
      if(typeof colorText!=='string'||!/^#[0-9a-f]{6}$/i.test(colorText))error('invalid_effect_color');
      color=[1,3,5].map(index=>parseInt(colorText.slice(index,index+2),16));
    }
    if(type==='speaker-audio'){
      if(typeof options.play!=='function')error('invalid_effect_play');
      duration=numberOption('durationMs',undefined,1,30000);
    }
    const signal=options.signal;
    if(signal!==undefined&&(!signal||typeof signal.addEventListener!=='function'||typeof signal.removeEventListener!=='function'))error('invalid_effect_signal');
    if(signal?.aborted)return {completed:false,cancelled:true,type};
    state.busy=true;state.effect=type;notify();
    let resolveDone;
    const done={promise:new Promise(resolve=>{resolveDone=resolve;}),resolve:()=>resolveDone()};
    activeEffectDone=done;
    let queue=Promise.resolve();
    // Cancellation may arrive between two awaited writes (for example LEDs).
    // Check the token when dequeuing, while allowing the final reset to run.
    const enqueue=(cleanup,method,...args)=>{
      const next=queue.then(()=>{
        if(!dev.opened||(!cleanup&&(token!==effectId||own!==generation)))return;
        return ctrl[method](...args);
      });
      queue=next.catch(()=>{});return next;
    };
    const io=(method,...args)=>enqueue(false,method,...args);
    const reset=(method,...args)=>enqueue(true,method,...args);
    const pcmAbort=type==='speaker-audio'?new AbortController():null;
    let cleanup=async()=>{};
    if(type==='rumble')cleanup=()=>dev.opened?reset('setVibration',0,0):Promise.resolve();
    if(type==='adaptive')cleanup=()=>dev.opened?reset('setAdaptiveTrigger',off,off):Promise.resolve();
    if(type==='speaker'||type==='headphones')cleanup=()=>dev.opened?reset('resetSpeakerSettings'):Promise.resolve();
    if(type==='speaker-audio')cleanup=()=>{
      pcmAbort.abort();
      return dev.opened?reset('resetPcmAudioRoute'):Promise.resolve();
    };
    if(type==='lights')cleanup=()=>dev.opened?reset('resetLights'):Promise.resolve();
    activeCleanup=cleanup;
    const abort=()=>{void stopEffects().catch(()=>{});};
    signal?.addEventListener('abort',abort,{once:true});
    const vibration=async(value=motorValue,target=side)=>io('setVibration',target==='right'?0:value,target==='left'?0:value);
    try {
      if(type==='rumble') {
        if(pattern==='steady'){
          await vibration();await wait(duration);
        }else if(pattern==='pulse'){
          const unit=duration/780;
          for(let i=0;i<3&&token===effectId;i++){
            await vibration();if(!await wait(180*unit))break;
            await io('setVibration',0,0);
            if(i<2&&!await wait(120*unit))break;
          }
        }else if(pattern==='alternate'){
          const slot=duration/6;
          for(let i=0;i<6&&token===effectId;i++){
            await vibration(motorValue,side==='both'?(i%2?'right':'left'):side);
            if(!await wait(slot))break;
          }
        }else{
          const profile=[.25,.5,.75,1,1,.75,.5,.25],slot=duration/profile.length;
          for(const scale of profile){
            if(token!==effectId)break;
            await vibration(Math.round(motorValue*scale));if(!await wait(slot))break;
          }
        }
      } else if(type==='adaptive') {
        const startZone=Math.round(start/10),level=Math.max(1,Math.min(8,Math.ceil(strength*8/100)));
        const effect=mode==='single'
          ?{mode,start:Math.max(2,Math.min(7,startZone)),end:Math.max(3,Math.min(8,Math.max(2,Math.min(7,startZone))+2)),strength:level}
          :{mode,start:startZone,strength:level,frequency};
        await io('setAdaptiveTrigger',side==='right'?off:effect,side==='left'?off:effect);
        await wait(duration);
      } else if(type==='speaker'||type==='headphones') {
        await io('setSpeakerTone',type); await wait(1000);
      } else if(type==='speaker-audio') {
        await io('setPcmAudioRoute','speaker');
        if(token===effectId&&own===generation&&dev.opened){
          let timer, timedOut=false;
          let removePcmAbort=()=>{};
          const cancelled=new Promise((_,reject)=>{
            const rejectCancelled=()=>reject(new Error('speaker_audio_cancelled'));
            pcmAbort.signal.addEventListener('abort',rejectCancelled,{once:true});
            removePcmAbort=()=>pcmAbort.signal.removeEventListener('abort',rejectCancelled);
          });
          const timeout=new Promise((_,reject)=>{
            timer=setTimeout(()=>{
              timedOut=true;
              pcmAbort.abort();
              reject(new Error('speaker_audio_timeout'));
            },duration);
          });
          try{
            await Promise.race([
              Promise.resolve().then(()=>options.play({signal:pcmAbort.signal})),
              cancelled,
              timeout,
            ]);
          }catch(cause){
            if(timedOut)error('speaker_audio_timeout');
            if(token===effectId&&own===generation)throw cause;
          }finally{
            clearTimeout(timer);
            removePcmAbort();
          }
        }
      } else if(type==='lights') {
        if(mode===undefined){
          const colors=[[90,0,0],[0,90,0],[0,0,90]],slot=duration/colors.length;
          for(const rgb of colors){
            if(token!==effectId)break;
            await io('setLightbarColor',...rgb);
            if(isDS5){await io('setPlayerIndicator',21);await io('setMuteLed',1);}
            if(!await wait(slot))break;
          }
        }else if(mode==='color'){
          await io('setLightbarColor',...color.map(value=>Math.round(value*brightness/100)));await wait(duration);
        }else if(mode==='rgb'){
          const level=Math.round(255*brightness/100),colors=[[level,0,0],[0,level,0],[0,0,level]],slot=duration/colors.length;
          for(const rgb of colors){if(token!==effectId)break;await io('setLightbarColor',...rgb);if(!await wait(slot))break;}
        }else if(mode==='player'){
          await io('setLedBrightness',brightness);
          const indicators=[1,2,4,8,16,31],slot=duration/indicators.length;
          for(const indicator of indicators){if(token!==effectId)break;await io('setPlayerIndicator',indicator);if(!await wait(slot))break;}
        }else{
          await io('setLedBrightness',brightness);await io('setMuteLed',1);await wait(duration);
        }
      }
      if(own!==generation || !state.connected)error('disconnected');
      const completed=token===effectId;
      return {completed,cancelled:!completed,type};
    } finally {
      signal?.removeEventListener('abort',abort);
      const stopping=activeStop;
      try{
        if(activeCleanup===cleanup){activeCleanup=null;await cleanup();}
        if(stopping){done.resolve();await stopping;}
      }
      catch(cause){
        if(own===generation)state.fault=true;
        throw cause;
      }
      finally{
        if(activeEffectDone===done)activeEffectDone=null;
        if(own===generation){state.busy=false;state.effect=null;notify();}
        done.resolve();
      }
    }
  }
  async function rumble(side='both'){return testEffect('rumble',{side});}

  return {beginTuning,writeTuning,restoreTuning,readTuning,saveTuning,endTuning,connect, disconnect, beginCenter, sampleCenter, endCenter, beginRange, endRange, savePermanent, rumble, autoCenter, testEffect, stopEffects, outputGuard,
    get state(){return {...state};}, get connection(){return generation;}, guard};
}

export { createSonyEngine };
