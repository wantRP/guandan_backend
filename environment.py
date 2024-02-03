import api
import random
from enum import Enum
class Position(Enum):
    NORTH=0
    WEST=1
    SOUTH=2
    EAST=3
PASS=['PASS','PASS',['PASS']]
class Player(object):
    def __init__(self,position,level='2'):
        self.level=level
        self.position=position
class Desk(object):
    def __init__(self,rank='2',mode="RankFrozen",port='23334'):
        #先实现只打2，先不实现
        self.rank=rank
        self.teamALevel='2'
        self.teamBLevel='2'
        self.players=[None,None,None,None]
        while(True):
            self.runPlay()
            self.setLevel()
            self.tribute()
        pass
    def sendState(self):
        pass
    def getPreviousHand(a):
        i=2
        while(i>=0):
            if(a[i]==PASS):
                i=i-1
            else:
                return a[i]
        return PASS
    def runPlay(self):
        state='fourRemains'
        fullDeck=api.FULL_DECK
        random.shuffle(fullDeck)
        self.players[0]=Player(fullDeck[0:13],Position.NORTH)
        self.players[1]=Player(fullDeck[13:26],Position.SOUTH)
        self.players[2]=Player(fullDeck[26:39],Position.WEST)
        self.players[3]==Player(fullDeck[39:52],Position.EAST)
        lastThreeActions=[PASS,PASS,PASS]
        while(state=='fourRemains'):
            p=0
            previousHand=self.getPreviousHand(lastThreeActions)
            legalActions=api.getHands(self.players[p],previousHand)#上家手牌和自己所有手牌
            """
            send legalActions to player[p]
            currentAction=translateToOurs(receive( player[p]'s action))
            if((currentAction in legalActions)==False):
              currentAction=random from legalActions
            lastThreeActions=lastThreeActions[1:]+[currentAction]
            remove cards(currentAction) from players[i]
            lastTurn=player[p]'s action
            check state
            """
            p=(p+1) % 4
            
            
            pass
        while(state=='threeRemains'):
            """
            positionPointer=0
            #handle player[p]'s action
            #p=(p+1) % 3
            if dubleupper:
                handle
            else:
                status='tworemains'
            """
            pass
        while(state=='tworemains'):
            pass
        self.setLevel()