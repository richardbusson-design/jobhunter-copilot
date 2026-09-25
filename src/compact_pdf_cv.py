# -*- coding: utf-8 -*-
import re, html as H, sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor, white
S='/tmp/claude-0/-home-user-jobhunter-copilot/2e9d9f5c-51d9-5430-991a-31bd2053a5dc/scratchpad'
SRC='candidatures/2026-09-25_CNAM_Hauts-de-France_Vivier_formateurs_RH_Paie/CV_Richard_BUSSON.html'
src=open(SRC,encoding='utf-8').read()
def txt(s):
    s=re.sub(r'<strong>(.*?)</strong>',r'<b>\1</b>',s,flags=re.S)
    s=re.sub(r'<br\s*/?>','<br/>',s)
    s=re.sub(r'<(?!/?b>|br/>)[^>]+>','',s)
    s=H.unescape(re.sub(r'\s+',' ',s)).strip()
    return s.replace('&','&amp;').replace('&amp;amp;','&amp;')
def grab(pat,flags=re.S):
    m=re.search(pat,src,flags); return m.group(1) if m else ''
title=txt(grab(r'class="title-sub">(.*?)</div>'))
spec=txt(grab(r'class="specialties">(.*?)</div>'))
profil=txt(grab(r'class="profil-text">(.*?)</div>'))
dipl=[(txt(a),txt(b),txt(c)) for a,b,c in re.findall(r'class="diplome-nom">(.*?)</div>\s*<div class="diplome-univ">(.*?)</div>\s*<div class="diplome-desc">(.*?)</div>',src,re.S)]
badges=[txt(b) for b in re.findall(r'class="badge-skill[^"]*">(.*?)</div>',src,re.S)]
meth=txt(grab(r'class="didactique-box">(.*?)</div>'))
tools=txt(grab(r'class="tools-box">(.*?)</div>'))
senior=txt(grab(r'class="card-senior">(.*?)</div>'))
exps=[]
for card in re.findall(r'<div class="exp-card">(.*?)</ul>\s*</div>',src,re.S):
    poste=txt(re.search(r'class="exp-poste">(.*?)</span>',card,re.S).group(1))
    dates=txt(re.search(r'class="exp-dates">(.*?)</span>',card,re.S).group(1))
    ent=re.search(r'class="exp-entreprise">\s*<span>(.*?)</span>\s*<span class="exp-lieu">(.*?)</span>',card,re.S)
    bullets=[txt(b) for b in re.findall(r'<li>(.*?)</li>',card,re.S)]
    exps.append((poste,dates,txt(ent.group(1)),txt(ent.group(2)),bullets))
boxes=[(txt(h),txt(p)) for h,p in re.findall(r'<div class="(?:focus|values|mobility)-box">\s*<h4>(.*?)</h4>\s*<p>(.*?)</p>',src,re.S)]
boxcol=[('#eff6ff','#2563eb','#1d4ed8','#1e40af'),('#f0fdf4','#16a34a','#15803d','#166534'),('#fefce8','#ca8a04','#a16207','#854d0e')]

NAVY=HexColor('#122b4d'); GOLD=HexColor('#d4af37'); YEL=HexColor('#facc15'); BLUE=HexColor('#1b365d')
GREY=HexColor('#f8fafc'); LINE=HexColor('#cbd5e1'); TXT=HexColor('#334155'); MUT=HexColor('#64748b')
W,Hh=A4
def build(k, out, kr=None):
    kr = kr or k
    c=canvas.Canvas(out,pagesize=A4,pageCompression=1)
    c.setTitle('CV Richard BUSSON - Formateur RH, Paie et Droit social'); c.setAuthor('Richard Busson')
    # header
    HH=78
    c.setFillColor(NAVY); c.rect(0,Hh-HH,W,HH,stroke=0,fill=1)
    c.setFillColor(GOLD); c.rect(0,Hh-HH-2.5,W,2.5,stroke=0,fill=1)
    c.setFillColor(white); c.setFont('Helvetica-Bold',18); c.drawString(16,Hh-24,'RICHARD BUSSON')
    c.setFillColor(YEL); c.setFont('Helvetica-Bold',9.2); c.drawString(16,Hh-38,H.unescape(title).replace('&amp;','&'))
    c.setFillColor(HexColor('#e2e8f0')); c.setFont('Helvetica',7.4); c.drawString(16,Hh-50,H.unescape(spec).replace('&amp;','&'))
    # contact block
    bx=W-16-196; by=Hh-HH+6
    c.setFillColor(HexColor('#2a4468')); c.roundRect(bx,by,196,HH-12,4,stroke=0,fill=1)
    c.setFillColor(HexColor('#16a34a')); c.roundRect(bx+196-108,Hh-20,100,11,5,stroke=0,fill=1)
    c.setFillColor(white); c.setFont('Helvetica-Bold',6.4); c.drawCentredString(bx+196-58,Hh-16.8,'DISPONIBILITÉ IMMÉDIATE')
    c.setFont('Helvetica',7.2); c.setFillColor(HexColor('#f8fafc'))
    c.drawRightString(bx+188,Hh-32,'98, allée Paul Cézanne, 60100 Creil')
    c.setFont('Helvetica-Bold',7.2); c.setFillColor(YEL); c.drawRightString(bx+188,Hh-43,'07 61 96 15 46 · 09 39 20 08 70')
    c.drawRightString(bx+188,Hh-54,'richard.busson@kairos-paye.fr')
    c.setFont('Helvetica',7.2); c.setFillColor(HexColor('#f8fafc')); c.drawRightString(bx+188,Hh-65,'linkedin.com/in/richard-busson · Permis B')
    # columns
    top=Hh-HH-2.5; LW=208; c.setFillColor(GREY); c.rect(0,0,LW,top,stroke=0,fill=1)
    c.setStrokeColor(LINE); c.setLineWidth(1); c.line(LW,0,LW,top)
    f=k  # scale factor
    st=lambda name,size,lead,col=TXT,al=TA_JUSTIFY,font='Helvetica': ParagraphStyle(name,fontName=font,fontSize=size*f,leading=lead*f,textColor=col,alignment=al)
    def para(text,style,x,y,w):
        p=Paragraph(text,style); _,h=p.wrap(w,2000); p.drawOn(c,x,y-h); return y-h
    def sec(num,label,x,y,w):
        c.setFillColor(BLUE); c.rect(x,y-9,10,10,stroke=0,fill=1)
        c.setFillColor(white); c.setFont('Helvetica-Bold',6.5); c.drawCentredString(x+5,y-6.6,str(num))
        c.setFillColor(BLUE); c.setFont('Helvetica-Bold',8.2); c.drawString(x+14,y-7.5,label.upper())
        c.setStrokeColor(BLUE); c.setLineWidth(1.2); c.line(x,y-12,x+w,y-12); return y-17
    def card(x,y,w,h,fill,border,left):
        c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(border)); c.setLineWidth(0.6)
        c.roundRect(x,y-h,w,h,3,stroke=1,fill=1); c.setFillColor(HexColor(left)); c.rect(x,y-h+1,2.4,h-2,stroke=0,fill=1)
    # LEFT
    x=12; w=LW-24; y=top-10; gap=6*f
    y=sec(1,'Démarche pédagogique',x,y,w)
    p=Paragraph(profil,st('pr',6.6,8.6)); _,h=p.wrap(w-12,2000); card(x,y,w,h+10,'#ffffff','#e2e8f0','#1b365d'); p.drawOn(c,x+7,y-5-h); y-=h+10+gap
    y=sec(2,'Diplômes supérieurs',x,y,w)
    for a,b,d in dipl:
        pa=Paragraph(a,st('dn',6.9,8.4,BLUE,TA_LEFT,'Helvetica-Bold')); pb=Paragraph(b,st('du',6,7.4,MUT,TA_LEFT,'Helvetica-Bold')); pd=Paragraph(d,st('dd',5.9,7.2,HexColor('#475569'),TA_LEFT))
        hs=[q.wrap(w-12,2000)[1] for q in (pa,pb,pd)]; hh=sum(hs)+7
        card(x,y,w,hh,'#ffffff','#e2e8f0','#0284c7'); yy=y-3.5
        for q,hq in zip((pa,pb,pd),hs): q.drawOn(c,x+7,yy-hq); yy-=hq
        y-=hh+3.4*f
    y-=gap-3.4*f
    y=sec(3,"Domaines d'enseignement",x,y,w)
    # badges flow
    bx0=x+6; by=y-4; bxx=bx0; rowh=10.5*f; maxw=w-12; c.setFont('Helvetica-Bold',6.0*f)
    lines=[[]]; 
    for i,bd in enumerate(badges):
        t=H.unescape(bd).replace('&amp;','&'); tw=c.stringWidth(t,'Helvetica-Bold',6.0*f)+8
        if lines[-1] and sum(l[1]+3 for l in lines[-1])+tw>maxw: lines.append([])
        lines[-1].append((t,tw,i in (0,1,5)))
    hb=len(lines)*rowh+8; card(x,y,w,hb,'#ffffff','#e2e8f0','#d97706')
    yy=y-4
    for ln in lines:
        xx=bx0
        for t,tw,acc in ln:
            c.setFillColor(HexColor('#fef3c7' if acc else '#e0e7ff')); c.setStrokeColor(HexColor('#fde68a' if acc else '#c7d2fe')); c.setLineWidth(0.5)
            c.roundRect(xx,yy-rowh+2,tw,rowh-2.5,2,stroke=1,fill=1)
            c.setFillColor(HexColor('#78350f' if acc else '#1e1b4b')); c.setFont('Helvetica-Bold',6.0*f); c.drawString(xx+4,yy-rowh+4.6,t); xx+=tw+3
        yy-=rowh
    y-=hb+gap
    y=sec(4,'Méthodes & pédagogie active',x,y,w)
    p=Paragraph(meth,st('me',6.5,8.4,TXT,TA_LEFT)); _,h=p.wrap(w-12,2000); card(x,y,w,h+9,'#ffffff','#e2e8f0','#7c3aed'); p.drawOn(c,x+7,y-4.5-h); y-=h+9+gap
    y=sec(5,'Outils & environnement numérique',x,y,w)
    p=Paragraph(tools,st('to',6.5,8.4,TXT,TA_LEFT)); _,h=p.wrap(w-12,2000); card(x,y,w,h+9,'#ffffff','#e2e8f0','#0ea5e9'); p.drawOn(c,x+7,y-4.5-h); y-=h+9+gap
    p=Paragraph(senior.replace('<b>','<font color="#facc15"><b>').replace('</b>','</b></font>'),st('se',6.5,8.6,white,TA_LEFT)); _,h=p.wrap(w-14,2000)
    c.setFillColor(HexColor('#1b2f4e')); c.roundRect(x,y-h-11,w,h+11,3,stroke=0,fill=1); c.setFillColor(GOLD); c.rect(x,y-h-10,2.6,h+9,stroke=0,fill=1); p.drawOn(c,x+8,y-5.5-h); y-=h+11
    left_bottom=y
    # RIGHT
    f=kr; st=lambda name,size,lead,col=TXT,al=TA_JUSTIFY,font='Helvetica': ParagraphStyle(name,fontName=font,fontSize=size*f,leading=lead*f,textColor=col,alignment=al)
    x=LW+10; w=W-x-12; y=top-10; rgap=7.5*f
    y=sec(6,'Expériences professionnelles & réalisations',x,y,w)
    for poste,dates,ent,lieu,bullets in exps:
        pp=Paragraph(poste,st('po',8.2,10,BLUE,TA_LEFT,'Helvetica-Bold')); dw=c.stringWidth(H.unescape(dates),'Helvetica-Bold',7*f)+6
        _,hp=pp.wrap(w-16-dw,2000)
        pe=Paragraph('<i>'+ent+'</i>',st('en',6.9,8.6,HexColor('#475569'),TA_LEFT)); lw=c.stringWidth(H.unescape(lieu),'Helvetica-Bold',6.3*f)+6
        _,he=pe.wrap(w-16-lw,2000)
        bl=[Paragraph('<font color="#1b365d">•</font> '+b,ParagraphStyle('bl',fontName='Helvetica',fontSize=6.6*f,leading=9.1*f,textColor=TXT,alignment=TA_JUSTIFY,leftIndent=7,firstLineIndent=-7,spaceAfter=2*f)) for b in bullets]
        hb=[q.wrap(w-16,2000)[1] for q in bl]
        hh=hp+he+sum(hb)+2*f*len(bl)+11
        card(x,y,w,hh,'#f8fafc','#e2e8f0','#1b365d')
        pp.drawOn(c,x+8,y-5-hp); c.setFillColor(HexColor('#b45309')); c.setFont('Helvetica-Bold',7*f); c.drawRightString(x+w-8,y-5-7*f,H.unescape(dates))
        yy=y-5-hp; pe.drawOn(c,x+8,yy-he); c.setFillColor(MUT); c.setFont('Helvetica-Bold',6.3*f); c.drawRightString(x+w-8,yy-6.3*f,H.unescape(lieu)); yy-=he+1.5
        for q,hq in zip(bl,hb): q.drawOn(c,x+8,yy-hq); yy-=hq+2*f
        y-=hh+rgap
    for (hd,bd),(fill,bord,hc,tc) in zip(boxes,boxcol):
        ph=Paragraph(hd.upper(),st('bh',7.2,9,HexColor(hc),TA_LEFT,'Helvetica-Bold')); pb=Paragraph(bd,st('bb',6.5,8.8,HexColor(tc)))
        _,h1=ph.wrap(w-16,2000); _,h2=pb.wrap(w-16,2000); hh=h1+h2+11
        card(x,y,w,hh,fill,bord,bord); ph.drawOn(c,x+8,y-5-h1); pb.drawOn(c,x+8,y-5-h1-h2-1); y-=hh+rgap
    right_bottom=y+rgap
    c.showPage(); c.save()
    return left_bottom, right_bottom
k=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
kr=float(sys.argv[2]) if len(sys.argv)>2 else k
lb,rb=build(k,S+'/CV_Richard_BUSSON.pdf',kr)
import os; print('scale',k,'left_bottom',round(lb),'right_bottom',round(rb),'size',os.path.getsize(S+'/CV_Richard_BUSSON.pdf'))
