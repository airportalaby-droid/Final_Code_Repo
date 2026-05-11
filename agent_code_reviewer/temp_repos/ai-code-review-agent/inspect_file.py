with open('src/detectors.py','rb') as f:
    b = f.read()
print(repr(b[:800]))
print('\n---LINES---\n')
with open('src/detectors.py','r',encoding='utf-8',errors='backslashreplace') as f:
    for i,l in enumerate(f,1):
        if i<=60:
            print(i, repr(l))
        else:
            break
