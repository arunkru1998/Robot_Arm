import cv2
import numpy as np
from matplotlib import pyplot as plt

x = []
y = []

x_data = np.vstack((np.arange(0, 100), np.arange(0, 100))).T  # arbitrary values (for testing).
cnt = 10

fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
out = cv2.VideoWriter("ax.avi", fourcc, 30, (1000,200))

def figure_to_array(fig):
    fig.canvas.draw()
    return np.array(fig.canvas.renderer._renderer)

while len(x_data)>60+cnt:
    x = [i for i in range(cnt,cnt+60)]
    y = x_data[cnt:cnt+60,0]
    cnt+=1
    f = plt.figure(figsize=(5,1))
    #plt.ylim(0,1)
    plt.plot(x,y)
    #plt.show(block=True) # Show plot for testing
    plt.close()    
    f_arr = figure_to_array(f)
    f_arr = cv2.resize(f_arr,(1000,200))
    #cv2.imshow('f_arr', f_arr) # Show f_arr for testing
    #cv2.waitKey(10)
    bgr = cv2.cvtColor(f_arr, cv2.COLOR_RGBA2BGR)
    out.write(bgr)

out.release()
#cv2.destroyAllWindows()
