"""Re-run the keyframe gate on given shots without redrawing: python3 sec1/gate_one.py s31 s38"""
import sys, json
ids=sys.argv[1:]; sys.argv=['keys.py','__none__']
src=open('sec1/keys.py').read().split("todo = [s for s in data")[0]
exec(src)
for i in ids: print(i, json.dumps(gate(SH[i]), ensure_ascii=False))
