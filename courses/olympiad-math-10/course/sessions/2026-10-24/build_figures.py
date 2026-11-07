#!/usr/bin/env python3
"""Draw and validate exact configurations for the ten teacher solutions."""
from html import escape
from math import acos, atan2, cos, degrees, hypot, pi, sin, sqrt
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'figures'
BLACK = '#222222'
GREY = '#929292'
BLUE = '#255a86'
RED = '#a43a30'


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, t):
    return (a[0] * t, a[1] * t)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def norm(a):
    return hypot(*a)


def unit(a):
    return mul(a, 1 / norm(a))


def mid(a, b):
    return mul(add(a, b), .5)


def intersection(a, b, c, d):
    u, v = sub(b, a), sub(d, c)
    return add(a, mul(u, cross(sub(c, a), v) / cross(u, v)))


def project(p, a, b):
    u = sub(b, a)
    return add(a, mul(u, dot(sub(p, a), u) / dot(u, u)))


def circle(a, b, c):
    u, v = sub(b, a), sub(c, a)
    den = 2 * cross(u, v)
    p = ((dot(u, u) * v[1] - dot(v, v) * u[1]) / den,
         (u[0] * dot(v, v) - v[0] * dot(u, u)) / den)
    o = add(a, p)
    return o, norm(p)


def line_circle(a, b, o, r):
    foot = project(o, a, b)
    u = unit(sub(b, a))
    d = sqrt(max(0, r*r - dot(sub(foot, o), sub(foot, o))))
    return sub(foot, mul(u, d)), add(foot, mul(u, d))


def angle(a, b, c):
    u, v = unit(sub(a, b)), unit(sub(c, b))
    return degrees(acos(max(-1, min(1, dot(u, v)))))


def equal(a, b, description):
    assert abs(a-b) <= 1e-7 * max(1, abs(a), abs(b)), (description, a, b)


def cyclic(points, description):
    o, r = circle(*points[:3])
    for p in points[3:]:
        equal(norm(sub(p, o)), r, description)
    return o, r


class Figure:
    def __init__(self, bounds, width=800):
        self.x0, self.y0, self.x1, self.y1 = bounds
        self.pad = 45
        self.scale = (width - 2*self.pad) / (self.x1-self.x0)
        self.width = width
        self.height = (self.y1-self.y0)*self.scale + 2*self.pad
        self.items = []

    def xy(self, p):
        return (self.pad + (p[0]-self.x0)*self.scale,
                self.pad + (self.y1-p[1])*self.scale)

    def line(self, a, b, color=BLACK, dash=False, width=1.8):
        x, y = self.xy(a)
        u, v = self.xy(b)
        dashattr = ' stroke-dasharray="7 5"' if dash else ''
        self.items.append(f'<line x1="{x:.3f}" y1="{y:.3f}" x2="{u:.3f}" y2="{v:.3f}" stroke="{color}" stroke-width="{width}"{dashattr}/>')

    def poly(self, points, color=BLACK, close=False, fill='none', opacity=1):
        coords = ' '.join(f'{x:.3f},{y:.3f}' for x, y in map(self.xy, points))
        tag = 'polygon' if close else 'polyline'
        self.items.append(f'<{tag} points="{coords}" fill="{fill}" fill-opacity="{opacity}" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>')

    def circ(self, o, r, color=GREY, dash=False):
        x, y = self.xy(o)
        dashattr = ' stroke-dasharray="7 5"' if dash else ''
        self.items.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r*self.scale:.3f}" fill="none" stroke="{color}" stroke-width="1.4"{dashattr}/>')

    def arc(self, o, r, first, last, via=None, color=BLUE, dash=False, extend=0):
        a = atan2(first[1]-o[1], first[0]-o[0])
        b = atan2(last[1]-o[1], last[0]-o[0])
        d = (b-a) % (2*pi)
        if via is not None:
            v = (atan2(via[1]-o[1], via[0]-o[0])-a) % (2*pi)
            if v > d:
                d -= 2*pi
        elif d > pi:
            d -= 2*pi
        sign = 1 if d >= 0 else -1
        a -= sign*extend
        d += sign*2*extend
        points = [add(o, (r*cos(a+d*i/120), r*sin(a+d*i/120))) for i in range(121)]
        coords = ' '.join(f'{x:.3f},{y:.3f}' for x, y in map(self.xy, points))
        dashattr = ' stroke-dasharray="7 5"' if dash else ''
        self.items.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.8"{dashattr}/>')

    def label(self, p, text, dx=0, dy=-12, color=BLACK, size=28):
        x, y = self.xy(p)
        if dy >= 20:
            dy += 7
        anchor = 'start' if dx > 3 else 'end' if dx < -3 else 'middle'
        self.items.append(f'<text x="{x+dx:.3f}" y="{y+dy:.3f}" text-anchor="{anchor}" font-family="Times New Roman" font-style="italic" font-size="{size}" fill="{color}" stroke="white" stroke-width="4" paint-order="stroke">{escape(text)}</text>')

    def point(self, p, text, dx=0, dy=-12):
        x, y = self.xy(p)
        self.items.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2.8" fill="{BLACK}"/>')
        self.label(p, text, dx, dy)

    def tick(self, a, b, count=1, color=BLUE):
        u = unit(sub(b, a))
        v = (-u[1], u[0])
        for i in range(count):
            p = add(mid(a, b), mul(u, (i-(count-1)/2)*6/self.scale))
            self.line(sub(p, mul(v, 5/self.scale)), add(p, mul(v, 5/self.scale)), color, width=1.8)

    def right(self, a, p, b, size=10, color=GREY):
        u, v = mul(unit(sub(a, p)), size/self.scale), mul(unit(sub(b, p)), size/self.scale)
        self.poly([add(p,u), add(add(p,u),v), add(p,v)], color)

    def angle(self, a, p, b, radius, text=None, color=BLUE):
        u, v = unit(sub(a,p)), unit(sub(b,p))
        self.arc(p, radius, add(p,mul(u,radius)), add(p,mul(v,radius)), color=color)
        if text:
            direction = unit(add(u,v))
            self.label(add(p,mul(direction,radius+18/self.scale)),text,dy=5,color=color,size=23)

    def save(self, number):
        OUT.mkdir(exist_ok=True)
        content = '\n'.join(self.items)
        (OUT/f'{number:02}.svg').write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height:.3f}" viewBox="0 0 {self.width} {self.height:.3f}">\n'
            f'<rect width="100%" height="100%" fill="white"/>\n{content}\n</svg>\n')


def first():
    O=(0,0); B=(1,0); C=(0,1); A=(-sqrt(3)/2,-.5)
    P=intersection(B,O,A,C)
    equal(angle(A,B,C),60,'1: ABC')
    equal(angle(C,B,O),45,'1: CBO')
    equal(norm(sub(A,P)),norm(sub(P,O)),'1: AP=PO')
    f=Figure((-1.06,-1.06,1.06,1.06))
    f.circ(O,1)
    f.poly([A,B,C],close=True)
    for p in [A,B,C]: f.line(O,p,BLUE,True)
    f.line(B,P,BLUE)
    f.line(A,P,RED,width=2.6); f.line(P,O,RED,width=2.6)
    f.tick(A,P,color=RED); f.tick(P,O,color=RED)
    f.angle(A,B,C,.31,'60°'); f.angle(O,B,C,.18,'45°')
    f.angle(A,O,P,.24,'30°',RED); f.angle(O,A,P,.20,'30°',RED)
    for p,s,dx,dy in [(A,'A',-12,12),(B,'B',12,6),(C,'C',0,-12),(O,'O',12,22),(P,'P',-9,22)]: f.point(p,s,dx,dy)
    f.save(1)


def second():
    A=(0,0); D=(0,4); o1=(.25,2); o2=(-.35,2)
    r1=hypot(.25,2); r2=hypot(.35,2)
    t1=1; t2=2.8
    d1=sqrt(r1*r1-(t1-2)**2); d2=sqrt(r2*r2-(t2-2)**2)
    B=(o1[0]+d1,t1); F=(o1[0]-d1,t1)
    C=(o2[0]+d2,t2); E=(o2[0]-d2,t2)
    K=intersection(A,E,B,F)
    cyclic([A,B,D,F],'2: ABDF'); cyclic([A,C,D,E],'2: ACDE')
    equal(angle(F,A,E),angle(B,D,C),'2: angle hypothesis')
    f=Figure((-2.5,-.25,2.5,4.25))
    f.circ(o1,r1); f.circ(o2,r2,dash=True)
    f.poly([A,B,C,D,E,F],close=True)
    for a,b in [(A,E),(B,F),(C,E)]: f.line(a,b,BLUE,width=2.3)
    for a,b in [(A,D),(B,D),(C,D)]: f.line(a,b,GREY,True)
    f.angle(F,A,E,.65,'α',RED); f.angle(B,D,C,.65,'α',RED)
    for p,s,dx,dy in [(A,'A',5,24),(B,'B',12,6),(C,'C',12,-5),(D,'D',0,-12),(E,'E',-12,0),(F,'F',-12,10),(K,'K',10,24)]: f.point(p,s,dx,dy)
    f.save(2)


def third():
    A=(0,4); B=(6,0); C=(0,0)
    K=(0,24/(norm(sub(A,B))+6))
    o,r=circle(A,B,K)
    L=(2*o[0]-B[0],0); H=project(K,A,B)
    equal(angle(A,B,K),angle(K,B,C),'3: bisector')
    equal(norm(sub(B,C))+norm(sub(C,L)),norm(sub(A,B)),'3: target')
    f=Figure((o[0]-r,-.95,o[0]+r,o[1]+r))
    f.circ(o,r)
    f.poly([A,B,C],close=True)
    f.line(B,K,BLUE); f.line(K,H,RED,True); f.line(K,L,BLUE,True)
    f.right(K,C,B); f.right(K,H,A)
    for a,b in [(B,C),(B,H)]: f.tick(a,b,1,BLUE)
    for a,b in [(A,H),(C,L)]: f.tick(a,b,2,RED)
    for p,s,dx,dy in [(A,'A',-12,0),(B,'B',12,15),(C,'C',-12,20),(K,'K',-12,-4),(L,'L',0,23),(H,'H',12,-8)]: f.point(p,s,dx,dy)
    f.save(3)


def fourth():
    A=(-5,0); C=(5,0); B=(3,5); H=(3,0)
    M=mid(A,H); N=mid(C,H); O,r=circle(B,M,N)
    B0=sub(mul(O,2),B); P=project(O,A,C); S=mid(A,C); H0=project(B0,A,C)
    equal(norm(sub(H0,S)),0,'4: H0=S')
    equal(norm(sub(A,B0)),norm(sub(C,B0)),'4: target')
    f=Figure((-5.2,-1.4,5.2,5.5))
    f.circ(O,r); f.poly([A,B,C],close=True)
    f.line(B,H,BLUE,True); f.line(B,B0,RED)
    f.line(O,P,BLUE,True); f.line(B0,S,BLUE,True)
    f.line(O,M,GREY,True); f.line(O,N,GREY,True)
    f.line(A,B0,GREY,True); f.line(C,B0,GREY,True)
    f.right(B,H,C); f.right(O,P,N)
    f.tick(H,P,1,RED); f.tick(P,S,1,RED)
    for p,s,dx,dy in [(A,'A',-12,6),(C,'C',12,6),(B,'B',6,-12),(H,'H',2,25),(M,'M',-6,25),(N,'N',2,25),(O,'O',-12,-8),(B0,'B₀',0,26),(P,'P',0,-13),(S,'S = H₀',-6,46)]: f.point(p,s,dx,dy)
    f.save(4)


def fifth():
    def polar(d): return (3*cos(d*pi/180),3*sin(d*pi/180))
    B=polar(-35); C=polar(35); N=polar(140); K=polar(230)
    x=norm(sub(K,N)); y=norm(sub(B,C))
    A=add(K,mul(unit(sub(K,B)),x)); D=add(N,mul(unit(sub(N,C)),x))
    L=add(B,mul(unit(sub(K,B)),y)); M=add(C,mul(unit(sub(N,C)),y))
    o,r=cyclic([A,D,M,L],'5: ADML')
    assert norm(sub(B,K))>y and norm(sub(C,N))>y
    f=Figure((-6.9,-3.4,3.3,3.4))
    f.circ((0,0),3); f.circ(o,r,RED,True)
    f.poly([B,C,M],BLUE,True,'#cbdfee',.36)
    f.poly([N,K,A],BLUE,True,'#cbdfee',.36)
    f.poly([A,B,C,D],close=True)
    for a,b in [(K,N),(B,M),(A,N),(C,L),(K,D)]: f.line(a,b,BLUE,True)
    for a,b in [(A,K),(K,N),(D,N)]: f.tick(a,b,1,RED)
    for a,b in [(B,L),(B,C),(C,M)]: f.tick(a,b,2,BLUE)
    for p,s,dx,dy in [(A,'A',-10,20),(B,'B',10,15),(C,'C',12,-5),(D,'D',-10,-10),(K,'K',-7,24),(L,'L',10,24),(M,'M',8,-12),(N,'N',-9,-12)]: f.point(p,s,dx,dy)
    f.save(5)


def sixth():
    A=(0,3); B=(-4,0); C=(3,0)
    ab=norm(sub(A,B)); ac=norm(sub(A,C))
    L=mul(add(mul(B,ac),mul(C,ab)),1/(ab+ac))
    T=mid(A,L); u=unit(sub(L,A)); axis=(-u[1],u[0])
    O,r=circle(A,B,C)
    P,Q=line_circle(T,add(T,axis),O,r)
    O2=sub(O,mul(u,2*dot(sub(O,T),u)))
    equal(norm(sub(L,O2)),r,'6: reflected circle')
    equal(abs(O2[1]),r,'6: tangency to BC')
    tangent=unit((-(A[1]-O[1]),A[0]-O[0]))
    X=add(A,mul(tangent,2.5))
    Y=sub(A,mul(tangent,2.5))
    f=Figure((-4.3,-4.1,3.5,3.9))
    f.circ(O,r); f.arc(O2,r,P,Q,via=L,color=BLUE)
    f.poly([A,B,C],close=True)
    f.line(A,L,RED,True); f.line(sub(T,mul(axis,4.1)),add(T,mul(axis,4.1)),GREY,True)
    f.line(X,Y,BLUE)
    for a,b in [(P,A),(P,L),(Q,A),(Q,L)]: f.line(a,b,GREY,True,width=1.1)
    f.right(A,T,add(T,axis))
    f.tick(A,T,1,RED); f.tick(T,L,1,RED)
    for p,s,dx,dy in [(A,'A',0,-14),(B,'B',-12,10),(C,'C',12,10),(L,'L',0,24),(P,'P',-14,-9),(Q,'Q',14,-9),(X,'X',-6,-10),(Y,'Y',8,-10)]: f.point(p,s,dx,dy)
    f.save(6)


def seventh():
    alpha=50*pi/180
    A=(0,0); B=(6,0); F=(-2,0)
    D=(2*cos(2*alpha),2*sin(2*alpha)); C=(2,4*sin(alpha)/cos(alpha)); E=(2,0)
    O,r=cyclic([A,B,C,D],'7: ABCD')
    equal(angle(D,A,B),2*angle(A,B,C),'7: angle condition')
    equal(norm(sub(A,D))+norm(sub(A,E)),norm(sub(B,E)),'7: target')
    f=Figure((-2.3,-2,6.6,5.2))
    f.circ(O,r); f.poly([F,B,C],close=True)
    f.line(A,D,RED); f.line(C,E,BLUE)
    f.tick(F,A,1,RED); f.tick(A,D,1,RED)
    f.tick(F,E,2,BLUE); f.tick(E,B,2,BLUE)
    f.angle(B,F,C,.65,'α'); f.angle(C,B,A,.65,'α'); f.angle(B,A,D,.57,'2α',RED)
    f.right(C,E,B)
    for p,s,dx,dy in [(F,'F',-10,20),(A,'A',-6,26),(E,'E',0,26),(B,'B',12,20),(C,'C',0,-12),(D,'D',-14,-4)]: f.point(p,s,dx,dy)
    f.save(7)


def eighth():
    A=(-.5,sqrt(3)/2); B=(-1,0); C=(1,0); K=(-2,0)
    M=mid(A,B); N=mid(A,C); O,r=circle(M,K,N)
    equal(dot(sub(A,K),A),0,'8: original tangent')
    equal(dot(sub(A,K),sub(K,O)),0,'8: new tangent')
    f=Figure((-2.7,-1.15,1.5,1.3))
    f.circ((0,0),1)
    f.arc(O,r,K,N,via=M,color=BLUE,extend=.22)
    f.poly([A,B,C],close=True); f.line(K,C)
    f.line(add(K,mul(sub(A,K),-.2)),add(A,mul(sub(A,K),.3)),RED)
    f.line(M,N,BLUE); f.line(K,M,BLUE,True); f.line(K,N,BLUE,True)
    f.tick(A,M); f.tick(M,B); f.tick(A,N,2); f.tick(N,C,2)
    for p,s,dx,dy in [(A,'A',0,-14),(B,'B',0,24),(C,'C',12,15),(K,'K',-12,12),(M,'M',-14,-5),(N,'N',12,-6)]: f.point(p,s,dx,dy)
    f.label((.05,1.18),'ℓ',15,3,RED)
    f.save(8)


def ninth():
    A=(0,0); B=(6,0); D=(4.5,4.5*sqrt(3)); C=add(B,D)
    K=add(B,(3,3*sqrt(3))); L=(3,0); M=mid(C,L)
    O,r=circle(A,L,M)
    u=unit(D); N=mul(u,2*dot(O,u)); X=add(B,mul(u,3))
    cyclic([A,L,M,N],'9: ALMN')
    assert norm(N)>norm(D)
    equal(angle(C,N,L),90,'9: target')
    equal(norm(sub(L,M)),norm(sub(M,N)),'9: equal chords')
    f=Figure((-4.1,-.5,10.9,10.9))
    f.circ(O,r)
    f.arc(M,norm(sub(M,L)),C,L,via=N,color=RED,dash=True)
    f.poly([A,B,C,D],close=True)
    f.line(D,N,GREY,True); f.line(A,K,BLUE); f.line(C,L,RED)
    f.line(L,X,BLUE,True); f.line(M,N,RED,True)
    f.right(C,N,L,14,RED)
    f.tick(C,K,1,BLUE); f.tick(K,X,1,BLUE)
    f.tick(C,M,2,RED); f.tick(M,L,2,RED); f.tick(M,N,2,RED)
    for p,s,dx,dy in [(A,'A',-8,24),(B,'B',10,22),(C,'C',14,-2),(D,'D',-14,-3),(K,'K',13,-5),(L,'L',0,26),(M,'M',-14,-6),(N,'N',8,-12),(X,'X',14,12)]: f.point(p,s,dx,dy)
    f.save(9)


def tenth():
    A=(0,6); B=(-2,0); C=(3,0)
    a=norm(sub(B,C)); b=norm(sub(A,C)); c=norm(sub(A,B)); per=a+b+c
    A=mul(A,1/per); B=mul(B,1/per); C=mul(C,1/per)
    a/=per; b/=per; c/=per; s=.5
    P=add(A,mul(unit(sub(B,A)),s)); Q=add(A,mul(unit(sub(C,A)),s))
    M=mid(A,B); N=mid(A,C); O,r=circle(A,P,Q)
    X,Y=line_circle(M,N,O,r)
    I=mul(add(add(mul(A,-a),mul(B,b)),mul(C,c)),1/(-a+b+c))
    T=project(I,B,C); re=norm(sub(I,T))
    equal(norm(sub(I,P)),re,'10: excircle P'); equal(norm(sub(I,Q)),re,'10: excircle Q')
    equal(norm(sub(X,Y)),.5,'10: XY')
    f=Figure((O[0]-r-.01,O[1]-r-.01,O[0]+r+.01,O[1]+r+.01))
    f.circ(O,r)
    f.arc(I,re,P,Q,via=T,color=BLUE)
    f.poly([A,B,C],close=True)
    f.line(B,P,GREY,True); f.line(C,Q,GREY,True)
    f.line(X,Y,RED,width=2.6)
    for p,s,dx,dy in [(A,'A',0,-13),(B,'B',-10,22),(C,'C',10,22),(P,'P',-10,22),(Q,'Q',10,22),(M,'M',-10,-12),(N,'N',10,-12),(X,'X',-10,-7),(Y,'Y',10,-7),(T,'T',0,23)]: f.point(p,s,dx,dy)
    for p,label in [(mid(X,M),'x'),(mid(M,N),'a'),(mid(N,Y),'y')]: f.label(p,label,dy=24,color=RED,size=25)
    f.label(add(T,(0,-.045)),'ω',15,0,BLUE)
    f.save(10)


if __name__ == '__main__':
    for draw in [first,second,third,fourth,fifth,sixth,seventh,eighth,ninth,tenth]:
        draw()
    print('Created 10 SVG figures; all construction checks passed.')
