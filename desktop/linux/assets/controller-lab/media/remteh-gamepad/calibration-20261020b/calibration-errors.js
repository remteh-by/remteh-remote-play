// Stable public messages shared by the website and CRM. No device identifiers,
// stack traces or browser-local backup contents are sent to the server.
export function calibrationErrorCode(error) {
  const message = String(error?.message ?? error ?? '');
  if (/^[a-z][a-z0-9_]+$/.test(message)) return message;
  if (/hid_open timed out/i.test(message)) return 'hid_open_timeout';
  const name = error?.name ?? '';
  if (name === 'NotFoundError') return 'cancelled';
  if (name === 'NotAllowedError' || name === 'NotReadableError') return 'hid_open_failed';
  if (name === 'SecurityError') return 'hid_permission_denied';
  if (name === 'NetworkError' || /NetworkError|transfer failed|timed out|Failed to (?:receive|send)/i.test(message)) return 'hid_transfer_failed';
  if (/NotAllowedError|NotReadableError|Failed to open/i.test(message)) return 'hid_open_failed';
  if (/SecurityError|user gesture|user activation/i.test(message)) return 'hid_permission_denied';
  return 'protocol_failed';
}

export const calibrationErrorMessages = {
  hid_open_timeout: 'Windows или браузер не завершил открытие USB за 8 секунд. Закройте программы для геймпада, переподключите кабель и повторите запуск. Настройки не менялись.',
  hid_open_pending: 'Предыдущее открытие USB ещё не завершено в браузере. Переподключите кабель и обновите страницу. Настройки не менялись.',
  hid_open_failed: 'Браузер не смог открыть геймпад. Закройте Steam, DS4Windows, DSX, PlayStation Accessories и другие тестеры, затем нажмите «Подключить и начать» снова.',
  hid_permission_denied: 'Браузер не разрешил доступ по USB. Откройте страницу напрямую в Chrome или Edge, нажмите «Подключить и начать» и выберите DualSense в окне браузера.',
  hid_transfer_failed: 'Не удалось прочитать параметры по USB. Закройте другие программы для геймпада, проверьте кабель и нажмите «Подключить и начать» снова.',
  hid_report_descriptor_invalid: 'Браузер передал неполное описание USB-отчёта. Обновите Chrome или Edge и подключите геймпад снова. Команда калибровки не отправлена.',
  sony_interface_unavailable: 'Выбранное устройство не передаёт данные геймпада. Подключите DualSense кабелем USB с передачей данных и выберите его в окне браузера.',
  multiple_sony_interfaces: 'Браузер вернул несколько интерфейсов геймпада. Отключите другие контроллеры и повторите выбор устройства.',
  unsupported_device: 'Не удалось подтвердить поддержку калибровки. Откройте «Устройство» и проверьте модель и версию ПО. Настройки геймпада не изменены.',
  protocol_failed: 'Геймпад не подтвердил операцию по USB. Закройте другие тестеры и переподключите кабель, затем повторите запуск.',
  cancelled: 'Выбор устройства отменён. Нажмите «Подключить и начать», выберите DualSense и подтвердите подключение в окне браузера.',
  controller_in_another_tab: 'Геймпад уже открыт в другой вкладке. Отключите его в той вкладке или закройте её, затем повторите подключение здесь.',
};
