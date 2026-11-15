// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
#pragma once
#include <QCoreApplication>
#include <QDesktopServices>
#include <QDir>
#include <QFile>
#include <QMimeDatabase>
#include <QTcpServer>
#include <QTcpSocket>
#include <QTimer>
#include <QUuid>
#include <QUrl>

// Read-only static server for the bundled Gamepad API lab. No device-writing IPC.
class ControllerLabServer : public QTcpServer
{
public:
    explicit ControllerLabServer(QObject *parent) : QTcpServer(parent)
    {
        connect(this, &QTcpServer::newConnection, this, [this] {
            while (hasPendingConnections()) {
                auto socket = nextPendingConnection();
                socket->setReadBufferSize(8193);
                connect(socket, &QTcpSocket::disconnected, socket, &QObject::deleteLater);
                connect(socket, &QTcpSocket::readyRead, this, [this, socket] { respond(socket); });
                QTimer::singleShot(8000, socket, [socket] { socket->disconnectFromHost(); });
            }
        });
    }
    bool openLab(bool russian)
    {
        if (!isListening() && !listen(QHostAddress::LocalHost, 0)) return false;
        return QDesktopServices::openUrl(QUrl("http://127.0.0.1:" + QString::number(serverPort()) + (russian ? "/?lang=ru" : "/?lang=en")));
    }
private:
    void respond(QTcpSocket *socket)
    {
        auto headers = socket->peek(8193);
        auto end = headers.indexOf("\r\n\r\n");
        if (end < 0 && headers.size() < 8193) return;
        socket->readAll();
        QByteArray status = "404 Not Found", body, mime = "text/plain";
        const QByteArray host = "127.0.0.1:" + QByteArray::number(serverPort());
        auto lines = headers.left(end).split('\n');
        auto request = lines.takeFirst().trimmed().split(' ');
        bool allowed = false;
        for (const auto &line : lines)
            if (line.trimmed().toLower() == "host: " + host) allowed = true;
        if (end >= 0 && allowed && request.size() == 3 && request[0] == "GET") {
            auto path = QUrl::fromEncoded(request[1]).path(QUrl::FullyDecoded);
            if (path == "/") path = "/index.html";
            auto root = QDir(QCoreApplication::applicationDirPath() + "/controller-lab").canonicalPath();
            auto filePath = QFileInfo(root + path).canonicalFilePath();
            if (!root.isEmpty() && path.startsWith('/') && !path.contains('\\') && !path.contains(':')
                && filePath.startsWith(root + "/", Qt::CaseInsensitive)) {
                QFile file(filePath);
                if (file.size() <= 16000000 && file.open(QIODevice::ReadOnly)) {
                    body = file.readAll();
                    mime = QMimeDatabase().mimeTypeForFile(filePath).name().toLatin1();
                    if (filePath.endsWith(".js")) mime = "text/javascript";
                    status = "200 OK";
                }
            }
        }
        socket->write("HTTP/1.1 " + status + "\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nX-Frame-Options: DENY\r\nContent-Type: " + mime + "\r\nContent-Length: " + QByteArray::number(body.size()) + "\r\n\r\n" + body);
        socket->disconnectFromHost();
    }
};

