"""Editable SVG design handoff; text and the own screen illustration remain separate editable layers.

No screenshots, account data or network credentials are embedded. These are
reference screens for Figma import, not evidence of an active PS5 connection.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import base64

ROOT=Path(__file__).resolve().parent


def rect(x,y,w,h,fill='#1A1E24',radius=20,stroke='#303640'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def text(x,y,value,size=14,color='#A4ACBA',weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="IBM Plex Sans, sans-serif" font-size="{size}" font-weight="{weight}">{escape(value)}</text>'


def button(x,y,w,value,primary=False):
    fill,fg=('#DAF975','#17200A') if primary else ('#222730','#F3F5F7')
    return '<g aria-label="'+escape(value)+'">'+rect(x,y,w,48,fill,12)+text(x+18,y+30,value,16,fg,600)+'</g>'


def product_image():
    payload=base64.b64encode((ROOT.parent/'assets/play-space.svg').read_bytes()).decode('ascii')
    return '<g id="Deckivo_Own_Illustration_Image"><image x="541" y="140" width="298" height="374" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/svg+xml;base64,'+payload+'"/></g>'



def chrome(title,active):
    body=rect(0,0,1280,720,'#101216',0,'none')+rect(0,0,87,720,'#15181D',0,'none')
    body+='<path d="M30 29H42C67 29 67 57 42 57H30V49H42C56 49 56 37 42 37H30Z" fill="#DAF975"/>'
    for i,glyph in enumerate(('⌂','◇','↶','☷')):
        y=98+i*62
        if i==active:body+=rect(14,y,56,48,'#DAF975',15,'none')
        body+=text(30,y+31,glyph,27,'#17200A' if i==active else '#A4ACBA')
    body+=text(115,52,title,29,'#F3F5F7',600)
    body+=rect(1040,23,105,38,'#222A24',14,'none')+text(1054,47,'● PS5 online',12,'#DAF975')
    body+=text(1162,47,'12:30',14)+text(1224,47,'×',23)
    body+=text(115,700,'Developed by RemTeh.by ↗',13,'#B6C295')
    body+=text(1030,700,'PRIVATE PREVIEW · 0.4',12)
    return body


def home():
    s=chrome('Play space',0)+text(116,91,'A small screen. A whole console.')
    s+=rect(116,112,745,430,'url(#hero)',24,'#3F4944')+'<g clip-path="url(#hero-clip)">'+product_image()+'</g>'
    s+=text(143,150,'PS5 / HOME NETWORK',11,'#B5BDCB',600)
    s+=text(143,213,'Your console.',43,'#F3F5F7',600)+text(143,267,'Your play space.',43,'#F3F5F7',600)
    s+=text(143,305,'Bring your PS5 to the screen you love.')
    s+=text(143,385,'PlayStation 5',17,'#F3F5F7',600)+text(143,415,'Local profile · Registered console',12)
    s+=button(143,434,225,'Let’s play',True)+text(143,518,'Ready when you are',12)
    s+=rect(879,112,373,250)+text(898,150,'Streaming profile',17,'#F3F5F7',600)
    for i,value in enumerate(('Smooth · 720p / 60','Balanced · 720p / 30','Compatibility · 540p / 30')):
        s+=rect(898,163+i*55,335,46,'#293124' if i==0 else '#222730',12,'#DAF975' if i==0 else '#3C4350')+text(912,192+i*55,value,14,'#DAF975' if i==0 else '#F3F5F7')
    s+=text(898,342,'Resolution and FPS are requested targets.',12)
    s+=rect(879,379,373,163)+text(898,421,'Your controller',17,'#F3F5F7',600)+text(898,467,'GameSir / Pro Controller ready',14,'#DAF975')+text(1058,511,'Test inputs ↗',14)
    s+=rect(116,558,1136,77)
    for i,name in enumerate(('Discovery response','Decoded FPS','Session time','Decoded frames')):
        s+=text(140+i*279,584,name,12)+text(140+i*279,617,'—',24,'#F3F5F7',600)
    s+=text(116,665,'D-pad / stick: navigate    A: choose    B: back    L1 / R1: pages',12)
    return s


def controller():
    s=chrome('Controller lab',1)+text(116,91,'Move both sticks and press buttons. Highlights show real Linux input.')
    s+=rect(116,112,744,556)+text(140,153,'GameSir / Pro Controller',17,'#F3F5F7',600)
    s+='''<g id="Live_Controller_Diagram" transform="translate(486 375)">
    <path d="M-110-70C-190-100-233 149-158 110L-95 62Q0 94 95 62L158 110C233 149 190-100 110-70Z" fill="#232A34" stroke="#566070" stroke-width="3"/>
    <circle cx="-103" cy="-19" r="29" fill="#13171D" stroke="#536070" stroke-width="3"/><circle cx="-103" cy="-19" r="16" fill="#DAF975"/>
    <circle cx="58" cy="37" r="29" fill="#13171D" stroke="#536070" stroke-width="3"/><circle cx="58" cy="37" r="16" fill="#DAF975"/>
    </g>'''
    for x,y,name in ((604,333,'Y'),(631,360,'B'),(604,387,'A'),(577,360,'X')):
        s+=f'<circle cx="{x}" cy="{y}" r="13" fill="#161C23" stroke="#6C7787"/>'+text(x-5,y+5,name,13,'#CBD3DF')
    for x,y in ((430,396),(445,411),(430,426),(415,411)):s+=rect(x-7,y-7,14,14,'#667181',3,'none')
    s+=text(140,615,'Raw stick values and pressed buttons appear here.',13)
    s+=text(140,648,'Diagram uses Xbox positions. Printed GameSir labels may differ.',12)
    s+=rect(879,112,373,556)+text(902,152,'YOUR SHORTCUTS',11,'#B5BDCB',600)
    for i,line in enumerate(('Home → PS menu','Capture → touchpad click','Hold + and − for 1.5 s → end stream','Ctrl+Q → end stream')):s+=text(902,196+27*i,line,16,'#F3F5F7',600)
    s+=text(902,348,'Exclusive capture while streaming.',14)+text(902,638,'Input silent? L1+R1, then L2+R2.',12)
    return s


def history():
    s=chrome('Sessions',2)+text(116,91,'Session history stays on this device.')
    s+=rect(116,112,1136,190)+text(142,157,'Your next session starts here.',23,'#F3F5F7',600)
    s+=text(142,197,'Session time, profile and decoded frames are recorded locally.')
    s+=text(142,246,'No sample sessions or invented performance figures.',13)
    s+=text(116,613,'Diagnostics exclude IP addresses, accounts, pairing keys and raw logs.',13)
    s+=button(950,590,302,'Export safe diagnostics')
    return s


def settings():
    s=chrome('Preferences',3)+rect(116,112,559,527)+rect(693,112,559,527)
    s+=text(140,152,'Local network',17,'#F3F5F7',600)+text(140,192,'Console IP address')
    s+=rect(140,207,511,43,'#15191F',10,'#485160')+text(154,235,'Your PS5 address',14,'#F3F5F7')
    s+=text(140,282,'Language')+rect(140,297,511,43,'#15191F',10,'#485160')+text(154,325,'Automatic · system language',14,'#F3F5F7')
    s+=text(140,370,'New Linux features are translated into English and Russian.',12)
    s+=button(140,567,511,'Save preferences',True)+text(717,152,'Preferences',17,'#F3F5F7',600)
    for i,line in enumerate(('Open stream in full screen','Navigate Deckivo with a gamepad','Hold + and − to disconnect safely','Keep a local session history')):
        y=190+i*54;s+=rect(717,y,25,25,'#DAF975',6,'#A1B958')+text(756,y+18,line,14,'#F3F5F7')
    s+=text(717,607,'Change preferences after ending the stream.',12)
    return s


DEFS='''<defs><clipPath id="hero-clip"><rect x="116" y="112" width="745" height="430" rx="24"/></clipPath><linearGradient id="hero"><stop stop-color="#202827"/><stop offset="1" stop-color="#20202E"/></linearGradient>
<radialGradient id="glow"><stop stop-color="#A395FF" stop-opacity=".2"/><stop offset="1" stop-color="#A395FF" stop-opacity="0"/></radialGradient></defs>'''

if __name__=='__main__':
    for name,fn in (('01-play-space',home),('02-controller-lab',controller),('03-sessions',history),('04-preferences',settings)):
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1280" height="720" viewBox="0 0 1280 720"><title>Deckivo Ubuntu · {name}</title>{DEFS}<g id="{name}">{fn()}</g></svg>'
        (ROOT/(name+'.svg')).write_text(svg)
    manifest={'file':'https://www.figma.com/design/IMCnaXKObedKagsDKvPlB0',
              'figma_status':'File created; MCP Starter quota exhausted; browser Terms acceptance awaiting owner. SVG import not completed.',
              'screens':'Four editable SVG screens; home uses one discrete own screen illustration, no flattened UI screenshot.',
              'font':'IBM Plex Sans','colors':{'background':'#101216','surface':'#1A1E24','accent':'#DAF975','secondary':'#AAA0F5'},
              'viewport':[1280,720],'reference_only':True}
    (ROOT/'figma-handoff.json').write_text(json.dumps(manifest,indent=2))
    print('Wrote four editable SVG screens and Figma handoff.')
