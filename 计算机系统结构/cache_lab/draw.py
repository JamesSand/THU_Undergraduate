import matplotlib.pyplot as plt
import numpy as np
# plt.xscale('log')

x = []
y = []
with open('log.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        line_split = line.split(" ")
        x.append(int(line_split[4]))
        y.append(float(line_split[-2]))

print(x)
print(y)

plt.xlabel('log of test step(B)')
plt.ylabel('time(ms)')
plt.xticks(np.log2(x), x)
plt.plot(np.log2(x), y)

# plt.show()

plt.savefig('./img/line.png')


