"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.9
 *                @date:   03.06.2019
 ******************************************************************************/
/**         RenderWindow.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 context and display some 2D animation.
 ****
"""

import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
import math

import numpy as np
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_NORMAL_ARRAY, GL_MODELVIEW


from OpenGL.raw.GLUT import glutSolidTeapot


WIDTH =640
HEIGHT =480
actOri = np.identity(4)
angle = 0
axis = np.array([1,0,0])
doRotation = False
startP = np.array([1, 0, 0])
doTranslation = False
lightsOn = True;
trans = np.array([0,0,0])
scrollScale = 1
x=0
y =0
orthogonal = False
perspective = True
doshadow = True;
lightPoint = np.array([10000.,20000.,10000.,9.0])
p= np.array([[1.0,0,0,0],[0,1.0,0,0],[0,0,1.0,0],[0,-1.0/lightPoint[1],0,0]]).transpose()
modelColor = [0.9, 0.9, 0.9]
shadowColor = [0.0, 0.0, 0.0]
IMAGEPATH = "elephant.obj"
BACKGROUNDCOLOR = [0, 0.5, 1.0, 1.0]
def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
        return v
    return v / norm  

class Scene3D:
    
    def __init__(self, width, height,filename):
        
        self.width = width
        self.height = height
        self.readAndCalc(filename)
        
    def readAndCalc(self,filename):

        calcnorm = False
        myDic = {"v":[],"vn":[],"vt":[],"f":[]}
        
        for line in open((filename)):
            if not line is None:
                line = line.strip()
                if not len(line) == 0:
                    if not line.split()[0] == "f" and not line.split()[0] == "s" and not line.split()[0] == "usemtl":#kp was s in der liste is 
                        myDic[line.split()[0]].append(list(map(float,line.split()[1:])))
                    elif not line.split()[0] == "s" and not line.split()[0] == "usemtl":
                        myDic[line.split()[0]].append(line.split()[1:])
                        if not "//" in myDic["f"][-1][0]:
                            calcnorm =True
    
        boundingbox = [map(min,zip(*myDic["v"])),map(max,zip(*myDic["v"]))]
        self.center = [(s[0]+s[1])/2.0 for s in zip(*boundingbox)]
        print(boundingbox[0],boundingbox[1])
        self.scale = 1 / np.linalg.norm(np.array(self.center)-np.array(boundingbox[0]))
        print(self.scale)
        
        self.miny = boundingbox[0][1]
        print(self.miny)
        
        self.data = []
        if calcnorm:
            myDic["vn"] = [np.array([0,0,0]) for i in myDic["v"]]
            
            for face in myDic["f"]:
                point_a = np.array(myDic["v"][int(face[0])-1])
                point_b = np.array(myDic["v"][int(face[1])-1])
                point_c = np.array(myDic["v"][int(face[2])-1])
                
                vec_a_b = point_a-point_b
                vec_a_c = point_a-point_c
                
                normvec = np.cross(vec_a_b,vec_a_c)
                
                myDic["vn"][int(face[0])-1] = np.add(myDic["vn"][int(face[0])-1],normvec)
                myDic["vn"][int(face[1])-1] = np.add(myDic["vn"][int(face[1])-1],normvec)
                myDic["vn"][int(face[2])-1] = np.add(myDic["vn"][int(face[2])-1],normvec)
            
            #myDic["vn"] =list( map(float,myDic["vn"]))
            for face in myDic["f"]:
                for vertexBlock in face:
                    vertex = myDic["v"][int(vertexBlock)-1]
                    vertexnorm = list(myDic["vn"][int(vertexBlock)-1])
                    
                    self.data.append(vertex+vertexnorm)
        else:
            for face in myDic["f"]:
                for vertexBlock in face:
                    vertex = myDic["v"][int(vertexBlock.split("//")[0])-1]
                    vertexnorm = myDic["vn"][int(vertexBlock.split("//")[1])-1]
                    
                    self.data.append(vertex+vertexnorm)
        self.myVBO = vbo.VBO(np.array(self.data,'f'))
        
 
    def rotate(self,angle, axis):
        c, mc = np.cos(angle), 1-np.cos(angle)
        s = np.sin(angle)
        l = np.sqrt(np.dot(np.array(axis), np.array(axis))) 
        if l == 0:
            return np.identity(4)
        x, y, z = np.array(axis)/l
        r = np.array([[x*x*mc+c,x*y*mc-z*s, x*z*mc+y*s,0],[x*y*mc+z*s,y*y*mc+c,y*z*mc-x*s,0],[x*z*mc-y*s,y*z*mc+x*s,z*z*mc+c,0],[0,0,0,1]])
     
        return r.transpose() 
    
    
    def render(self):
        global actOri,angle,axis,trans,modelColor,lightPoint,p,shadowColor,doshadow,scrollScale
        self.myVBO.bind()
        glColor3fv(modelColor)
        glLoadIdentity()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glVertexPointer(3,GL_FLOAT,24,self.myVBO)
        glNormalPointer(GL_FLOAT,24,self.myVBO+12)
        
        glTranslate(-trans[0],-trans[1],0)
        glScale(scrollScale,scrollScale,scrollScale)
        glMultMatrixf(np.dot(actOri,self.rotate(angle, axis)))
        
        glScale(self.scale,self.scale,self.scale)
        glTranslate(-self.center[0],-self.center[1],-self.center[2])
        #glDrawArrays(GL_TRIANGLES,0,3*len(self.data))
        
        if doshadow:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            
            glMatrixMode(GL_MODELVIEW)
            
            glPushMatrix()
            glTranslate(0,self.miny,0)
            glTranslatef(lightPoint[0],lightPoint[1],lightPoint[2])
            glMultMatrixf(p)
            glTranslatef(-lightPoint[0],-lightPoint[1],-lightPoint[2])
            glTranslate(0,-self.miny,0)
            glColor3fv(shadowColor)
            glDrawArrays(GL_TRIANGLES,0, 3*len(self.data))
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            
            glPopMatrix()
        glColor3fv(modelColor)
        glDrawArrays(GL_TRIANGLES,0,3*len(self.data))
            
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.myVBO.unbind()
    
      

class RenderWindow:
    """GLFW Rendering window class"""
    def __init__(self):
        global WIDTH,HEIGHT,IMAGEPATH,lightPoint,BACKGROUNDCOLOR
        # save current working directory
        
        # save current working directory
        cwd = os.getcwd()
        
        # Initialize the library
        if not glfw.init():
            return
        
        # restore cwd
        os.chdir(cwd)
        
        # version hints
        #glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, 3)
        #glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, 3)
        #glfw.WindowHint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        #glfw.WindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # define desired frame rate
        self.frame_rate = 100

        # make a window
        self.width, self.height = 640, 480
        self.aspect = self.width/float(self.height)
        self.window = glfw.create_window(self.width, self.height, "2D Graphics", None, None)
        if not self.window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)
    
        # initialize GL
        glViewport(0, 0, self.width, self.height)
        glLightfv(GL_LIGHT0, GL_POSITION, lightPoint)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        
        glClearColor(*BACKGROUNDCOLOR)
        glMatrixMode(GL_PROJECTION)
        #glOrtho(-self.width/(self.width/2),self.width/(self.width/2),-self.height/(self.height/2),self.height/(self.height/2),-2,2)
        glOrtho(-1.5,1.5,-1.5*self.height/self.width,1.5*self.height/self.width,-1.,1.)
        
        glMatrixMode(GL_MODELVIEW)
        glClear(GL_COLOR_BUFFER_BIT) #clear screen
        
       
        #set window callbacks
        glfw.set_cursor_pos_callback(self.window, self.mousemoved)
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_scroll_callback(self.window, self.onMousescroll)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)


        # create 3D
        self.scene = Scene3D(self.width, self.height,IMAGEPATH)
       
        
        # exit flag
        self.exitNow = False



    
    def projectOnSphere(self,x, y, r):
        x, y = x-self.width/2.0, self.height/2.0-y 
        a = min(r*r, x**2 + y**2)
        z = math.sqrt(r*r - a)
        l = math.sqrt(x**2 + y**2 + z**2)
       
        return np.array([x/l, y/l, z/l])
    

    
    def onMousescroll(self,window,xoffset,yoffset):
        global scrollScale
        scrollScale = scrollScale+yoffset
       
        if scrollScale < 0:
            scrollScale = 0
        return None;
    
    def mousemoved(self, win, xpos , ypos ):
        global angle , axis , scaleFactor, doRotation,x,y,startP,doTranslation,trans
        x = xpos
        y = ypos
        if doRotation :
            r = min(self.width, self.height)/2.0
            moveP = self.projectOnSphere(x, y, r) 
            angle = np.arccos(np.dot(startP , moveP)) 
            axis = np.cross(startP , moveP) 
        if doTranslation:
            self.translate()
        
    def onMouseButton(self, win, button, action, mods):
        global startP , actOri , angle , doRotation, axis , x , y ,doTranslation,trans
        
        r = min(self.width, self.height)/2.0
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                doRotation = True
                startP = self.projectOnSphere(x, y, r)
            elif action == glfw.RELEASE:
                doRotation = False
                actOri = np.dot(actOri,self.scene.rotate(angle,axis))
                angle = 0
        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                doTranslation = True
                self.translate()
            elif action == glfw.RELEASE:
                doTranslation = False
                self.translate()
              
    def translate(self):
        global trans,x,y
        x1 = x/(self.width/3)-1.5
        y1 = y/(self.height/3)-1.5
        trans = np.array([x1*-1,y1,0])
        
    

    def onKeyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        
        global lightsOn,orthogonal, perspective,modelColor,doshadow
        
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_S:
                if mods == glfw.MOD_SHIFT:
                    modelColor = [0.0,0.0,0.0]
                else:
                    glClearColor(0.0, 0.0, 0.0, 0.0)
            if key == glfw.KEY_W:
                if mods == glfw.MOD_SHIFT:
                    modelColor = [1.0,1.0,1.0]
                else:
                    glClearColor(1.0, 1.0, 1.0, 1.0)
            if key == glfw.KEY_R:
                if mods == glfw.MOD_SHIFT:
                    modelColor = [1.0,0.0,0.0]
                else:
                    glClearColor(1.0, 0.0, 0.0, 0.0)
            if key == glfw.KEY_B:
                if mods == glfw.MOD_SHIFT:
                    modelColor = [0.0,0.0,1.0]
                else:
                    glClearColor(0.0, 0.0, 1.0, 0.0) 
            if key == glfw.KEY_G:
                if mods == glfw.MOD_SHIFT:
                    modelColor = [1.0,1.0,0.0]
                else:
                    glClearColor(1.0, 1.0,0.0, 0.0)      
            if key == glfw.KEY_P:
                orthogonal = False
                perspective = True
                self.onSize(self.window, self.width, self.height)
            if key == glfw.KEY_D:
                if doshadow:
                    doshadow = False
                else:
                    doshadow = True
                    
            if key == glfw.KEY_L:
                if lightsOn:
                    lightsOn = False
                    glDisable(GL_LIGHTING)
                else :
                    lightsOn = True
                    glEnable(GL_LIGHTING)
            
            if key ==  glfw.KEY_O:
                orthogonal = True
                perspective = False
                self.onSize(self.window, self.width, self.height)
       

    def onSize(self, win, width, height):
        global orthogonal, perspective

        print("onsize: ", win, width, height)
        self.width = width
        self.height = height
        
        glViewport(0, 0, width, height)
    
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = float(width) /float( height)
        self.aspect = aspect_ratio
        if orthogonal:
            if width<= height:
                glOrtho(-1.5,1.5,-1.5*height/width,1.5*height/width,-10,20)
            else:
                glOrtho(-1.5*width/height,1.5*width/height,-1.5,1.5,-10,20)
        if perspective:
                if width<= height:
                    gluPerspective(45.0*float(height)/float(width),aspect_ratio,0.5,20.0)
                else:
                    gluPerspective(45.0,aspect_ratio,0.5,20.0)
                gluLookAt(0,0,4,0,0,0,0,1,0)
   
        glMatrixMode(GL_MODELVIEW)
        #glfw.swap_buffers(self.window)
        


    def run(self):
        # initializer timer
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            currT = glfw.get_time()
            if currT - t > 1.0/self.frame_rate:
                # update time
                t = currT
                # clear
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                # render scene
                self.scene.render()
                
                glfw.swap_buffers(self.window)
                
                # Poll for and process events
                glfw.poll_events()
        # end
        glfw.terminate()


  
# main() function

def main():

    print("Simple glfw render Window") 
    rw = RenderWindow()
    rw.run()
    

# call main
if __name__ == '__main__':
    main()