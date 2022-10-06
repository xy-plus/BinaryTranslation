import os

res = os.popen("cat ./README.md | ./gh-md-toc -")
toc = res.read().strip()
fin = open("README.md")
fout = open("docs/README.md","w")
fout.write(fin.read().replace("[TOC]", toc))
fin.close()
fout.close()
