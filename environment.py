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

class Desk(object):
    def __init__(self,rank='2',mode="RankFrozen",port='23334'):
        #先实现只打2，先不实现各种模式
        self.rank=rank
        self.teamALevel='2'
        self.teamBLevel='2'
        self.players=[Player(Position.NORTH),Player(Position.WEST),Player(Position.SOUTH),Player(Position.EAST)]
        self.player_num=0
        self.state=None
        self.lastActions:list[list]=None
        self.cur_player=-1
        self.shuffle=False
        self.cur_level='2'
        self.order=[]
        self.total_game=1
    
    def begin(self):
        self.state='waiting'
        self.state='fourRemains'

        #和client连接
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.playgame, 'localhost', 23456))
        asyncio.get_event_loop().run_forever()
    def setLevel(self):
        self.rank='2'
        self.teamALevel='2'
        self.teamBLevel='2'
    def tribute(self):
        pass
    async def playgame(self, websocket, path, shuffle=True):
        self.players[self.player_num].sock = websocket
        num = self.player_num
        self.player_num += 1

        if self.player_num == 4:    #连接的client达到4个
            while(self.total_game>0):
            
                self.shuffle_deck()      #洗牌
                self.lastActions=[PASS, PASS, PASS]
                self.cur_player=0       #初始玩家根据什么规定？
                self.shuffle = True
                self.order = []
                self.total_game -= 1
                #升级什么的
                for x in range(4):
                    await self.send_begin_deck(self.players[x].sock, x)
                #await self.send_begin_deck(websocket, num)     #向当前玩家发送初始手牌
                await self.runPlay(websocket, 0)
                self.setLevel()
                self.tribute()
        else:
            
            await asyncio.Future()

    def shuffle_deck(self):
        """随机发牌"""
        fullDeck=api.FULL_DECK
        random.shuffle(fullDeck)
        self.players[0].deck = fullDeck[0:13]
        self.players[1].deck = fullDeck[13:26]
        self.players[2].deck = fullDeck[26:39]
        self.players[3].deck = fullDeck[39:52]

    async def send_begin_deck(self, websocket, num):
        """将初始手牌信息发送给client"""
        
        await websocket.send(json.dumps({"type": "notify",
                                         "stage": "beginning",
                                         "handCards": self.players[num].deck,
                                         "myPos": num}))
        print(num)

    def sendState(self):
        pass

    def getPreviousHand(a):
        i=len(a)-1
        while(i>=0):
            if(a[i]==PASS):
                i=i-1
            else:
                return a[i]
        return PASS

    async def runPlay(self, websocket, num):
        print("runplay")
        while True:
            previousHand = self.getPreviousHand(self.lastActions)
            legalActions = api.getHands(self.players[num].deck, api.HandGenerator.translateToOurForm(previousHand))
            self.send_legalactions(websocket, num, legalActions)
            message = await websocket.recv()
            action = legalActions[json.loads(str(message))["actIndex"]]
            self.send_notice_action(num, action)
            if action != PASS:
                for card in action[2]:
                    self.players[num].deck.remove(card)
            if len(self.players[num].deck) == 0:
                self.order.append(num)
                if len(self.order) == 3 or self.order == [0, 2] or self.order == [2, 0] or self.order == [1, 3] or self.order == [3, 1]:
                    self.send_episode_over(num) 
                    break
            self.lastActions = self.lastActions[1:] + [action]
            all_pass = True
            for i in range(0, 4-len(self.order)):
                if self.lastActions[-1-i] != PASS:
                    all_pass = False
                    break
            if all_pass == True:
                self.lastActions = [PASS for _ in range(3-len(self.order))]
                self.cur_player = (self.order[-1]+2)%4
            else:
                for i in range(1, 4):
                    if len(self.players[(num+i)%4].deck) > 0:
                        self.cur_player = (num+i)%4
                        break

    #出牌阶段，通知当前玩家做出动作
    async def send_legalactions(self, websocket, num, legalActions):
        print("act")
        publicinfo = [{}, {}, {}, {}]
        publicinfo[num] = {'rest': len(self.players[num].deck), 'playArea': None}
        k = 0
        for i in range(1, 4):
            if len(self.players[(num+i)%4].deck) != 0:
                publicinfo[(num+i)%4] = {'rest': len(self.players[(num+i)%4].deck), 
                                         'playArea': self.lastActions[k]}
                k += 1
            else:
                publicinfo[(num+i)%4] = {'rest': 0, 
                                         'playArea': None}
        curpos = -1
        curaction = None
        greateraction = None
        greaterpos = -1
        all_pass = True
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


        await websocket.send(json.dumps({"type": "act",
                                         "handsCards": self.players[num].deck,
                                         "publicInfo": publicinfo,
                                         "selfRank": self.players[num].level,
                                         "oppoRank": self.players[(num+1)%4].level,
                                         "curRank": self.cur_level,
                                         "stage": "play",
                                         "curPos": curpos,
                                         "curAction": curaction,
                                         "greaterAction": greateraction,
                                         "greaterPos": greaterpos,
                                         "actionList": legalActions,
                                         "indexRange": len(legalActions)-1}))

    #出牌阶段，通知其他玩家做出的动作
    async def send_notice_action(self, num, action):
        greaterpos = num
        greateraction = action
        if action == PASS:
            gpos = -1
            k = 1
            for action_ in self.lastActions:
                if action_ != PASS:
                    greateraction = api.HandGenerator.translateToBlackBoxForm(action_)
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
    async def send_episode_over(self, num):
        restcards = []
        for i in range(0, 4):
            if len(self.players[i].deck) > 0:
                self.order.append(i)
                restcards.append([len(self.players[i].deck), self.players[i].deck])
        for i in range(0, 4):
            await self.players[i].sock.send(json.dumps({"type": "notify",
                                            "stage": "episodeOver",
                                            "order": self.order,
                                            "curRank": self.cur_level,
                                            "restCards": restcards}))

desk = Desk()
desk.begin()