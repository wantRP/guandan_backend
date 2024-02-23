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
        self.lastAction:list=None

class Desk(object):
    def resetStatus(self):
        #self.rank=rank
        self.teamALevel='2'
        self.teamBLevel='2'
        #self.players=[Player(Position.NORTH),Player(Position.WEST),Player(Position.SOUTH),Player(Position.EAST)]
        self.hasCards=[True,True,True,True]
        self.player_num=0
        self.state=None
        self.lastActions:list[list]=[None, None, None]
        self.cur_player=-1
        self.shuffle=False
        self.level='2'
        self.finished=[]
        self.shuffle_deck()      #洗牌
        for x in self.players:
            x.lastAction=None

    def __init__(self,rank='2',total_game=20,mode="RankFrozen",port='23334'):
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
        self.total_game=total_game
    
    def begin(self):
        self.state='waiting'
        self.state='fourRemains'

        #和client连接
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.runDesk, 'localhost', 23456))
        asyncio.get_event_loop().run_forever()
    def updateLevel(self):
        self.rank='2'
        self.teamALevel='2'
        self.teamBLevel='2'
    def beginTribute(self):
        pass
    async def runDesk(self, websocket, path, shuffle=True):
        self.players[self.player_num].sock = websocket
        num = self.player_num
        self.player_num += 1
        if self.player_num == 4:    #连接的client达到4个
            for i in range(self.total_game):
            
                self.shuffle_deck()      #洗牌
                self.lastActions=[None, None, None]
                self.cur_player=0       #初始玩家根据什么规定？
                self.shuffle = True
                self.finished = []
                
                
                for x in range(4): #向四位玩家发送初始手牌
                    await self.notify_begin(self.players[x].sock, x) 
                
                await self.runPlay_4( 0)
                #self.total_game -= 1
                #升级什么的
                self.updateLevel()
                self.beginTribute()
                self.resetStatus()
            print("完全结束")
            return
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
    def getPreviousHand(a:list[list]):
        i=len(a)-1
        while(i>=0):
            if(a[i]==PASS or a[i]==None):
                i=i-1
            else:
                return a[i]
        return PASS

    async def runPlay_4(self, begin_num):
        "运行一次小局"
        print("server start")
        num=begin_num
        while True:
            for i in range(4):
                if(self.hasCards[i]==False):
                    continue
                #notify current player to act
                previousHand = self.getPreviousHand(self.lastActions)
                if(previousHand==None):
                    previousHand=PASS
                legalActions = api.getHands(self.players[i].deck, api.HandGenerator.translateToOurForm(previousHand),self.level)
                await self.send_play( i, legalActions)
                #broadcast his action
                message = await self.players[i].sock.recv()
                action = legalActions[json.loads(str(message))["actIndex"]]
                await self.send_notice_action(i, action)
                if action != PASS:
                    for card in action[2]: 
                        try:
                            self.players[i].deck.remove(card)
                        except:
                            print(self.players[i].deck,action[2])
                            raise "139"
                self.players[i].lastAction=action
                self.lastActions = self.lastActions[1:] + [action]
                #有一个人全部出牌：
                if len(self.players[i].deck) == 0:
                    
                    self.finished.append(i)
                    self.hasCards[i]=False
                    await self.runPlay_3(i)
                    return
                    if len(self.finished) == 3 or self.finished == [0, 2] or self.finished == [2, 0] or self.finished == [1, 3] or self.finished == [3, 1]:
                        await self.send_episode_over() 
                        return
                
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
    async def runPlay_3(self, finishedPos):
        print("=========3=========")
        p=finishedPos
        lastActions=[None,None]
        noFollower=True
        for i in range(4):
            p=(p+1)%4
            if(self.hasCards[p]==False):
                continue
            previousHand = self.getPreviousHand(self.lastActions)
            legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(previousHand),self.level)
            if(len(legalActions)==0):
                    print("177",self.players[p].deck,previousHand)
                    raise "200"
            await self.send_play(p, legalActions)
            message = await self.players[p].sock.recv()
            action = legalActions[json.loads(str(message))["actIndex"]]
            if(len(legalActions)==0):
                print("183",self.players[p].deck,previousHand)
                raise "206"
            await self.send_notice_action(p, action)
            if action != PASS:
                noFollower=True
                for card in action[2]: 
                    self.players[p].deck.remove(card)
            self.players[p].lastAction=action
            self.lastActions = self.lastActions[1:] + [action]
            lastActions = lastActions[1:] + [action]
            if len(self.players[p].deck) == 0:
                self.finished.append(p)
                self.hasCards[p]=False
                if(self.finished == [0, 2] or self.finished == [2, 0] or self.finished == [1, 3] or self.finished == [3, 1]):
                    print("出现双上啦！")
                    await self.send_episode_over() 
                    return
                else:
                    await self.runPlay_2(p)
                    return
        #判断首圈接风情况
        if(noFollower==True):
            p=(finishedPos+1)%4
        for i in range(4):
            p=(p+1)%4
            if(self.hasCards[p]==False):
                continue
            previousHand = self.getPreviousHand(lastActions)
            legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(previousHand),self.level)
            if(len(legalActions)==0):
                print("211",previousHand)
                raise "215"
            await self.send_play(p, legalActions)
            message = await self.players[p].sock.recv()
            action = legalActions[json.loads(str(message))["actIndex"]]
            await self.send_notice_action(p, action)
            if action != PASS:
                for card in action[2]: 
                    self.players[p].deck.remove(card)
            self.players[p].lastAction=action
            lastActions = lastActions[1:] + [action]
            if len(self.players[p].deck) == 0:
                self.finished.append(p)
                self.hasCards[p]=False
                #self.players[p].lastAction=None
                if(self.finished == [0, 2] or self.finished == [2, 0] or self.finished == [1, 3] or self.finished == [3, 1]):
                    await self.send_episode_over() 
                    return
                else:
                    await self.runPlay_2(p)
                    return
    async def runPlay_2(self, finishedPos=0): 
        print("=========2==========")
        p=finishedPos
        lastAction=self.players[p].lastAction
        firstTwoActions=[None,None]
        p_remain=0
        for i in range(4):
            p=(p+1)%4
            if(self.hasCards[p]==False):
                continue
            try:
                legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(lastAction),self.level)
            except:
                print(self.players[p].deck)
                raise "111"
            if(len(legalActions)==0):
                print("242",self.players[p].deck, api.HandGenerator.translateToOurForm(lastAction))
                raise "222"
            await self.send_play(p, legalActions)
            message = await self.players[p].sock.recv()
            action = legalActions[json.loads(str(message))["actIndex"]]
            self.players[p].lastAction=action
            await self.send_notice_action(p, action)
            firstTwoActions[p_remain]=action
            lastAction=action
            if action != PASS:
                for card in action[2]: 
                    self.players[p].deck.remove(card)
            if len(self.players[p].deck) == 0:
                    self.finished.append(p)
                    self.hasCards[p]=False
                    await self.send_episode_over() 
                    return    
            p_remain+=1
        if(firstTwoActions==[PASS,PASS]):
            p=(finishedPos+1)%4
        while(True):
            for i in range(4):
                p=(p+1)%4
                if(self.hasCards[p]==False):
                    continue
                legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(lastAction),self.level)
                await self.send_play(p, legalActions)
                message = await self.players[p].sock.recv()
                action = legalActions[json.loads(str(message))["actIndex"]]
                await self.send_notice_action(p, action)
                lastAction=action
                if action != PASS:
                    for card in action[2]: 
                        self.players[p].deck.remove(card)
                if len(self.players[p].deck) == 0:
                    self.finished.append(p)
                    self.hasCards[p]=False
                    await self.send_episode_over() 
                    return          

    async def send_play(self, pos, legalActions):
        "出牌阶段，通知当前玩家做出动作"
        #print("act")
        publicinfo = [{}, {}, {}, {}]
        #set publicinfo, 实际此信息没有利用到
        k = 0
        for i in range(4):
            publicinfo[i] = {'rest': len(self.players[i].deck), 
                                         'playArea': self.players[i].lastAction}
        """
        for i in range(1, 4):
            if len(self.players[(num+i)%4].deck) != 0:
                publicinfo[(num+i)%4] d= {'rest': len(self.players[(num+i)%4].deck), 
                                         'playArea': self.lastActions[k]}
            else:
                publicinfo[(num+i)%4] = {'rest': 0, 
                                         'playArea': None}
        """
        publicinfo[pos] = {'rest': len(self.players[pos].deck), 'playArea': None}
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
                if len(self.players[(pos+4-i)%4].deck) != 0:
                    curpos = (pos+4-i)%4
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
                if len(self.players[(pos+k)%4].deck) > 0:
                    gpos -= 1
                k += 1
            greaterpos = (pos+k-1)%4
        
        await self.players[pos].sock.send(json.dumps({"type": "act",
                                         "handsCards": self.players[pos].deck,
                                         "publicInfo": publicinfo,
                                         "selfRank": self.players[pos].level,
                                         "oppoRank": self.players[(pos+1)%4].level,
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
        print(num,self.players[num].deck,action)
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
        print("小局结束")
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
    async def send_game_over(self,curTimes):
        for i in range(4):
            await self.players[i].sock.send(json.dumps({"type": "notify",
                                            "stage": "gameOver",
                                            "curTimes": curTimes,
                                            "settingTimes": self.total_game}))
desk = Desk()
desk.begin()