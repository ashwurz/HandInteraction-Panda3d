from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, KeyboardButton, CollisionHandlerQueue, CollisionBox, Point3, \
    CollisionNode, CollisionCapsule
from panda3d.core import BitMask32
from panda3d.core import TextNode, NodePath, LightAttrib
from panda3d.core import LVector3
from direct.actor.Actor import Actor
from direct.task.Task import Task
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CollisionTraverser, CollisionHandlerPusher
import gltf
import sys

x_button = KeyboardButton.ascii_key('q')
y_button = KeyboardButton.ascii_key('w')
z_button = KeyboardButton.ascii_key('e')


def clamp(i, mn=-1, mx=1):
    return min(max(i, mn), mx)


def genLabelText(text, i, self):
    return OnscreenText(text=text, parent=self.a2dTopLeft, scale=.06,
                        pos=(0.06, -.08 * i), fg=(1, 1, 1, 1),
                        shadow=(0, 0, 0, .5), align=TextNode.ALeft)


class TccSample(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        gltf.patch_loader(self.loader)
        self.disable_mouse()

        self.cTrav = CollisionTraverser()

        self.cHandler = CollisionHandlerQueue()

        pusher = CollisionHandlerPusher()

        self.generateText()

        self.defineKeys()

        self.title = OnscreenText(text="Simulação do TCC",
                                  fg=(1, 1, 1, 1), parent=self.a2dBottomRight,
                                  align=TextNode.ARight, pos=(-0.1, 0.1),
                                  shadow=(0, 0, 0, .5), scale=.08)

        self.hand = Actor("models/Simple_Hand_AfterApply.gltf")
        #self.hand = Actor("models/Simple_Handv3.gltf")
        self.hand.reparentTo(self.render)
        #self.hand.hide()
        self.hand.setPos(0, 5, 0)

        self.loadHandJoints()

        self.allfingers = {
            'T2': self.t2Thumb,
            'T1': self.t1Thumb,
            'T0': self.t0Thumb,
            'I2': self.i2IndexFinger,
            'I1': self.i1IndexFinger,
            'I0': self.i0IndexFinger,
            'M2': self.m2MiddleFinger,
            'M1': self.m1MiddleFinger,
            'M0': self.m0MiddleFinger,
            'R2': self.r2RingFinger,
            'R1': self.r1RingFinger,
            'R0': self.r0RingFinger,
            'L2': self.l2LittleFinger,
            'L1': self.l1LittleFinger,
            'L0': self.l0LittleFinger
        }

        self.define_fingers_collision()

        self.ball = self.loader.loadModel("models/ball")

        self.ball.reparentTo(self.render)

        self.ball.setScale(0.25, 0.25, 0.25)

        self.ball.setPos(1, 5, 0)

        self.ballRoot = self.ball.getPos()

        self.ballSphere = self.ball.find("**/ball")
        self.ballSphere.node().setFromCollideMask(BitMask32.bit(1))
        self.ballSphere.node().setIntoCollideMask(BitMask32.allOff())
        self.ballSphere.show()

        # self.cTrav.addCollider(self.ballSphere, self.cHandler)
        self.cTrav.addCollider(self.ballSphere, pusher)

        pusher.addCollider(self.ballSphere, self.ball, self.drive.node())

        self.taskMgr.add(self.setHandPostion, "HandTracking")
        # self.taskMgr.add(self.mainTask, "MainTask")
        self.cTrav.showCollisions(self.render)

    def mainTask(self, task):
        self.cTrav.traverse(self.render)
        for i in range(self.cHandler.getNumEntries()):
            entry = self.cHandler.getEntry(i)
            name = entry.getIntoNode().getName()
            if name == "Hand":
                self.handInteraction(entry)

        return Task.cont

    def handInteraction(self, colEntry):
        print(colEntry)  # -> To see the collision entry
        colPoint = colEntry.getSurfacePoint(self.render)
        self.ball.setX(colPoint.getX() + .1)
        self.ball.setZ(colPoint.getZ() + .1)

    def loadHandJoints(self):
        # Joints do dedo mindinho
        self.l2LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L2')
        self.l1LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L1')
        self.l0LittleFinger = self.hand.controlJoint(None, 'modelRoot', 'L0')

        # Joints do dedo anelar
        self.r2RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R2')
        self.r1RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R1')
        self.r0RingFinger = self.hand.controlJoint(None, 'modelRoot', 'R0')

        # Joints do dedo do meio
        self.m2MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M2')
        self.m1MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M1')
        self.m0MiddleFinger = self.hand.controlJoint(None, 'modelRoot', 'M0')

        # Joints do dedo indicador
        self.i2IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I2')
        self.i1IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I1')
        self.i0IndexFinger = self.hand.controlJoint(None, 'modelRoot', 'I0')

        # Joints do dedão da mão
        self.t2Thumb = self.hand.controlJoint(None, 'modelRoot', 'T2')
        self.t1Thumb = self.hand.controlJoint(None, 'modelRoot', 'T1')
        self.t0Thumb = self.hand.controlJoint(None, 'modelRoot', 'T0')

    def define_capsule_collision(self, finger):
        connected_finger = finger
        nconnected_finger = int(finger[1]) - 1
        if nconnected_finger >= 0:
            connected_finger = finger[0] + str(nconnected_finger)

        cNode = CollisionNode("Collision" + finger)
        cNode.addSolid(CollisionCapsule((self.allfingers[finger].getY() - self.allfingers[connected_finger].getY())*0.25,
                             (self.allfingers[finger].getX() - self.allfingers[connected_finger].getX())*0.25,
                             (self.allfingers[finger].getZ() - self.allfingers[connected_finger].getZ())*0.25,
                             0, 0, 0, 0.02))
        c_armature = self.allfingers[finger].attachNewNode(cNode)
        c_armature.reparentTo(self.hand.exposeJoint(None, 'modelRoot', finger))
        #c_armature.setColor(0, 0, 1, 1)
        c_armature.show()

    def define_fingers_collision(self):
        # finger radius 0.02
        for finger in self.allfingers:
            self.define_capsule_collision(finger)

    def defineKeys(self):
        self.accept('escape', sys.exit)
        self.accept('1', self.changePerspective, [-60, -60])
        self.accept('2', self.changePerspective, [-60, 60])
        self.accept('3', self.moveFingers)
        self.accept('4', self.resetPerspective)
        self.accept('5', self.resetFinger)
        self.accept('6', self.setHandDepth, [0.1])
        self.accept('7', self.setHandDepth, [-0.1])
        self.accept('8', self.resetHandPosition)

    def generateText(self):
        self.onekeyText = genLabelText("ESC: Sair", 1, self)
        self.onekeyText = genLabelText("[1]: Muda a Perpectiva da câmera para o primeiro modo", 2, self)
        self.onekeyText = genLabelText("[2]: Muda a Perspectiva da câmera para o segundo modo", 3, self)
        self.onekeyText = genLabelText("[3]: Mexe os dedos", 4, self)
        self.onekeyText = genLabelText("[4]: Volta a perspectiva da mão para o formato original", 5, self)
        self.onekeyText = genLabelText("[5]: Volta os dedos para a posição inicial", 6, self)
        self.onekeyText = genLabelText("[6]: Muda a profundidade da mão positivamente", 7, self)
        self.onekeyText = genLabelText("[7]: Muda a profundidade da mão negativamente", 8, self)
        self.onekeyText = genLabelText("[8]: Reseta a posição da mão", 9, self)

    def setHandPostion(self, task):
        if self.mouseWatcherNode.hasMouse():
            mousePosition = self.mouseWatcherNode.getMouse()
            self.hand.setX(mousePosition.getX() * 2)
            self.hand.setZ(mousePosition.getY() * 1.5)
            # print(self.hand.getPos())
        return Task.cont

    def setHandDepth(self, value):
        self.hand.setY(self.hand.getY() + value)

    def resetHandPosition(self):
        self.hand.setPos(0, 5, 0)

    def changePerspective(self, firstAngle, secondAngle):
        # Muda em Y e Z
        self.hand.setP(firstAngle)
        # Muda em X e Z
        self.hand.setR(secondAngle)
        # Muda em X e Y
        # self.hand.setH(60)

    def resetPerspective(self):
        self.hand.setP(0)
        self.hand.setR(0)

    def moveFingers(self):
        self.moveLittleFinger()
        self.moveRingFinger()
        self.moveMiddleFinger()
        self.moveIndexFinger()
        self.moveThumb()

    def moveLittleFinger(self):
        self.l0LittleFinger.setP(-20)
        self.l1LittleFinger.setP(-40)
        self.l2LittleFinger.setP(-30)

    def moveRingFinger(self):
        self.r0RingFinger.setP(-20)
        self.r1RingFinger.setP(-40)
        self.r2RingFinger.setP(-30)

    def moveMiddleFinger(self):
        self.m0MiddleFinger.setP(-20)
        self.m1MiddleFinger.setP(-40)
        self.m2MiddleFinger.setP(-30)

    def moveIndexFinger(self):
        self.i0IndexFinger.setP(-20)
        self.i1IndexFinger.setP(-40)
        self.i2IndexFinger.setP(-30)

    def moveThumb(self):
        self.t0Thumb.setP(-20)
        self.t1Thumb.setR(40)
        self.t2Thumb.setP(-30)
        self.t2Thumb.setR(40)

    def resetFinger(self):
        self.l0LittleFinger.setP(0)
        self.l1LittleFinger.setP(0)
        self.l2LittleFinger.setP(0)

        self.r0RingFinger.setP(0)
        self.r1RingFinger.setP(0)
        self.r2RingFinger.setP(0)

        self.m0MiddleFinger.setP(0)
        self.m1MiddleFinger.setP(0)
        self.m2MiddleFinger.setP(0)

        self.i0IndexFinger.setP(0)
        self.i1IndexFinger.setP(0)
        self.i2IndexFinger.setP(0)

        self.t0Thumb.setP(0)
        self.t1Thumb.setR(0)
        self.t2Thumb.setP(0)
        self.t2Thumb.setR(0)


demo = TccSample()

demo.run()
