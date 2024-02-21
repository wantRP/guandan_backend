import api
import random
import asyncio
import websockets
from enum import Enum
import json 

class Position(Enum):
    NORTH=0
    WEST=1
    SOUTH=2
    EAST=3

PASS=['PASS','PASS',['PASS']]

class Player(object):
    def __init__(self,position,deck=None,level='2'):
        self.deck=deck
        self.level=level
        self.position=position
        self.sock=None
        self.lastAction=None

class Desk(object):
    def __init__(self,rank='2',mode="RankFrozen",port='23334'):
        #先实现只打2，先不实现各种模式
        self.rank=rank
        self.teamALevel='2'
        self.teamBLevel='2'
        self.players=[Player(Position.NORTH),Player(Position.WEST),Player(Position.SOUTH),Player(Position.EAST)]
        self.hasCards=[True,True,True,True]
        self.player_num=0
        self.state=None
        self.lastActions:list[list]=[None, None, None]
        self.cur_player=-1
        self.shuffle=False
        self.level='2'
        self.finished=[]
        self.total_game=1
    
    def begin(self):
        self.state='waiting'
        self.state='fourRemains'

        #和client连接
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.initDesk, 'localhost', 23456))
        asyncio.get_event_loop().run_forever()
    def updateLevel(self):
        self.rank='2'
        self.teamALevel='2'
        self.teamBLevel='2'
    def beginTribute(self):
        pass
    async def initDesk(self, websocket, path, shuffle=True):
        self.players[self.player_num].sock = websocket
        num = self.player_num
        self.player_num += 1
        if self.player_num == 4:    #连接的client达到4个
            while(self.total_game>0):
            
                self.shuffle_deck()      #洗牌
                self.lastActions=[None, None, None]
                self.cur_player=0       #初始玩家根据什么规定？
                self.shuffle = True
                self.finished = []
                
                #升级什么的
                for x in range(4): #向四位玩家发送初始手牌
                    await self.notify_begin(self.players[x].sock, x) 
                
                await self.runPlay_4( 0)
                self.total_game -= 1
                self.updateLevel()
                self.beginTribute()
            print("完全结束")
        else:
            
            await asyncio.Future()

    def shuffle_deck(self)->None:
        """随机发牌"""
        fullDeck=api.FULL_DECK
        random.shuffle(fullDeck)
        self.players[0].deck = fullDeck[0:13]
        self.players[1].deck = fullDeck[13:26]
        self.players[2].deck = fullDeck[26:39]
        self.players[3].deck = fullDeck[39:52]

    async def notify_begin(self, websocket, num):
        """通知小局开始，将初始手牌信息发送给单个client"""
        
        await websocket.send(json.dumps({"type": "notify",
                                         "stage": "beginning",
                                         "handCards": self.players[num].deck,
                                         "myPos": num}))
        #print(num)

    def sendState(self):
        pass
    
    @staticmethod
    def getPreviousHand(a):
        i=len(a)-1
        while(i>=0):
            if(a[i]==PASS):
                i=i-1
            else:
                return a[i]
        return PASS

    async def runPlay_4(self, begin_num=0):
        print("server start")
        num=begin_num
        while True:
            for i in range(4):
                if(self.hasCards[i]==False):
                    continue
                previousHand = self.getPreviousHand(self.lastActions)
                if(previousHand==None):
                    previousHand=PASS
                legalActions = api.getHands(self.players[i].deck, api.HandGenerator.translateToOurForm(previousHand),self.level)
                #print("legalactions:\n",legalActions)
                await self.send_legalActions( i, legalActions)
                message = await self.players[i].sock.recv()
                action = legalActions[json.loads(str(message))["actIndex"]]
                await self.send_notice_action(i, action)
                if action != PASS:
                    for card in action[2]: 
                        self.players[i].deck.remove(card)
                if len(self.players[i].deck) == 0:
                    self.finished.append(i)
                    self.hasCards[i]=False
                    if len(self.finished) == 3 or self.finished == [0, 2] or self.finished == [2, 0] or self.finished == [1, 3] or self.finished == [3, 1]:
                        await self.send_episode_over() 
                        return
                self.lastActions = self.lastActions[1:] + [action]
                """
                all_pass = True
                for i in range(0, 4-1-len(self.finished)):
                    if self.lastActions[-1-i] != PASS:
                        all_pass = False
                        break
                if all_pass == True:
                    self.lastActions = [PASS for _ in range(3-len(self.finished))]
                    self.cur_player = (self.finished[-1]+2)%4
                else:
                    for i in range(1, 4):
                        if len(self.players[(num+i)%4].deck) > 0:
                            self.cur_player = (num+i)%4
                            break
                """
    #出牌阶段，通知当前玩家做出动作
    async def send_legalActions(self, num, legalActions):
        #print("act")
        publicinfo = [{}, {}, {}, {}]
        publicinfo[num] = {'rest': len(self.players[num].deck), 'playArea': None}
        #set publicinfo
        k = 0
        for i in range(1, 4):
            if len(self.players[(num+i)%4].deck) != 0:
                publicinfo[(num+i)%4] = {'rest': len(self.players[(num+i)%4].deck), 
                                         'playArea': self.lastActions[k]}
            else:
                publicinfo[i] = {'rest': 0, 
                                         'playArea': None}
        publicinfo[num] = {'rest': len(self.players[num].deck), 'playArea': None}
        #set end
        curpos = -1
        curaction = None
        greateraction = None
        greaterpos = -1
        all_pass = True
        greateraction = self.getPreviousHand(self.lastActions)

        for action in self.lastActions:
            if action != PASS:
                all_pass = False
                break
        if all_pass == False:
            for i in range(1, 4):
                if len(self.players[(num+4-i)%4].deck) != 0:
                    curpos = (num+4-i)%4
                    break
            curaction = self.lastActions[-1]
            k = 0
            gpos = -1
            for action in self.lastActions:
                k += 1
                if action != PASS:
                    greateraction = action
                    gpos = k
            k = 1
            while gpos > 0:
                if len(self.players[(num+k)%4].deck) > 0:
                    gpos -= 1
                k += 1
            greaterpos = (num+k-1)%4
        await self.players[num].sock.send(json.dumps({"type": "act",
                                         "handsCards": self.players[num].deck,
                                         "publicInfo": publicinfo,
                                         "selfRank": self.players[num].level,
                                         "oppoRank": self.players[(num+1)%4].level,
                                         "curRank": self.level,
                                         "stage": "play",
                                         "curPos": curpos,
                                         "curAction": curaction,
                                         "greaterAction": greateraction,
                                         "greaterPos": greaterpos,
                                         "actionList": legalActions,
                                         "indexRange": len(legalActions)-1}))

    #出牌阶段，通知其他玩家做出的动作
    async def send_notice_action(self, num, action):
        """出牌阶段，通知所有四个玩家当前玩家的动作"""
        greaterpos = num
        greateraction = action
        if action == PASS:
            gpos = -1
            k = 1
            for action_ in self.lastActions:
                if action_ != PASS:
                    #greateraction = api.HandGenerator.translateToBlackBoxForm(action_)
                    gpos = k
                k += 1
            k = 1
            while gpos > 0:
                if len(self.players[(num+k)%4].deck) > 0:
                    gpos -= 1
                k += 1
            greaterpos = (num+k-1)%4 

        for i in range(0, 4):
            await self.players[i].sock.send(json.dumps({"type": "notify",
                                            "stage": "play",
                                            "curPos": num,
                                            "curAction": action,
                                            "greaterPos": greaterpos,
                                            "greaterAction": greateraction}))
    
    #通知所有玩家小局结束
    async def send_episode_over(self):
        """通知所有玩家小局结束"""
        restcards = []
        for i in range(0, 4):
            if len(self.players[i].deck) > 0:
                self.finished.append(i)
                restcards.append([i, self.players[i].deck])
        for i in range(0, 4):
            await self.players[i].sock.send(json.dumps({"type": "notify",
                                            "stage": "episodeOver",
                                            "order": self.finished,
                                            "curRank": self.level,
                                            "restCards": restcards}))

desk = Desk()
desk.begin()