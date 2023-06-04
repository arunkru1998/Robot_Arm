import numpy as np
import matplotlib.pyplot as plt
import cv2



###Begining of code

#initialisation
#initial angles
theta1 = 2.865
theta2 = 2.865
theta3 = 2.865
ang=[theta1,theta2,theta3]
rad=np.deg2rad(ang)
n=3
# n - number of the links


#initial angvel
theta_1_dot=0.1
theta_2_dot=0
theta_3_dot=0
angvel=[theta_1_dot,theta_2_dot,theta_3_dot]
ref=angvel
# Joint lengths
L1 = 1
L2 = 1
L3 = 1
L=[L1,L2,L3]

# robot arm half-width
l1=0.2
l2=0.2
l3=0.2
l=[l1,l2,l3]

#position of the obstacle
x_ob=1.0
y_ob=1.8



#CBF constants

k=[0.1,0.1,0.1]
c=[0.01,0.01,0.01]



end_time=30
dt=0.1
steps=int(end_time/dt)
joint_pos=[]
obs_perpen_pose=[]
trackerref=[ref]
trackeru=[[0,0,0]]
trackervel=[np.asarray(ref)+np.asarray(trackeru[0])]
distance=[]

frame=(500,500)

fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
out = cv2.VideoWriter("video.avi", fourcc, 30, frame) 

# Functions
# Update angle position and angular velocity
def update_angle(angvel,rad,dt):
  newrad=[]
  for i in range(len(angvel)):
    s=angvel[i]*dt+rad[i]
    newrad.append(s)
  return newrad

def update_vel(ref,u):
  newvel=[]
  for i in range(len(angvel)):
    s=ref[i]+u[i]
    newvel.append(s)
  return newvel

# To calculate the position of joint points(xp), points perpendicular to the offset(dp) and obstacle-xp
def update_pos(rad,L,x_ob,y_ob):

# Calculate the coordinates of each joint
    x1 = 0.0
    y1 = 0.0

    x2 = L[1]* np.cos(rad[:1])
    y2 = L[1]* np.sin(rad[:1])

    x3 = x2 + L[2] * np.cos(sum(rad[:2]))
    y3 = y2 + L[2] * np.sin(sum(rad[:2]))

    xp=[x1,x2,x3]
    yp=[y1,y2,y3]

    Xp=[x_ob-x1,x_ob-x2,x_ob-x3]
    Yp=[y_ob-y1,y_ob-y2,y_ob-y3]

    L_C=(x_ob*np.ones(3)-xp[:3])*np.cos([rad[0],sum(rad[:2]),sum(rad[:3])])+(y_ob*np.ones(3)-yp[:3])*np.sin([rad[0],sum(rad[:2]),sum(rad[:3])])

    L_D=np.ones(3)
    for i in range(3):
        if(L_C[i]<0):
            L_D[i]=0
        elif (L_C[i]<L[i]):
            L_D[i]=L_C[i]
        else:
            L_D[i]=L[i]

    X_D_1=[L_D[0]*np.cos(rad[0]),L_D[0]*np.sin(rad[0])]
    X_D_2=[xp[1]+L_D[1]*np.cos(sum(rad[:2])),yp[1]+L_D[1]*np.sin(sum(rad[:2]))]
    X_D_3=[xp[2]+L_D[2]*np.cos(sum(rad[:3])),yp[2]+L_D[2]*np.sin(sum(rad[:3]))]

    dp=[X_D_1,X_D_2,X_D_3]

    return(xp,yp,Xp,Yp,dp,L_D)

def update_dynamics_case_1(rad,L,angvel,n):
    #n is the joint number (first-index = 1)

    #For When L_Dn=0


    #If n==1 (base link)
    if n==1:
      f=np.array([0,0,0])
      g=np.array([0,0,1])

    #If n>=2 (all other joints)
    else:
      s0=0
      s1=0
      s2=0
      #j,angvel,rad,L are first-index = 0 hence the difference
      #sum(vec[:x+1]) gives the sum of the first x elements in the list
      # j in range(n-1) gives j=0 --- j=n-2
      for j in range(n-1):
        x=-L[j]*sum(angvel[:j+1])*np.sin(sum(rad[:j+1])) 
        """- added"""
        s0+=x
      for j in range(n-1):
        x=L[j]*sum(angvel[:j+1])*np.cos(sum(rad[:j+1]))
        s1+=x
      s2=sum(angvel[:n-1])
      
      f=np.array([s0,s1,s2])
      g=np.array([0,0,1])
    return(f,g)

def update_dynamics_case_2(rad,L,angvel,Xp,Yp,n):
    #n is the joint number (first-index = 1)

    #For When 0 < L_Dn < Ln
   
    x_1,x_2,x_3=Xp
    y_1,y_2,y_3=Yp

    #Xp,Yp are vectors of the distance of each link basepoint to the obstacle point

    def alpha1_n(n):
        def part1a(n):
            f=-(np.sin(sum(rad[:n]))**2)
            s=0
            for j in range(int(n)-1):
                x=L[j]*sum(angvel[:j+1])*np.sin(sum(rad[:j+1]))
                s+=x
            return(f*s)

        def part2a(n):
            f=-0.5*(np.sin(2*sum(rad[:n])))
            s=0
            for j in range(int(n-1)):
                x=L[j]*sum(angvel[:j+1])*np.cos(sum(rad[:j+1]))
                s+=x
            return(f*s)

        def part3a(n):
            f=sum(angvel[:n-1])
            s=Yp[n-1]*np.cos(2*sum(rad[:n]))-Xp[n-1]*np.sin(2*sum(rad[:n]))
            return(f*s)
        a=part1a(n)+part2a(n)+part3a(n)
        return(a)
   
    def beta1_n(n):
        def part1b(n):
            f=(np.cos(sum(rad[:n]))**2)
            s=0
            for j in range(int(n)-1):
                x=L[j]*sum(angvel[:j+1])*np.cos(sum(rad[:j+1]))
                s+=x
            return(f*s)

        def part2b(n):
            f= 0.5*(np.sin(2*sum(rad[:n])))
            s=0
            for j in range(int(n-1)):
                x=L[j]*sum(angvel[:j+1])*np.sin(sum(rad[:j+1]))
                s+=x
            return(f*s)

        def part3b(n):
            #Xp[n-1]=x_ob-xp[n-1], Yp[n-1]=y_ob-yp[n-1]
            f=sum(angvel[:n-1])
            s=Xp[n-1]*np.cos(2*sum(rad[:n]))+Yp[n-1]*np.sin(2*sum(rad[:n]))
            return(f*s)
        return(part1b(n)+part2b(n)+part3b(n))

    if n==1:
      #If n==1 (base link)
      f=np.array([0,0,0])
      g=np.array([Yp[n-1]*np.cos(2*rad[0])-Xp[n-1]*np.sin(2*rad[0]),Xp[n-1]*np.cos(2*rad[0])+Yp[n-1]*np.sin(2*rad[0]),1])

    else:
      #If n>=2 (all other links)
      f=np.array([alpha1_n(n),beta1_n(n),sum(angvel[:n-1])])
      g=np.array([Yp[n-1]*np.cos(2*(sum(rad[:n])))-Xp[n-1]*np.sin(2*(sum(rad[:n]))),Xp[n-1]*np.cos(2*(sum(rad[:n])))+Yp[n-1]*np.sin(2*(sum(rad[:n]))),1])

    return(f,g)

def update_dynamics_case_3(rad,L,angvel,Xp,Yp,n):

    def alpha2_n(n):
        def part1a(n):
            s=0
            for j in range(n-1):
                x=L[j]*sum(angvel[:j+1])*np.sin(sum(rad[:j+1]))
                s+=x
            return(-1*s)

        def part2a(n):
            f=sum(angvel[:n-1])*L[n-1]*np.sin(sum(rad[:n]))
            return(-1*f)


        return(part1a(n)+part2a(n))

 
    def beta2_n(n):
        def part1b(n):
            s=0
            for j in range(n-1):
                x=L[j]*sum(angvel[:j+1])*np.cos(sum(rad[:j+1]))
                s+=x
            return(s)

        def part2b(n):
            f=sum(angvel[:n-1])*L[n-1]*np.cos(sum(rad[:n]))
            return(f)


        return(part1b(n)+part2b(n))
    
    if n==1:
      #If n==1 (base link)
      f=np.array([0,0,0])
      g=np.array([-L[0]*np.sin(rad[0]),L[0]*np.cos(rad[0]),1])

    else:
      #If n>=2 (all other links)
      f=np.array([alpha2_n(n),beta2_n(n),sum(angvel[:n-1])])
      g=np.array([-L[n-1]*np.sin(sum(rad[:n])),L[n-1]*np.cos(sum(rad[:n])),1])

    return(f,g)

#Finding gradient of the barrier function 
def control_assist(rad,angvel,l,x_ob,y_ob,dp,f,g,k,c,n):

# dp is the x and y position of point of interest on the link 
    X_D_n=dp[n-1]
    B_n=(1/((x_ob-X_D_n[0])**2+(y_ob-X_D_n[1])**2+(l[n-1])**2))+X_D_n[0]**2+X_D_n[1]**2+rad[n-1]**2


    grad_B_n=[((2*(x_ob-X_D_n[0]))/((x_ob-X_D_n[0])**2+(y_ob-X_D_n[1])**2+l[n-1]**2)**2)+(2*X_D_n[0]),
    ((2*(y_ob-X_D_n[1]))/((x_ob-X_D_n[0])**2+(y_ob-X_D_n[1])**2+l[n-1]**2)**2)+(2*X_D_n[1]),
    2*rad[n-1]]


    #Finding the control assist inputs J and I 

    I_n=np.array(grad_B_n)@np.array(f)+(np.array(grad_B_n)@np.array(g))*angvel[n-1]

    J_n=k*B_n+c


    if (I_n-J_n>0):
        u_n=-((I_n-J_n)/np.linalg.norm(np.array(grad_B_n)@g))*(np.array(grad_B_n)@g)
    else:
        u_n=0

    u_n=float(u_n)

    return(u_n)

def figure_to_array(fig):
    fig.canvas.draw()
    return np.array(fig.canvas.renderer._renderer)

def plot(xp,yp,dp,n,rad,L):
# Plot the robotic arm
    fig, ax = plt.subplots(figsize=(frame[0]/100, frame[1]/100))
    c=['red','green','blue']
    x4 = xp[n-1] + L[n-1] * np.cos(sum(rad))
    y4 = yp[n-1] + L[n-1] * np.sin(sum(rad))
    xp.append(x4)
    yp.append(y4)
    plt.scatter(x_ob,y_ob)
    for i in range(n):
        plt.plot([xp[i], xp[i+1]], [yp[i], yp[i+1]], color=c[i], linewidth=2)
        plt.scatter(dp[i][0],dp[i][1], color=c[i])

    # Set axis limits and aspect ratio
    plt.xlim([-5.0, 5.0])
    plt.ylim([-5.0, 5.0])
    plt.gca().set_aspect('equal', adjustable='box')
    f_arr = figure_to_array(fig)
    f_arr = cv2.resize(f_arr,frame)
    bgr = cv2.cvtColor(f_arr, cv2.COLOR_RGBA2BGR)
    out.write(bgr)    
    # Show the plot



fig, ax = plt.subplots()
for i in range(steps):
    xp,yp,Xp,Yp,dp,L_D=update_pos(rad,L,x_ob,y_ob)
    dsquare=[]
    for i in range(len(xp)):
        x=x_ob-dp[i][0]
        y=y_ob-dp[i][1]
        d=x**2+y**2
        dsquare.append(np.sqrt(d))
    distance.append(dsquare)
    # xp,yp - base joint position for each link
    # Xp,Yp - Xob-Xn 
    # dp -Xd,Yd
    f=[]
    g=[]
    u=[]
    for j in range(n):
        if (L_D[j]==0):
            f_,g_=update_dynamics_case_1(rad,L,angvel,j+1)
        elif (L_D[j]==L[j]):
            f_,g_=update_dynamics_case_3(rad,L,angvel,Xp,Yp,j+1)
        else:
            f_,g_=update_dynamics_case_2(rad,L,angvel,Xp,Yp,j+1)
        f.append(f_)
        g.append(g_)

    print([l1,l2,l3],[k[0],k[1],k[2]])
    f=np.asarray(f)
    g=np.asarray(g)

    for w in range(n):
        u_=control_assist(rad,angvel,l,x_ob,y_ob,dp,f[w],g[w],k[w],c[w],w+1)
        u.append(u_)
    trackeru.append(u)
    trackerref.append(ref)
    trackervel.append(np.asarray(ref)+np.asarray(u))
    u=np.asarray(u)
    # Generate the new plot
    plot(xp, yp, dp, n, rad, L)  # Call your plot function here
    rad=update_angle(angvel,rad,dt)
    angvel=update_vel(ref,u)

out.release()

distance=np.asarray(distance)
trackervel=np.asarray(trackervel)
trackeru=np.asarray(trackeru)
trackerref=np.asarray(trackerref)
t=np.linspace(0,10,201)

plt.figure()
plt.plot(t,trackerref[:,0],t,trackeru[:,0],t,trackervel[:,0])
plt.legend(['Constant input','Control Assist','Total input'])
plt.title("Link 1")

plt.figure()
plt.plot(t,trackerref[:,1],t,trackeru[:,1],t,trackervel[:,1])
plt.legend(['Constant input','Control Assist','Total input'])
plt.title("Link 2")

plt.figure()
plt.plot(t,trackerref[:,2])
plt.plot(t,trackeru[:,2])
plt.plot(t,trackervel[:,2])
plt.legend(['Constant input','Control Assist','Total input'])
plt.title("Link 3")


plt.figure()
plt.plot(t[:-1],distance[:,0],t[:-1],distance[:,1],t[:-1],distance[:,2])
plt.plot([t[0] ,t[-1]],[l[0],l[2]],linestyle='dashed')
plt.legend(['D1',"D2","D3"])
plt.title("Distance Between Dn and Barrier point")



































