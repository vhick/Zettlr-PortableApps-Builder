#!/usr/bin/env python3
"""Original generic portable-package icon; no Zettlr logo or trademark use."""
from PIL import Image,ImageDraw
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'assets';root.mkdir(parents=True,exist_ok=True)
im=Image.new('RGBA',(256,256),(0,0,0,0));d=ImageDraw.Draw(im)
d.rounded_rectangle((18,18,238,238),radius=48,fill='#24354d')
d.rounded_rectangle((64,46,192,210),radius=15,fill='#f5f6fb')
d.line([(86,100),(167,100)],fill='#74829a',width=11)
d.line([(86,133),(167,133)],fill='#74829a',width=11)
d.line([(86,166),(145,166)],fill='#74829a',width=11)
im.save(root/'portable.ico',format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
for sz in (16,32):im.resize((sz,sz),Image.Resampling.LANCZOS).save(root/f'portable_{sz}.png')
print('Original non-trademark launcher icon created.')
