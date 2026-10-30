"""Explain observed connection state without exporting addresses or registration data."""
import math

def summarize(*,host_configured,paired,probe_state,probe_age,engine_present,decoder_active,input_present,profile):
    fresh=isinstance(probe_age,(int,float)) and math.isfinite(probe_age) and 0<=probe_age<=15
    checks=[]
    def add(code,status,en,ru):checks.append(dict(code=code,status=status,en=en,ru=ru))
    add('target','observed' if host_configured else 'missing',
        'Console address is configured.' if host_configured else 'Choose the console address in settings.',
        'Адрес консоли задан.' if host_configured else 'Укажите адрес консоли в настройках.')
    add('pairing','observed' if paired else 'missing',
        'A local registration exists; this alone does not prove authentication will succeed.' if paired else 'Complete pairing; keep any previous registration until a new one succeeds.',
        'Локальное сопряжение найдено; это ещё не доказывает успешную авторизацию.' if paired else 'Выполните сопряжение, сохраняя старую регистрацию до успешного результата.')
    if not fresh:
        add('discovery','not-measured','No recent discovery observation. Wait for the next dashboard probe.','Нет свежего ответа проверки. Дождитесь следующего опроса на главном экране.')
    elif probe_state=='online':
        add('discovery','observed','The configured console answered discovery. This does not measure video latency.','Консоль ответила на discovery-запрос. Это не измерение задержки видео.')
    elif probe_state=='rest':
        add('discovery','observed','The console reports rest mode. Check Remote Play/wake settings before starting.','Консоль сообщает режим покоя. Проверьте Remote Play и условия пробуждения.')
    else:
        add('discovery','not-observed','No valid reply was observed. Check console power, selected address and local connectivity; the cause is not established.','Корректный ответ не получен. Проверьте питание консоли, выбранный адрес и связь в сети; причина не установлена.')
    add('engine','observed' if engine_present else 'missing',
        'The required engine is present.' if engine_present else 'Install/select the documented engine for this platform.',
        'Необходимый движок найден.' if engine_present else 'Установите или выберите движок по инструкции для этой платформы.')
    add('decoder','observed' if decoder_active else 'not-measured',
        'The engine has reported video frames; visible output still requires observation.' if decoder_active else 'No current video-frame observation. Start a stream before assessing the decoder.',
        'Движок сообщил видеокадры; видимая картинка проверяется отдельно.' if decoder_active else 'Нет наблюдения кадров текущего потока. Для проверки декодера нужен запущенный поток.')
    add('input','observed' if input_present else 'not-measured',
        'An input device/capture is present; actual button delivery needs a test.' if input_present else 'Connect a controller or explicitly enable keyboard/mouse capture.',
        'Устройство ввода или захват обнаружены; доставку нажатий проверьте в сеансе.' if input_present else 'Подключите геймпад или явно включите захват клавиатуры и мыши.')
    allowed={'smooth','balanced','rescue','sharp','sharp30'}
    return {'schema':1,'scope':'connection-observations','profile':profile if profile in allowed else 'unknown','checks':checks}
