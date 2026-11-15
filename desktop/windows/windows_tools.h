// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
#pragma once

#include "private_settings.h"
#include "controller_lab_server.h"
#include <QDateTime>
#include <QElapsedTimer>
#include <QFileDialog>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkProxy>
#include <QNetworkReply>
#include <QRegularExpression>
#include <QTcpSocket>
#include <QTimer>
#include <QSaveFile>
#include <SDL.h>
#include <QDesktopServices>
#include <QCoreApplication>
#include <QLocale>
#include <QTranslator>
#include <QJsonArray>
#include "desktop_input.h"
#include "windows_update.h"

class DeckivoTranslator final : public QTranslator {
public:
    DeckivoTranslator() {
        QFile f(":/engine-ru.json");
        if (f.open(QIODevice::ReadOnly)) words = QJsonDocument::fromJson(f.readAll()).object();
    }
    bool isEmpty() const override { return words.isEmpty(); }
    QString translate(const char *, const char *source, const char *, int) const override {
        return words.value(QString::fromUtf8(source)).toString();
    }
private:
    QJsonObject words;
};

// Never persist the remote address or account ID in history.
class WindowsTools final : public QObject
{
    Q_OBJECT
    Q_PROPERTY(WindowsUpdate* updates READ updates CONSTANT)
    Q_PROPERTY(bool autoCheck READ autoCheck WRITE setAutoCheck NOTIFY autoCheckChanged)
    Q_PROPERTY(bool touchOverlay READ touchOverlay WRITE setTouchOverlay NOTIFY inputChanged)
    Q_PROPERTY(bool invert READ invert WRITE setInvert NOTIFY inputChanged)
    Q_PROPERTY(int sensitivity READ sensitivity WRITE setSensitivity NOTIFY inputChanged)
    Q_PROPERTY(QVariantList mouseActions READ mouseActions NOTIFY inputChanged)
    Q_PROPERTY(QVariantList overlayControls READ overlayControls CONSTANT)
    Q_PROPERTY(QStringList history READ history NOTIFY historyChanged)
    Q_PROPERTY(QVariantList sessions READ sessions NOTIFY historyChanged)
    Q_PROPERTY(bool remember READ remember WRITE setRemember NOTIFY rememberChanged)
    Q_PROPERTY(QString language READ language WRITE setLanguage NOTIFY languageChanged)
    Q_PROPERTY(QVariantMap strings READ strings NOTIFY languageChanged)
public:
    WindowsUpdate *updates() { return &updater; }
    bool autoCheck() const { return state.value("autoCheck", false).toBool(); }
    void setAutoCheck(bool enabled) { state.setValue("autoCheck", enabled); emit autoCheckChanged(); }
    QVariantList overlayControls() const { return DeckivoInput::controls(); }
    bool touchOverlay() const { return state.value("touchOverlay", false).toBool(); }
    bool invert() const { return state.value("invert", false).toBool(); }
    int sensitivity() const { return state.value("sensitivity", 100).toInt(); }
    void setTouchOverlay(bool v) { state.setValue("touchOverlay", v); emit inputChanged(); }
    void setInvert(bool v) { state.setValue("invert", v); emit inputChanged(); }
    void setSensitivity(int v) { state.setValue("sensitivity", qBound(10,v,300)); emit inputChanged(); }
    QVariantList mouseActions() const {
        const QVariantList defaults{CHIAKI_CONTROLLER_ANALOG_BUTTON_R2 + 0, CHIAKI_CONTROLLER_ANALOG_BUTTON_L2 + 0,
            CHIAKI_CONTROLLER_BUTTON_R3 + 0, CHIAKI_CONTROLLER_BUTTON_L1 + 0, CHIAKI_CONTROLLER_BUTTON_R1 + 0};
        const auto list = state.value("mouseActions", defaults).toList();
        return list.size() == defaults.size() ? list : defaults;
    }
    Q_INVOKABLE void mapMouse(int index, int action) {
        auto list = mouseActions();
        if (index < 0 || index >= list.size() || action < 0 || action > CHIAKI_CONTROLLER_ANALOG_BUTTON_R2) return;
        list[index] = action;
        state.setValue("mouseActions", list); emit inputChanged();
    }
    bool remember() const { return state.value("remember", true).toBool(); }
    void setRemember(bool value) {
        if (value == remember()) return;
        state.setValue("remember", value);
        emit rememberChanged();
    }
    QString language() const { return state.value("language", "auto").toString(); }
    void setLanguage(const QString &value) {
        if (value == language() || (value != "auto" && !catalog.contains(value))) return;
        state.setValue("language", value);
        updateTranslator();
        emit languageChanged();
    }
    QVariantMap strings() const {
        const auto code = language() == "auto" ? QLocale::system().name().section('_', 0, 0) : language();
        auto result = catalog.value("en").toObject().toVariantMap();
        result.insert(catalog.value(code).toObject().toVariantMap());
        return result;
    }
    Q_INVOKABLE QString guideText() const {
        const auto code = language() == "auto" ? QLocale::system().name().section('_', 0, 0) : language();
        QFile f(":/guides/" + code + ".md");
        if (!f.exists()) f.setFileName(":/guides/en.md");
        if (!f.open(QIODevice::ReadOnly)) return {};
        return QString::fromUtf8(f.readAll());
    }
    Q_INVOKABLE bool openLicenses() {
        return QDesktopServices::openUrl(QUrl::fromLocalFile(QCoreApplication::applicationDirPath() + "/licenses"));
    }
    Q_INVOKABLE bool openWindowsReleases() {
        return QDesktopServices::openUrl(QUrl("https://github.com/remteh-by/remteh-remote-play/releases"));
    }
    explicit WindowsTools(QObject *parent) : QObject(parent) { companion.setProxy(QNetworkProxy::NoProxy);
        QFile f(":/desktop-translations.json");
        if (f.open(QIODevice::ReadOnly)) catalog = QJsonDocument::fromJson(f.readAll()).object();
        updateTranslator();
        if (autoCheck()) QTimer::singleShot(1500, &updater, &WindowsUpdate::check);
    }
    Q_INVOKABLE bool privateLanHost(const QString &host) const
    {
        const QHostAddress address(host);
        if (address.protocol() != QAbstractSocket::IPv4Protocol || address.toString() != host)
            return false;
        const auto ip = address.toIPv4Address();
        return (ip & 255) != 0 && (ip & 255) != 255
            && ((ip >> 24) == 10 || (ip >> 20) == 0xac1 || (ip >> 16) == 0xc0a8);
    }
    Q_INVOKABLE int checkLan(const QString &host)
    {
        const int serial = ++requestSerial;
        auto socket = new QTcpSocket(this);
        socket->setProxy(QNetworkProxy::NoProxy);
        auto finish = [this, serial, socket](bool ok) {
            socket->disconnect(this);
            socket->abort();
            socket->deleteLater();
            emit lanCheckDone(serial, ok);
        };
        connect(socket, &QTcpSocket::connected, this, [finish]() { finish(true); });
        connect(socket, &QTcpSocket::errorOccurred, this, [finish]() { finish(false); });
        QTimer::singleShot(3500, socket, [finish]() { finish(false); });
        QTimer::singleShot(0, socket, [socket, host]() { socket->connectToHost(host, 9295); });
        return serial;
    }
    Q_INVOKABLE int fetchCompanion(const QString &host, const QString &code)
    {
        const int serial = ++requestSerial;
        static const QRegularExpression digits(QStringLiteral("^[0-9]{8}$"));
        if (!privateLanHost(host) || !digits.match(code).hasMatch()) {
            QTimer::singleShot(0, this, [this, serial]() { emit companionDone(serial, {}); });
            return serial;
        }
        QNetworkRequest request(QUrl(QStringLiteral("http://%1:38080/v1/account").arg(host)));
        request.setAttribute(QNetworkRequest::RedirectPolicyAttribute, QNetworkRequest::ManualRedirectPolicy);
        request.setHeader(QNetworkRequest::ContentTypeHeader, "text/plain");
        request.setRawHeader("X-RemTeh-Client", "1");
        auto reply = companion.post(request, code.toLatin1());
        reply->setReadBufferSize(4097);
        QTimer::singleShot(4000, reply, [reply]() { if (!reply->isFinished()) reply->abort(); });
        connect(reply, &QIODevice::readyRead, reply, [reply]() {
            if (reply->bytesAvailable() > 4096) reply->abort();
        });
        connect(reply, &QNetworkReply::finished, this, [this, reply, serial]() {
            QString id;
            if (reply->error() == QNetworkReply::NoError && reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt() == 200
                    && reply->bytesAvailable() <= 4096) {
                const auto obj = QJsonDocument::fromJson(reply->readAll()).object();
                const auto value = obj.value("accountId").toString().toLatin1();
                const auto decoded = QByteArray::fromBase64(value, QByteArray::AbortOnBase64DecodingErrors);
                if (obj.value("protocol").toInt() == 1 && decoded.size() == 8 && decoded.toBase64() == value)
                    id = QString::fromLatin1(value);
            }
            reply->deleteLater();
            emit companionDone(serial, id);
        });
        return serial;
    }
    Q_INVOKABLE bool openLab() { return lab.openLab((language() == "auto" ? QLocale::system().name() : language()).startsWith("ru")); }
    QStringList history() const { return state.value("history").toStringList(); }
    QVariantList sessions() const {
        auto list = state.value("sessions").toList();
        for (const auto &legacy : history())
            list.append(QVariantMap{{"legacy", legacy}});
        return list.mid(0, 60);
    }
    Q_INVOKABLE void clearHistory() {
        state.remove("sessions");
        state.remove("history");
        state.sync();
        emit historyChanged();
    }
    Q_INVOKABLE void connected(int resolution, int fps)
    {
        if (!timer.isValid()) {
            started = QDateTime::currentDateTime();
            sessionHeight = resolution;
            sessionFps = fps;
            timer.start();
        }
    }
    Q_INVOKABLE void disconnected(qint64 frames)
    {
        if (!timer.isValid()) return;
        const auto seconds = timer.elapsed() / 1000;
        timer.invalidate();
        if (!remember()) return;
        auto rows = state.value("sessions").toList();
        rows.prepend(QVariantMap{{"date", started.toString("yyyy-MM-dd  HH:mm")},
            {"seconds", seconds}, {"frames", frames}, {"height", sessionHeight}, {"fps", sessionFps}});
        state.setValue("sessions", rows.mid(0, 60));
        state.sync();
        emit historyChanged();
    }
    Q_INVOKABLE bool exportReport(const QString &renderer, double queue, int dropped)
    {
        const auto file = QFileDialog::getSaveFileName(nullptr, tr("Diagnostics"), "Deckivo-report.json", "*.json");
        if (file.isEmpty()) return false;
        const char *audio = SDL_GetCurrentAudioDriver();
        const QJsonObject report{{"product", "Deckivo"}, {"version", "0.9.0"}, {"build", 4},
            {"engine", "chiaki-ng 1.10.0"}, {"architecture", "x86_64"},
            {"renderer", renderer}, {"audioDriver", audio ? QString::fromLatin1(audio) : QString()},
            {"averageQueueDepth", queue < 0 ? QJsonValue() : QJsonValue(queue)},
            {"droppedFrames", dropped < 0 ? QJsonValue() : QJsonValue(dropped)}};
        QSaveFile target(file);
        QByteArray bytes = QJsonDocument(report).toJson();
        return target.open(QIODevice::WriteOnly) && target.write(bytes) == bytes.size() && target.commit();
    }
signals:
    void lanCheckDone(int serial, bool ok);
    void companionDone(int serial, QString id);
    void historyChanged();
    void languageChanged();
    void autoCheckChanged();
    void inputChanged();
    void rememberChanged();
private:
    DeckivoTranslator translator;
    void updateTranslator() {
        QCoreApplication::removeTranslator(&translator);
        if ((language() == "auto" ? QLocale::system().name() : language()).startsWith("ru"))
            QCoreApplication::installTranslator(&translator);
    }
    int requestSerial = 0;
    int sessionHeight = 0, sessionFps = 0;
    QJsonObject catalog;
    WindowsUpdate updater{this};
    QNetworkAccessManager companion{this};
    ControllerLabServer lab{this};
    QSettings state{Deckivo::path("windows-session-history"), Deckivo::format()};
    QElapsedTimer timer;
    QDateTime started;
};

