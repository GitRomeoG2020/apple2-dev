#!/bin/sh
# inline a2enc.js into template.html -> a2sprite.html
cd "$(dirname "$0")" && python3 -c "
t=open('template.html').read();e=open('a2enc.js').read()
open('a2sprite.html','w').write(t.replace('/*A2ENC*/',e))"
