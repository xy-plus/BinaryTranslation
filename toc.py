import os

os.makedirs("docs/src",exist_ok=True)
res = os.popen("cat ./README.md | ./gh-md-toc -")
toc = res.read().strip()
fin = open("README.md")
fout = open("docs/README.md","w")
fout.write(fin.read().replace("[TOC]", toc).replace("(./", "(../"))
fin.close()
fout.close()
os.system("cp ./src/*.md ./docs/src/")
