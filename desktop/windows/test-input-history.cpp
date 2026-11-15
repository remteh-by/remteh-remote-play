#include "windows_tools.h"
#include <QApplication>
#include <QTemporaryDir>
#include <cassert>
#include <iostream>
static QByteArray readFile(const QString &p) {
    QFile f(p); assert(f.open(QIODevice::ReadOnly)); return f.readAll();
}
int main(int argc, char **argv) {
    QApplication app(argc,argv);
    QTemporaryDir local;
    assert(local.isValid());
    app.setOrganizationName("Deckivo-Tests"); app.setApplicationName(QUuid::createUuid().toString());
    QStandardPaths::setTestModeEnabled(true);
    auto store = Deckivo::path("windows-session-history");
    assert(!QFile::exists(store));
    QDir().mkpath(QFileInfo(store).absolutePath());
    using namespace DeckivoInput;
    for (const QSize size : {QSize(2560,1440),QSize(620,450)}) {
        State state;
        state.keys = {Qt::Key_W, Qt::Key_A}; state.aim = QPoint(17000,-5000);
        state.mouseButtons.insert(0, CHIAKI_CONTROLLER_ANALOG_BUTTON_R2);
        auto sample = state.snapshot(size);
        assert(sample.left_x == -32767 && sample.left_y == -32767 && sample.right_x == 17000 && sample.r2_state == 255);
        state.keys.insert(Qt::Key_D); assert(state.snapshot(size).left_x == 0);
        state = {};
        for (int i = 0; i < int(std::size(overlay)); ++i) {
            auto p = center(overlay[i],size);
            state.contact(19,p,size,true);
            assert(state.contacts.value(19).control == i);
            if (overlay[i].action < 0) {
                state.contact(19,p+QPointF(unit(size),0),size,false);
                auto s=state.snapshot(size);
                assert((overlay[i].action==LeftStick?s.left_x:s.right_x) == 32767);
            }
            state.contacts.clear();
        }
        state.contact(3,center(overlay[11],size),size,true);
        state.contact(4,center(overlay[2],size),size,true);
        auto s=state.snapshot(size); assert((s.buttons&CHIAKI_CONTROLLER_BUTTON_CROSS) && s.r2_state==255);
        state.contacts.remove(3); assert(state.snapshot(size).buttons==0 && state.snapshot(size).r2_state==255);
    }
    auto doc=readFile("website/updates/index.json");
    auto sig=readFile("website/updates/index.sig");
    auto key=readFile("design-system/update-public.der");
    assert(WindowsUpdate::authentic(doc,sig,key));
    assert(!WindowsUpdate::authentic(doc+"x",sig,key));
    {
        QSettings old(store,Deckivo::format()); old.setValue("history",QStringList{"old record"}); old.sync();
        WindowsTools tools(nullptr);
        assert(tools.sessions().size()==1);
        tools.connected(1080,60); tools.disconnected(456);
        assert(tools.sessions().at(0).toMap().value("height")==1080);
        assert(tools.sessions().at(0).toMap().value("frames")==456);
        assert(tools.sessions().at(1).toMap().value("legacy")=="old record");
        tools.setRemember(false); tools.connected(720,30); tools.disconnected(120);
        assert(tools.sessions().size()==2); tools.setSensitivity(140); tools.setInvert(true); tools.mapMouse(0,1);
        tools.clearHistory(); assert(tools.sessions().isEmpty());
    }
    { WindowsTools reopened(nullptr); assert(reopened.invert() && reopened.sensitivity()==140 && reopened.mouseActions().at(0)==1 && !reopened.remember()); }
    assert(QFile::remove(store));
    std::cout<<"PASS: input and multitouch at two sizes, signed catalog and tampering, new and legacy history, settings persistence\n";
}
