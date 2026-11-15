// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
#pragma once

#include <chiaki/controller.h>
#include <QPointF>
#include <QLineF>
#include <QSize>
#include <QHash>
#include <iterator>
#include <QSet>
#include <QVariantList>
#include <QVector2D>
#include <algorithm>
#include <cmath>

namespace DeckivoInput {
enum Axis { LeftStick = -1, RightStick = -2 };
struct Control { const char *label; int action; double x, y; bool right; };
inline constexpr Control overlay[] = {
    {"L2", CHIAKI_CONTROLLER_ANALOG_BUTTON_L2, 0.7, 3.8, false},
    {"L1", CHIAKI_CONTROLLER_BUTTON_L1, 1.65, 3.8, false},
    {"R2", CHIAKI_CONTROLLER_ANALOG_BUTTON_R2, 0.7, 3.8, true},
    {"R1", CHIAKI_CONTROLLER_BUTTON_R1, 1.65, 3.8, true},
    {"↑", CHIAKI_CONTROLLER_BUTTON_DPAD_UP, 1.5, 2.97, false},
    {"←", CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT, 0.76, 2.22, false},
    {"→", CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT, 2.24, 2.22, false},
    {"↓", CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN, 1.5, 1.47, false},
    {"△", CHIAKI_CONTROLLER_BUTTON_PYRAMID, 1.5, 2.97, true},
    {"○", CHIAKI_CONTROLLER_BUTTON_MOON, 0.76, 2.22, true},
    {"□", CHIAKI_CONTROLLER_BUTTON_BOX, 2.24, 2.22, true},
    {"×", CHIAKI_CONTROLLER_BUTTON_CROSS, 1.5, 1.47, true},
    {"LS", LeftStick, 3.45, 1.3, false}, {"RS", RightStick, 3.45, 1.3, true},
    {"L3", CHIAKI_CONTROLLER_BUTTON_L3, 3.45, 2.75, false},
    {"R3", CHIAKI_CONTROLLER_BUTTON_R3, 3.45, 2.75, true},
    {"PS", CHIAKI_CONTROLLER_BUTTON_PS, 1.2, 0.55, false},
    {"☰", CHIAKI_CONTROLLER_BUTTON_OPTIONS, 1.2, 0.55, true},
    {"▭", CHIAKI_CONTROLLER_BUTTON_TOUCHPAD, 2.24, 0.55, true},
    {"SH", CHIAKI_CONTROLLER_BUTTON_SHARE, 2.24, 0.55, false}
};
inline double unit(QSize size) { return std::min({72.0, size.width()/9.4, size.height()/7.5}); }
inline double radius(const Control &c) { return c.action < 0 ? 0.92 : 0.405; }
inline QPointF center(const Control &c, QSize size) {
    const auto u = unit(size);
    return {c.right ? size.width() - c.x * u : c.x * u, size.height() - c.y * u};
}
inline QVariantList controls() {
    QVariantList list;
    for (const auto &c : overlay)
        list.append(QVariantMap{{"label",QString::fromUtf8(c.label)},{"x",c.x},{"y",c.y},{"right",c.right},{"radius",radius(c)}});
    return list;
}
struct Contact { int control; QPointF position; };
class State {
public:
    QHash<int, Contact> contacts;
    QSet<int> keys;
    QHash<int, int> mouseButtons;
    QPoint aim;
    void contact(int id, QPointF pos, QSize size, bool start) {
        if (start) {
            for (int i = 0; i < int(std::size(overlay)); ++i)
                if (QLineF(pos, center(overlay[i], size)).length() <= radius(overlay[i]) * unit(size)) {
                    contacts.insert(id, {i,pos}); break;
                }
        } else if (contacts.contains(id)) contacts[id].position = pos;
    }
    ChiakiControllerState snapshot(QSize size) const {
        ChiakiControllerState s;
        chiaki_controller_state_set_idle(&s);
        s.left_x = (int(keys.contains(Qt::Key_D)) - int(keys.contains(Qt::Key_A))) * 32767;
        s.left_y = (int(keys.contains(Qt::Key_S)) - int(keys.contains(Qt::Key_W))) * 32767;
        s.right_x = aim.x(); s.right_y = aim.y();
        auto press = [&s](int action) {
            if (action == CHIAKI_CONTROLLER_ANALOG_BUTTON_L2) s.l2_state = 255;
            else if (action == CHIAKI_CONTROLLER_ANALOG_BUTTON_R2) s.r2_state = 255;
            else if (action > 0) s.buttons |= uint32_t(action);
        };
        for (const auto action : mouseButtons) press(action);
        for (const auto &contact : contacts) {
            const auto &c = overlay[contact.control];
            if (c.action > 0) { press(c.action); continue; }
            QVector2D v((contact.position - center(c,size)) / std::max(1.0, radius(c)*unit(size)));
            if (v.lengthSquared() > 1) v.normalize();
            auto &x = c.action == LeftStick ? s.left_x : s.right_x;
            auto &y = c.action == LeftStick ? s.left_y : s.right_y;
            x = qRound(v.x()*32767); y = qRound(v.y()*32767);
        }
        return s;
    }
};
}
