"""Generate compact/wide native Deckivo shells using the shared visual language."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'android/app/src/main/res'
NS='xmlns:android="http://schemas.android.com/apk/res/android" xmlns:app="http://schemas.android.com/apk/res-auto"'

def text(value,size=14,color='deckivo_text',extra=''):
 size=max(size,12)
 return f'<TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="{value}" android:textSize="{size}sp" android:fontFamily="@font/ibm_plex_sans" android:textColor="@color/{color}" {extra}/>'
def btn(id,label,icon=None,extra=''):
 return f'<com.google.android.material.button.MaterialButton android:id="@+id/{id}" style="@style/Deckivo.Button.Secondary" android:layout_width="match_parent" android:layout_height="48dp" android:text="{label}" android:maxLines="2" '+(f'app:icon="@drawable/{icon}" app:iconSize="20dp" ' if icon else '')+extra+'/>'
nav=[('navPlay','@string/dv_play','ic_deckivo_play'),('navSetup','@string/dv_controller','ic_deckivo_link'),('navUpdates','@string/dv_sessions','ic_log'),('navSettings','@string/dv_settings','ic_settings')]
quality='<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:padding="14dp" android:background="@drawable/deckivo_panel">'+text('@string/dv_quality',17)+btn('qualityFast','@string/dv_quality_smooth',extra='android:textSize="12sp" android:layout_marginTop="8dp"')+btn('qualityBalanced','@string/dv_quality_balanced',extra='android:textSize="12sp" android:layout_marginTop="6dp"')+btn('qualitySafe','@string/dv_quality_safe',extra='android:textSize="12sp" android:layout_marginTop="6dp"')+text('@string/dv_requested_fps',11,'deckivo_muted','android:layout_marginTop="8dp"')+'</LinearLayout>'
pad='<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:padding="14dp" android:background="@drawable/deckivo_panel" android:layout_marginTop="12dp">'+text('@string/dv_controller',17)+btn('controllerTestButton','@string/dv_test_controller',extra='android:layout_marginTop="8dp" android:textSize="12sp"')+'</LinearLayout>'
for wide in (False,True):
 root=f'<LinearLayout {NS} android:id="@+id/rootLayout" android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="'+('horizontal' if wide else 'vertical')+'" android:background="@color/deckivo_bg">'
 if wide:
  root+='<LinearLayout android:layout_width="76dp" android:layout_height="match_parent" android:orientation="vertical" android:padding="10dp" android:background="@color/deckivo_rail"><ImageView android:layout_width="48dp" android:layout_height="58dp" android:src="@drawable/ic_deckivo" android:importantForAccessibility="no"/>'
  for id,label,ic in nav:root+=btn(id,'',ic,extra=f'android:contentDescription="{label}" android:layout_marginTop="8dp" android:paddingStart="8dp" android:paddingEnd="8dp" app:iconPadding="0dp" app:iconGravity="textStart"')
  root+='<Space android:layout_width="1dp" android:layout_height="0dp" android:layout_weight="1"/>'+text('',10,'deckivo_muted','android:id="@+id/buildVersion"')+'</LinearLayout>'
 root+='<LinearLayout android:layout_width="'+('0dp' if wide else 'match_parent')+'" '+('android:layout_weight="1" ' if wide else '')+'android:layout_height="'+('match_parent' if wide else '0dp')+'" '+('' if wide else 'android:layout_weight="1" ')+'android:orientation="vertical" android:padding="16dp">'
 root+='<LinearLayout android:layout_width="match_parent" android:layout_height="56dp" android:gravity="center_vertical" android:orientation="horizontal">'
 root+=text('@string/dv_room',26,extra='android:layout_weight="1"').replace('android:layout_width="match_parent"','android:layout_width="0dp"')
 root+='<com.google.android.material.button.MaterialButton android:id="@+id/languageButton" style="@style/Deckivo.Button.Secondary" android:layout_width="wrap_content" android:layout_height="48dp" android:text="@string/dv_language" android:contentDescription="@string/dv_language" android:textSize="12sp"/>'
 for id,ic,label in [('addConsoleButton','ic_add','@string/dv_add'),('updatesButton','ic_log','@string/dv_updates')]:
  root+=f'<com.google.android.material.button.MaterialButton android:id="@+id/{id}" style="@style/Deckivo.Button.Secondary" android:layout_width="48dp" android:layout_height="48dp" android:contentDescription="{label}" app:icon="@drawable/{ic}" app:iconSize="20dp" app:iconPadding="0dp" android:paddingStart="8dp" android:paddingEnd="8dp" android:layout_marginStart="6dp"/>'
 root+='</LinearLayout><LinearLayout android:layout_width="match_parent" android:layout_height="40dp" android:gravity="center_vertical">'
 root+=text('@string/dv_consoles_network',12,'deckivo_muted','android:id="@+id/libraryStatus" android:layout_weight="1"').replace('android:layout_width="match_parent"','android:layout_width="0dp"')
 root+='<com.google.android.material.button.MaterialButton android:id="@+id/discoveryButton" style="@style/Deckivo.Button.Secondary" android:layout_width="wrap_content" android:layout_height="40dp" android:text="@string/dv_discovery_on" android:textSize="10sp" app:icon="@drawable/ic_discover_on" app:iconSize="16dp"/></LinearLayout>'
 root+='<LinearLayout android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:orientation="horizontal"><FrameLayout android:layout_width="0dp" android:layout_weight="'+('2' if wide else '1')+'" android:layout_height="match_parent"><androidx.recyclerview.widget.RecyclerView android:id="@+id/hostsRecyclerView" android:layout_width="match_parent" android:layout_height="match_parent" android:clipToPadding="false" android:paddingTop="10dp" android:paddingBottom="12dp"/><LinearLayout android:id="@+id/emptyInfoLayout" android:layout_width="match_parent" android:layout_height="wrap_content" android:layout_gravity="center" android:orientation="vertical" android:padding="20dp" android:background="@drawable/deckivo_panel">'+text('@string/dv_empty_title',22)+text('@string/dv_empty_intro',14,'deckivo_muted','android:id="@+id/emptyInfoTextView" android:layout_marginTop="12dp"')+'</LinearLayout></FrameLayout>'
 root+='<ScrollView android:layout_width="'+('0dp' if wide else '1dp')+'" '+('android:layout_weight="1" ' if wide else 'android:visibility="gone" ')+'android:layout_height="match_parent" android:layout_marginStart="14dp" android:scrollbars="none"><LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:paddingTop="10dp">'+quality+pad+'</LinearLayout></ScrollView></LinearLayout>'
 root+=text('@string/dv_update_ready',13,'accent','android:id="@+id/updateStatus" android:visibility="gone" android:clickable="true" android:focusable="true" android:minHeight="44dp" android:gravity="center_vertical"')
 root+='<LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="horizontal" android:gravity="center_vertical">'+text('@string/dv_developer_credit',12,'deckivo_muted','android:id="@+id/developerCredit" android:layout_weight="1" android:clickable="true" android:focusable="true" android:minHeight="44dp" android:gravity="center_vertical"').replace('android:layout_width="match_parent"','android:layout_width="0dp"')+btn('supportButton','@string/dv_support_link',extra='android:contentDescription="@string/dv_support" android:layout_marginStart="8dp"').replace('android:layout_width="match_parent"','android:layout_width="wrap_content"')+'</LinearLayout></LinearLayout>'
 if not wide:
  root+='<LinearLayout android:layout_width="match_parent" android:layout_height="64dp" android:padding="8dp" android:background="@color/deckivo_rail">'
  for id,label,ic in nav:
   root+=btn(id,'',ic,extra=f'android:contentDescription="{label}" android:layout_weight="1" android:paddingStart="8dp" android:paddingEnd="8dp" app:iconPadding="0dp" app:iconGravity="textStart"').replace('android:layout_width="match_parent"','android:layout_width="0dp"')
  root+='</LinearLayout>'
 root+='</LinearLayout>'
 folder=R/('layout-w600dp' if wide else 'layout');folder.mkdir(exist_ok=True);(folder/'activity_main.xml').write_text(root)
item=f'''<com.google.android.material.card.MaterialCardView {NS} android:layout_width="match_parent" android:layout_height="wrap_content" android:layout_marginBottom="14dp" app:cardBackgroundColor="@color/deckivo_surface" app:cardCornerRadius="24dp" app:strokeColor="@color/deckivo_border" app:strokeWidth="1dp" app:cardElevation="0dp" android:focusable="false"><LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="vertical" android:padding="20dp"><LinearLayout android:layout_width="match_parent" android:layout_height="36dp" android:gravity="center_vertical"><TextView android:id="@+id/statusText" android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content" android:textColor="@color/accent" android:textSize="12sp"/><androidx.appcompat.widget.AppCompatImageButton android:id="@+id/menuButton" android:layout_width="40dp" android:layout_height="40dp" android:src="@drawable/ic_overflow" app:tint="@color/deckivo_muted" android:background="?attr/selectableItemBackgroundBorderless" android:contentDescription="@string/dv_console_options"/></LinearLayout><LinearLayout android:layout_width="match_parent" android:layout_height="250dp" android:orientation="horizontal"><LinearLayout android:layout_width="0dp" android:layout_weight="1.25" android:layout_height="match_parent" android:orientation="vertical">{text('@string/dv_ps5_model',12,'deckivo_muted','android:id="@+id/modelText" android:letterSpacing="0.12"')}{text('@string/dv_hero_title',26,extra='android:layout_marginTop="12dp"') }<Space android:layout_width="1dp" android:layout_height="0dp" android:layout_weight="1"/>{text('',18,extra='android:id="@+id/nameTextView" android:maxLines="2" android:ellipsize="end"')}{text('',11,'deckivo_muted','android:id="@+id/hostTextView" android:layout_marginTop="6dp"')}{text('',11,'deckivo_muted','android:id="@+id/bottomInfoTextView" android:maxLines="1" android:ellipsize="end" android:layout_marginTop="6dp"')}</LinearLayout><ImageView android:id="@+id/consoleImage" android:layout_width="0dp" android:layout_weight="1" android:layout_height="match_parent" android:layout_marginStart="8dp" android:src="@drawable/play_space" android:scaleType="fitCenter" android:importantForAccessibility="no"/></LinearLayout><com.google.android.material.button.MaterialButton android:id="@+id/playButton" style="@style/Deckivo.Button" android:layout_width="match_parent" android:layout_height="50dp" android:layout_marginTop="16dp" android:text="@string/dv_play" app:icon="@drawable/ic_deckivo_play"/></LinearLayout></com.google.android.material.card.MaterialCardView>'''
(R/'layout/item_display_host.xml').write_text(item)
print('Native compact/wide shells and own-illustration console card generated.')
# Eliminate weighted ancestors: the outer shell and columns use constraints.
import xml.etree.ElementTree as ET
ANDROID='http://schemas.android.com/apk/res/android';APP='http://schemas.android.com/apk/res-auto'
ET.register_namespace('android',ANDROID);ET.register_namespace('app',APP)
def a(name):return '{'+ANDROID+'}'+name
def c(name):return '{'+APP+'}layout_constraint'+name
for wide in (False,True):
 path=R/('layout-w600dp' if wide else 'layout')/'activity_main.xml';root=ET.fromstring(path.read_text());root.tag='FrameLayout'
 main=root[1] if wide else root[0]
 main.attrib.pop(a('layout_weight'),None);main.set(a('layout_width'),'match_parent');main.set(a('layout_height'),'match_parent')
 if wide:main.set(a('layout_marginStart'),'76dp')
 else:
  main.set(a('layout_marginBottom'),'64dp');root[1].set(a('layout_gravity'),'bottom')
  main.append(ET.Element('TextView',{a('id'):'@+id/buildVersion',a('layout_width'):'0dp',a('layout_height'):'0dp',a('visibility'):'gone'}))
 columns=next(x for x in main if x.get(a('orientation'))=='horizontal' and x.get(a('layout_height'))=='0dp')
 columns.tag='androidx.constraintlayout.widget.ConstraintLayout'
 split=ET.SubElement(columns,'androidx.constraintlayout.widget.Guideline',{a('id'):'@+id/columnsGuideline',a('layout_width'):'wrap_content',a('layout_height'):'wrap_content',a('orientation'):'vertical','{'+APP+'}layout_constraintGuide_percent':'0.66' if wide else '1.0'})
 for i,column in enumerate(list(columns)[:2]):
  column.attrib.pop(a('layout_weight'),None);column.set(a('layout_width'),'0dp');column.set(a('layout_height'),'0dp')
  column.set(c('Top_toTopOf'),'parent');column.set(c('Bottom_toBottomOf'),'parent')
  column.set(c('Start_toStartOf'),'parent' if i==0 else '@id/columnsGuideline');column.set(c('End_toStartOf'),'@id/columnsGuideline') if i==0 else column.set(c('End_toEndOf'),'parent')
 for node in root.iter():
  if node.tag=='LinearLayout' and node.get(a('orientation'),'horizontal')=='horizontal':node.set(a('baselineAligned'),'false')
  if node.get(a('textSize'))=='10sp':node.set(a('textSize'),'12sp')
 ET.indent(root);path.write_text(ET.tostring(root,encoding='unicode'))
path=R/'layout/item_display_host.xml';root=ET.fromstring(path.read_text());row=next(x for x in root.iter('LinearLayout') if x.get(a('layout_height'))=='250dp');row.tag='androidx.constraintlayout.widget.ConstraintLayout'
for i,column in enumerate(list(row)):
 column.attrib.pop(a('layout_weight'),None);column.set(a('layout_width'),'0dp');column.set(a('layout_height'),'0dp');column.set(c('Top_toTopOf'),'parent');column.set(c('Bottom_toBottomOf'),'parent')
 column.set(c('Start_toStartOf'),'parent' if i==0 else '@id/cardGuideline')
 column.set(c('End_toStartOf'),'@id/cardGuideline') if i==0 else column.set(c('End_toEndOf'),'parent')
ET.SubElement(row,'androidx.constraintlayout.widget.Guideline',{a('id'):'@+id/cardGuideline',a('layout_width'):'wrap_content',a('layout_height'):'wrap_content',a('orientation'):'vertical','{'+APP+'}layout_constraintGuide_percent':'0.54'})
for node in root.iter():
 if node.tag=='LinearLayout' and node.get(a('orientation'),'horizontal')=='horizontal':node.set(a('baselineAligned'),'false')
ET.indent(root);path.write_text(ET.tostring(root,encoding='unicode'))
