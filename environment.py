import time
import api
import random
import asyncio
import websockets
from enum import Enum
import json 
from typing import List, Any

PASS=['PASS','PASS',['PASS']]

class Player(object):
    def __init__(self,deck=None,level='2'):
        self.deck=deck
        self.level=level
        self.sock=None
        self.lastAction:list=None

class Server(object):
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

    def __init__(self,rank='2',total_game=1,actOrder=-1,mode="RankFrozen",port='23456'):
        #先实现只打2，先不实现各种模式
        print("desk made")
        self.rank=rank
        self.teamALevel='2'
        self.teamBLevel='2'
        self.players=[Player(),Player(),Player(),Player()]
        self.hasCards=[True,True,True,True]
        self.player_num=0
        self.state=None
        self.lastActions:List[list]=[None, None, None]
        self.cur_player=-1
        self.shuffle=False
        self.level='2'
        self.finished=[]
        self.total_game=total_game
        self.port=port
        self.shutdown_event = asyncio.Event()
        self.hasFuture=False
        self.position=actOrder
    async def begin(self):
        self.resetStatus()
        async with websockets.serve(self.runDesk, '0.0.0.0', self.port):
            await self.shutdown_event.wait()
    def updateLevel(self):
        self.rank='2'
        self.teamALevel='2'
        self.teamBLevel='2'
    def beginTribute(self):
        pass
    async def runDesk(self, websocket, path, shuffle=True):
        try:
            if(self.player_num<4):
                if not self.hasFuture:
                    self.future=asyncio.Future()
                    self.hasFuture=True
                print(self.player_num)
                self.players[self.player_num].sock = websocket
                num = self.player_num
                self.player_num += 1
            if self.player_num == 4:    #连接的client达到4个
                if(self.position!=-1):
                    self.players[self.position],self.players[3]=self.players[3],self.players[self.position]
                for i in range(self.total_game):
                    self.shuffle_deck()      #洗牌
                    self.lastActions=[None, None, None]
                    self.cur_player=0       #初始玩家根据什么规定？
                    self.shuffle = True
                    self.finished = []
                    for x in range(4): #向四位玩家发送初始手牌
                        await self.notify_begin(self.players[x].sock, x) 
                    await self.runPlay_4( 0)
                    #升级什么的
                print("完全结束")
                self.future.set_result(0)
                for x in self.players:
                    await x.sock.close(code=1001,reason="final")
                self.shutdown_event.set()
                return
            if(self.player_num>4):
                await websocket.close(code=1001, reason="Server Overloaded")
                self.player_num-=1
                return
            await self.future
            return
        except websockets.exceptions.ConnectionClosed:
            print("CLOSE")
            for x in self.players:
                if x.sock.open:
                    await x.sock.close(code=1001,reason="final")
            self.shutdown_event.set()
        finally:
            if websocket.open:
                await websocket.close()
            

    def shuffle_deck(self)->None:
        """随机发牌"""
        fullDeck=api.FULL_DECK
        random.shuffle(fullDeck)
        self.players[0].deck = fullDeck[0:27]
        self.players[1].deck = fullDeck[27:54]
        self.players[2].deck = fullDeck[54:81]
        self.players[3].deck = fullDeck[81:108]

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
    def getPreviousHand(a:List[list]):
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
                #print("Player ",i,len(legalActions),legalActions[:5])
                await self.send_play( i, legalActions)
                #broadcast his action
                while True:
                    message = await self.players[i].sock.recv()
                    actionIndex=json.loads(str(message))["actIndex"]
                    if(actionIndex>=len(legalActions)):
                        await self.send_error(i)
                    else:
                        break
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
            print("")
                
    async def runPlay_3(self, finishedPos):
        print("=========3=========")
        p=finishedPos
        lastActions=[None,self.lastActions[-1]]
        noFollower=True
        for i in range(4):
            p=(p+1)%4
            if(not self.hasCards[p]):
                continue
            previousHand = self.getPreviousHand(self.lastActions)
            legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(previousHand),self.level)
            if(len(legalActions)==0):
                    print("177",self.players[p].deck,previousHand)
                    raise "200"
            await self.send_play(p, legalActions)
            while True:
                    message = await self.players[i].sock.recv()
                    actionIndex=json.loads(str(message))["actIndex"]
                    if(actionIndex>=len(legalActions)):
                        await self.send_error(i)
                    else:
                        break
            action = legalActions[json.loads(str(message))["actIndex"]]
            if(len(legalActions)==0):
                print("183",self.players[p].deck,previousHand)
                raise "206"
            await self.send_notice_action(p, action)
            if action != PASS:
                noFollower=False
                for card in action[2]: 
                    self.players[p].deck.remove(card)
            self.players[p].lastAction=action
            self.lastActions = self.lastActions[1:] + [action]
            lastActions = lastActions[1:] + [action]
            if len(self.players[p].deck) == 0:
                self.finished.append(p)
                self.hasCards[p]=False
                if(self.finished == [0, 2] or self.finished == [2, 0] or self.finished == [1, 3] or self.finished == [3, 1]):
                    await self.send_episode_over() 
                    return
                else:
                    await self.runPlay_2(p)
                    return
        #判断首圈接风情况
        if(noFollower==True):
            p=(finishedPos+1)%4
            print(lastActions)
            #lastActions=[PASS,PASS]
        while(True):
            print("")
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
                while True:
                    message = await self.players[i].sock.recv()
                    actionIndex=json.loads(str(message))["actIndex"]
                    if(actionIndex>=len(legalActions)):
                        await self.send_error(i)
                    else:
                        break
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
        upperAction=self.players[p].lastAction
        firstTwoActions=[self.players[p].lastAction,None]
        p_remain=0
        for i in range(4):
            p=(p+1)%4
            if(self.hasCards[p]==False):
                continue
            legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(upperAction),self.level)
            if(len(legalActions)==0):
                print("242",self.players[p].deck, api.HandGenerator.translateToOurForm(upperAction))
                raise "222"
            await self.send_play(p, legalActions)
            while True:
                message = await self.players[i].sock.recv()
                actionIndex=json.loads(str(message))["actIndex"]
                if(actionIndex>=len(legalActions)):
                    await self.send_error(i)
                else:
                    break
            self.players[p].lastAction=action
            await self.send_notice_action(p, action)
            firstTwoActions[p_remain]=action
            upperAction=action
            if action != PASS:
                upperAction=action
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
            upperAction=PASS
        while(True):
            for i in range(4):
                p=(p+1)%4
                if(self.hasCards[p]==False):
                    continue
                legalActions = api.getHands(self.players[p].deck, api.HandGenerator.translateToOurForm(upperAction),self.level)
                await self.send_play(p, legalActions)
                while True:
                    message = await self.players[i].sock.recv()
                    actionIndex=json.loads(str(message))["actIndex"]
                    if(actionIndex>=len(legalActions)):
                        await self.send_error(i)
                    else:
                        break
                action = legalActions[json.loads(str(message))["actIndex"]]
                await self.send_notice_action(p, action)
                upperAction=action
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
                                         "handCards": self.players[pos].deck,
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

    async def send_error(self, num, message="出牌不符合规则"):
        await self.players[num].sock.send(json.dumps({"type": "error",
                                            "message": message}))
    async def send_notice_action(self, num, action):
        """出牌阶段，通知所有四个玩家当前玩家的动作"""
        time.sleep(0.5)        
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
        print(num,action)
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
#desk = Server()
#asyncio.get_event_loop().run_until_complete(desk.begin())