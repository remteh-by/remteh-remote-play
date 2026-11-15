// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
#pragma once
#include <QCoreApplication>
#include <QFile>
#include <functional>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QVersionNumber>
#include <QRegularExpression>
#include <openssl/evp.h>
#include <openssl/x509.h>

// The same signed manifest and pinned public key are used by the other clients.
class WindowsUpdate final : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString status READ status NOTIFY changed)
    Q_PROPERTY(QString version READ version NOTIFY changed)
public:
    explicit WindowsUpdate(QObject *parent = nullptr) : QObject(parent) {}
    QString status() const { return result; }
    QString version() const { return available; }
    static bool authentic(QByteArrayView document, const QByteArray &encoded, const QByteArray &der) {
        auto signature = QByteArray::fromBase64(encoded.trimmed(), QByteArray::AbortOnBase64DecodingErrors);
        auto data = reinterpret_cast<const unsigned char *>(der.constData());
        auto key = d2i_PUBKEY(nullptr, &data, der.size());
        auto ctx = EVP_MD_CTX_new();
        const bool ok = key && ctx && EVP_DigestVerifyInit(ctx, nullptr, EVP_sha256(), nullptr, key) == 1
            && EVP_DigestVerify(ctx, reinterpret_cast<const unsigned char *>(signature.constData()), signature.size(),
                reinterpret_cast<const unsigned char *>(document.data()), document.size()) == 1;
        EVP_MD_CTX_free(ctx); EVP_PKEY_free(key);
        return ok;
    }
    Q_INVOKABLE void check() {
        if (result == "busy") return;
        available.clear(); result = "busy"; emit changed();
        fetch("index.json", false, [this](QByteArray doc) {
            if (doc.isEmpty()) { finish("network"); return; }
            fetch("index.sig", false, [this,doc](QByteArray sig) {
                if (sig.isEmpty()) { finish("network"); return; }
                QFile key(":/update-public.der");
                if (!key.open(QIODevice::ReadOnly) || !authentic(doc,sig,key.readAll())) { finish("signature"); return; }
                auto index = QJsonDocument::fromJson(doc).object();
                if (index.value("schema").toInt() != 1 || !index.value("packages").isArray()) { finish("format"); return; }
                QVersionNumber best(0,9,0);
                int build = 4;
                bool published = false;
                for (const auto &row : index.value("packages").toArray()) {
                    auto entry = row.toObject();
                    if (entry.value("platform").toString() != "windows-x64") continue;
                    const auto v = entry.value("version").toString();
                    static const QRegularExpression semver("^[0-9]+\\.[0-9]+\\.[0-9]+$");
                    if (!semver.match(v).hasMatch() || entry.value("build").toInt() < 1) { finish("format"); return; }
                    published = true;
                    auto candidate = QVersionNumber::fromString(v);
                    int candidateBuild = entry.value("build").toInt();
                    if (candidate > best || (candidate == best && candidateBuild > build)) {
                        best = candidate; build = candidateBuild;
                        available = v + " · " + QString::number(build);
                    }
                }
                finish(!available.isEmpty() ? "new" : published ? "current" : "unpublished");
            });
        });
    }
signals:
    void changed();
private:
    using Callback = std::function<void(QByteArray)>;
    void finish(const QString &s) { result = s; emit changed(); }
    void fetch(const QString &name, bool migrated, Callback done) {
        const auto base = migrated ? "https://deckivo.remteh.by/updates/" : "https://remteh-by.github.io/remteh-remote-play/updates/";
        QNetworkRequest request{QUrl(base + name)};
        request.setTransferTimeout(10000);
        request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,QNetworkRequest::ManualRedirectPolicy);
        auto reply = network.get(request);
        const int limit = name.endsWith(".json") ? 65536 : 1024;
        reply->setReadBufferSize(limit + 1);
        connect(reply,&QIODevice::readyRead,reply,[reply,limit]{ if (reply->bytesAvailable() > limit) reply->abort(); });
        connect(reply,&QNetworkReply::finished,this,[this,reply,name,migrated,limit,done]{
            reply->deleteLater();
            auto dest = reply->attribute(QNetworkRequest::RedirectionTargetAttribute).toUrl();
            if (!migrated && dest == QUrl("https://deckivo.remteh.by/updates/" + name)) {
                fetch(name,true,done); return;
            }
            if (reply->error() != QNetworkReply::NoError || reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt() != 200
                || reply->bytesAvailable() > limit) { done({}); return; }
            done(reply->readAll());
        });
    }
    QNetworkAccessManager network{this};
    QString result, available;
};
