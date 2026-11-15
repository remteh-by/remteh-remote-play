// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
#pragma once

#include <windows.h>
#include <wincrypt.h>
#include <QCryptographicHash>
#include <QDataStream>
#include <QIODevice>
#include <QSettings>
#include <QStandardPaths>

namespace Deckivo {
inline bool writeSettings(QIODevice &device, const QSettings::SettingsMap &settings)
{
    QByteArray plain;
    QDataStream stream(&plain, QIODevice::WriteOnly);
    stream.setVersion(QDataStream::Qt_6_0);
    stream << settings;
    if (stream.status() != QDataStream::Ok)
        return false;
    DATA_BLOB source{DWORD(plain.size()), reinterpret_cast<BYTE *>(plain.data())}, encrypted{};
    bool ok = CryptProtectData(&source, L"Deckivo", nullptr, nullptr, nullptr,
                               CRYPTPROTECT_UI_FORBIDDEN, &encrypted);
    SecureZeroMemory(plain.data(), plain.size());
    if (!ok)
        return false;
    bool written = device.write(reinterpret_cast<char *>(encrypted.pbData), encrypted.cbData) == encrypted.cbData;
    LocalFree(encrypted.pbData);
    return written;
}

inline bool readSettings(QIODevice &device, QSettings::SettingsMap &settings)
{
    if (device.size() > 16 * 1024 * 1024)
        return false;
    QByteArray encrypted = device.readAll();
    DATA_BLOB source{DWORD(encrypted.size()), reinterpret_cast<BYTE *>(encrypted.data())}, plain{};
    if (!CryptUnprotectData(&source, nullptr, nullptr, nullptr, nullptr, CRYPTPROTECT_UI_FORBIDDEN, &plain))
        return false;
    QDataStream stream(QByteArray::fromRawData(reinterpret_cast<char *>(plain.pbData), plain.cbData));
    stream.setVersion(QDataStream::Qt_6_0);
    QSettings::SettingsMap result;
    stream >> result;
    bool ok = stream.status() == QDataStream::Ok && stream.atEnd();
    if (ok)
        settings.swap(result);
    SecureZeroMemory(plain.pbData, plain.cbData);
    LocalFree(plain.pbData);
    return ok;
}

inline QSettings::Format format()
{
    static const auto value = QSettings::registerFormat("dvp", readSettings, writeSettings);
    return value;
}

inline QString path(const QString &name)
{
    const auto id = QCryptographicHash::hash(name.toUtf8(), QCryptographicHash::Sha256).toHex();
    return QStandardPaths::writableLocation(QStandardPaths::AppLocalDataLocation)
           + "/profiles/" + QString::fromLatin1(id) + ".dvp";
}
}

