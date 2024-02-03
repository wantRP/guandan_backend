from enum import Enum
from functools import cmp_to_key
from collections import defaultdict, namedtuple
from itertools import combinations,product
import collections
import itertools
FULL_DECK = [
    # 黑桃Spades、红桃Hearts、梅花Clubs、方片Diamonds分别对应字符S, H, C, D
    # 级牌表示为SL CL 2L
 'SB', # 小王
 'HR', # 大王
 #HL 红心级牌
 'S2', 'C2', 'H2', 'D2', 
 'SA', 'CA', 'HA', 'DA', 
 'SK', 'CK', 'HK', 'DK', 
 'SQ', 'CQ', 'HQ', 'DQ', 
 'SJ', 'CJ', 'HJ', 'DJ', 
 'ST', 'CT', 'HT', 'DT', # 10
 'S9', 'C9', 'H9', 'D9', 
 'S8', 'C8', 'H8', 'D8', 
 'S7', 'C7', 'H7', 'D7', 
 'S6', 'C6', 'H6', 'D6', 
 'S5', 'C5', 'H5', 'D5', 
 'S4', 'C4', 'H4', 'D4', 
 'S3', 'C3', 'H3', 'D3']
RANK=['B', 'R', 'L', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
RANK_WITHOUT_WILD=[ 'A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
RANK_NUM={'R': 17, 'B': 16, 'L': 15, 'A': 13, 'K': 12, 'Q': 11, 'J': 10, 'T': 9, 
           '9': 8, '8': 7, '7': 6, '6': 5, '5': 4, '4': 3, '3': 2, '2': 1,'1':0}
NUM_RANK={17: 'R', 16: 'B', 15: 'L', 13: 'A', 12: 'K', 11: 'Q', 10: 'J', 9: 'T', 8: '9', 7: '8', 6: '7', 5: '6', 4: '5', 3: '4', 2: '3', 1: '2', 0: 'A'}

class HandType(Enum):
    PASS = 0
    SINGLE = 1
    PAIR = 2
    TRIPLE_OF_PAIR=3# 6 三连对，没有三带一
    TRIPLE=4# 3 ok
    PLATE=5# 6
    FULLHOUSE=6 #5 ok
    STRAIGHT=7# 5 ok
    BOMB_4=8# 4 ok
    BOMB_5=9# 5 ok
    FLUSH=10# 5 ok
    BOMB_6=11# 6
    BOMB_7=12# 7
    BOMB_8=13# 8
    BOMB_KING=14# 4 ok
    INVALID=15
OURS_BLACK_BOX={
    HandType.PASS:"PASS",
    HandType.SINGLE :"Single",
    HandType.PAIR :"Pair",
    HandType.TRIPLE_OF_PAIR:"ThreePair",
    HandType.TRIPLE:"Trips",
    HandType.PLATE:"TwoTrips",
    HandType.FULLHOUSE:"ThreeWithTwo",
    HandType.STRAIGHT:"Straight",
    HandType.BOMB_4:"Bomb",
    HandType.BOMB_5:"Bomb",
    HandType.FLUSH:"StraightFlush",
    HandType.BOMB_6:"Bomb",
    HandType.BOMB_7:"Bomb",
    HandType.BOMB_8:"Bomb",
    HandType.BOMB_KING:"Bomb"
}
BLACK_BOX_OURS={
    'PASS': HandType.PASS,
    'Single': HandType.SINGLE,
    'Pair': HandType.PAIR,
    'ThreePair': HandType.TRIPLE_OF_PAIR,
    'Trips': HandType.TRIPLE,
    'TwoTrips': HandType.PLATE,
    'ThreeWithTwo': HandType.FULLHOUSE,
    'Straight': HandType.STRAIGHT,
    'Bomb': HandType.BOMB_4,
    'StraightFlush': HandType.FLUSH
}

Hand = namedtuple('Hand', ['handType', 'rank', 'cards','wildCardUsed'])
class HandGenerator(object):
    def __init__(self, handCards,level='2'):
        #初始化后，会把牌升序排序，，级牌在普通牌后，红心级牌在普通级牌后。注意，大小王在级牌后
        self.handCards = handCards
        self.level=level
        self.wildCount=0
        self.wildCard='H'+self.level
        self.nonWildCards:list[str]=[]#非万能牌的列表
        self.pairs=None
        self.triples=None
        self.pointedCards:list[list[str]] = [[] for _ in range(14)]#A23 ... QKA排列，级牌按实际点数
        self.handCards=self.sortHand(handCards) #升序的手牌的列表
        for x in self.handCards:
           if(x==self.wildCard):
               self.wildCount=self.wildCount+1
           else:
               self.nonWildCards=self.nonWildCards+[x]
               if(x[1]!='B' and x[1]!='R'):
                   self.pointedCards[RANK_NUM[x[1]]]=self.pointedCards[RANK_NUM[x[1]]]+[x]
               if(x[1]=='A'):
                   self.pointedCards[0]=self.pointedCards[0]+[x]
           pass
        self.pointedCount=[len(x) for x in self.pointedCards]
    @staticmethod
    def translateToBlackBoxForm(a:list)->list:
        a[0]=OURS_BLACK_BOX[a[0]]
        return a[-1]
    @staticmethod
    def translateToOurForm(a:list)->list:
        if(a[0]=='Bomb'):
            if(len(a[2])==4): a[0]==HandType.BOMB_4
            if (a[2][0]=='SB' or a[2][1]=='SB' or a[2][2]=='SB' or a[2][3]=='SB'):
                a[0]=HandType.BOMB_KING
            if(len(a[2])==4): a[0]==HandType.BOMB_5
            if(len(a[2])==4): a[0]==HandType.BOMB_6
            if(len(a[2])==4): a[0]==HandType.BOMB_7
            if(len(a[2])==4): a[0]==HandType.BOMB_8
            return a
        a[0]=BLACK_BOX_OURS[a[0]]
        return a
    @staticmethod
    def compareSingle(a,b)->bool:
        if(RANK_NUM[a[1]]<RANK_NUM[b[1]]):
            return -1
        elif RANK_NUM[a[1]]>RANK_NUM[b[1]]:
            return 1
        else:
            if(b[0]=='H'):
                return -1
            else:
                return 0
        return 0

    def sortHand(self,a,byRealPoint=False):
        """
        接受和返回的有序牌组。级牌（含红心）均为实际点数，没有特殊表示。levelMask=True时，将按照实际点数排序。
        """
        if(byRealPoint==False):
            level=self.level
            a=[x[0]+'L' if x[1]==level else x for x in a]
            a=sorted(a,key=cmp_to_key(self.compareSingle))
            a=[x[0]+level if x[1]=="L" else x for x in a]
        else:
            a=[x[0]+'1' if x[1]=='A' else x for x in a]
            a=sorted(a,key=cmp_to_key(self.compareSingle))
            #a=[x[0]+"A" if x[1]=="1" else x for x in a]
        return a
    #legal: player_hand_card and rival_move:can be NULL ->legal_action
    @classmethod
    def getHandType(self,a:list[str])->str:#H5 etc
        """
        废弃的方法！升序排列的牌组，级牌不特殊表示
        SB HR
        """
        level=self.level
        a=self.sortHand(a)
        cardCount=len(a)
        wildCard="H"+level
        wildCount=0
        for x in a:
            if(x==wildCard):
                wildCount=wildCount+1
        points=[x[1] for x in a]
        if(cardCount==1): return HandType.SINGLE
        if(cardCount==2):
            if(a[0][1]==a[1][1]): return HandType.PAIR
            if(a[1]==wildCard):return HandType.PAIR
            return HandType.INVALID #joker, etc
        if(cardCount==3):
            if(points[0]==points[1]==points[2]): return HandType.TRIPLE
            if(wildCount==1 and points[0]==points[1]): return HandType.TRIPLE
            if(wildCount==2 and a[2]!=level): return HandType.TRIPLE #joker
            return HandType.INVALID
        if(cardCount==4):
            if(points[0]=='B' and points[1]=='B' and points[2]=='R' and points[3]=='R'): return HandType.BOMB_KING
            if(points[0]==points[3]): return HandType.BOMB_4
            if(points[0]==points[1]==points[2] and a[3]==wildCard):return HandType.BOMB_4
            if(points[0]==points[1] and a[2]==a[3]==wildCard):return HandType.BOMB_4
            return HandType.INVALID
        if(cardCount==5):
            if(points[0]==points[4]): return HandType.BOMB_5
            if(points[0]==points[3] and a[4]==wildCard):return HandType.BOMB_5
            if(points[0]==points[2] and a[3]==a[4]==wildCard):return HandType.BOMB_5
            if(wildCount==1):
                if(points[0]==points[1]!=points[2]):
                    if(points[2]==points[3] or points[3]==points[4]):#AABB* or AA*JJ
                        return HandType.FULLHOUSE
                    else: #joker
                        return HandType.INVALID
                if(points[0]==points[1]==points[2] and a[4]==wildCard):return HandType.FULLHOUSE
                return HandType.INVALID
            if(wildCount==2): #A**JJ || AAB** that not AA**J ||  ABB**
                if(points[3]==points[4]>=RANK_NUM['B'] or (points[0]==points[1] and a[2]!=wildCard) or points[1]==points[2]):return HandType.FULLHOUSE
            if(points[0]==points[1] and points[3]==points[4] and (points[2]==points[1] or points[2]==points[3]) ): return HandType.FULLHOUSE         
            #straight
            flush=False
            realPointHands=self.sortHand(a,level,True)
            #duplicate in former 4 cards or joker
            if(RANK_NUM[points[4]]>=RANK_NUM['B'] or points[0]==points[1] or points[1]==points[2] or points[2]==points[3]): return HandType.INVALID
            if(wildCount==0):
                if(RANK_NUM[realPointHands[4][1]] - RANK_NUM[realPointHands[0][1]]!=4 or RANK_NUM[points[4]]-RANK_NUM[points[0]]!=4): return HandType.INVALID
                if(a[0][0]==a[1][0]==a[2][0]==a[3][0]==a[4][0]): flush=True
            if(wildCount==1):
                realPointHands=self.sortHand(a[:-1],level,True)#A???\*
                if(realPointHands[0]=='1'): #special treat
                    if(realPointHands[1]=='1'): return HandType.INVALID
                    gap=RANK_NUM[realPointHands[2][1]]-RANK_NUM[realPointHands[1][1]]-1+RANK_NUM[realPointHands[3][1]]-RANK_NUM[realPointHands[2][1]]-1
                    if(gap>1):return HandType.INVALID
                    if(RANK_NUM['3']<RANK_NUM[realPointHands[1][1]]<RANK_NUM['10']): return HandType.INVALID 
                if( RANK_NUM[realPointHands[3][1]]-RANK_NUM[realPointHands[0][1]]>4): return HandType.INVALID
                if(a[0][0]==a[1][0]==a[2][0]==a[3][0]): flush=True
            if(wildCard==2):
                realPointHands=self.sortHand(a[:-2],level,True)
                if(realPointHands[0]=='1'):
                    if(RANK_NUM[realPointHands[2][1]]-RANK_NUM[realPointHands[1][1]]-1>2 and RANK_NUM['4']<realPointHands[1][1]<RANK_NUM['10']):return HandType.INVALID
                if(RANK_NUM[points[2]]-RANK_NUM[points[0]]>4):return HandType.INVALID
                if(a[0][0]==a[1][0]==a[2][0]): flush=True
            return HandType.FLUSH if flush==True else HandType.STRAIGHT
        #max triple pair:QQKKAA min: AA2233
        if(cardCount==6):
            #AAA222 KKKAAA AA2233 QQKKAA
            if((points[0]==points[5])or (points[0]==points[4] and a[5]==wildCard) or (points[0]==points[3] and a[4]==a[5]==wildCard)):return HandType.BOMB_6
            if(points[0]==points[3] or points[1]==points[4] or points[4]==points[5]): return HandType.INVALID
            if(RANK_NUM[points[5]]>=RANK_NUM['B']): return HandType.INVALID
            realPointHands=self.sortHand(a[:wildCount],level,True)
            realPoints=[x[1] for x in realPointHands]
            if(wildCount==0):
                if(points[0]==points[2] and points[3]==points[5]):#maybe plate
                    if(realPointHands[0][1]=='1'):
                         if(realPoints[3]=='2' or realPoints[3]=='K'):
                            return HandType.PLATE
                         return HandType.INVALID
                    if(RANK_NUM[points[3]]-RANK_NUM[points[2]]==1):return HandType.PLATE
            if(wildCount==1):
                if(points[0]==points[2] and points[3]==points[4]):#AAABB*
                    if(RANK_NUM[points[3]]-RANK_NUM[points[2]]==1 or RANK_NUM[realPoints[3]]-RANK_NUM[realPoints[2]]==1):
                        return HandType.PLATE
                if(points[0]==points[1] and points[2]==points[4]):#AABBB*
                    if(RANK_NUM[realPoints[2]]-RANK_NUM[realPoints[1]]==1 or RANK_NUM[points[2]]-RANK_NUM[points[1]]==1):
                        return HandType.PLATE
            if(wildCount==2):
                gap=0
                if(realPointHands[1]==realPointHands[3]):
                    gap=RANK_NUM[realPoints[1]]-RANK_NUM[realPoints[0]]
                if(realPoints[0]==realPoints[1] and realPoints[2]==realPoints[3]):
                    gap=RANK_NUM[realPoints[2]]-RANK_NUM[realPoints[1]]
                if(realPoints[0]==realPoints[2]):
                    gap=RANK_NUM[realPoints[3]]-RANK_NUM[realPoints[2]]
                if(gap==1 or gap==RANK_NUM['K']-RANK_NUM['1']):
                    return HandType.PLATE
            if(wildCount==0):
                if(realPoints[0]==realPoints[1] and realPoints[2]==realPoints[3] and realPoints[4]==realPoints[5]):
                    if(RANK_NUM[points[2]]-RANK_NUM[points[0]]-1+RANK_NUM[points[4]]-RANK_NUM[points[2]]-1==0 or  (realPoints[0]=='1' and realPoints[2]=='2' and realPoints[4]=='3')):
                        return HandType.TRIPLE_OF_PAIR
            if(wildCount==1):
                if((realPoints[0]==realPoints[1] and realPoints[2]==realPoints[3]) or (realPoints[0]==realPoints[1] and realPoints[3]==realPoints[4]) or (realPoints[1]==realPoints[2] and realPoints[3]==realPoints[4])):
                    if(RANK_NUM[points[2]]-RANK_NUM[points[0]]-1+RANK_NUM[points[4]]-RANK_NUM[points[2]]-1==0 or (realPoints[0]=='1' and realPoints[2]=='2' and realPoints[4]=='3')):
                        return HandType.TRIPLE_OF_PAIR
            if(wildCount==2):
                if(realPoints[0]==realPoints[1]):#AA----
                    if(realPoints[1]==realPoints[2]): return HandType.INVALID
                    if(realPoints[2]==realPoints[3]):#AABB--
                        if(RANK_NUM[realPoints[2]]-RANK_NUM[realPoints[1]]<=2 or RANK_NUM[realPoints[2]]-RANK_NUM[realPoints[1]]>=RANK_NUM['Q']-RANK_NUM['A']):
                            return HandType.TRIPLE_OF_PAIR
                        else:#AADD--
                            return HandType.INVALID
                        #AABC**
                    if((RANK_NUM[realPoints[2]]-RANK_NUM[realPoints[1]]==1 and RANK_NUM[realPoints[3]]-RANK_NUM[realPoints[2]]==1 ) or (realPoints[0]=='1' and realPoints[2]=='Q' and realPoints[3]=='K')): return HandType.TRIPLE_OF_PAIR
                if((realPoints[1]==realPoints[2]) or (realPoints[2]==realPoints[3])):
                    if((RANK_NUM[realPoints[1]]-RANK_NUM[realPoints[0]]==1 and RANK_NUM[realPoints[3]]-RANK_NUM[realPoints[1]]==1 ) or (realPoints[0]=='1' and realPoints[1]=='Q' and realPoints[3]=='K')): return HandType.TRIPLE_OF_PAIR
            return HandType.INVALID
        if(cardCount==7):
            if(points[0]==points[6-wildCount] and points[6-wildCount]==points[6]): return HandType.BOMB_7
        if(cardCount==8):
            if(points[0]==points[7-wildCount] and points[7-wildCount]==points[7]): return HandType.BOMB_8
        return HandType.INVALID
    
    def getSingles(self)->list:
        l=[]
        gotWild=False
        for x in self.handCards:
            if(x!=self.wildCard):
                l=l+[Hand(HandType.SINGLE,x[1],[x],0)]
            elif gotWild==False:
                for y in RANK_WITHOUT_WILD:
                    l=l+[Hand(HandType.SINGLE,y,[x],1)]
                gotWild=True
        return l
    def getPairs(self)->list:
        l=[]
        wildCount=self.wildCount
        if(wildCount==2):
            for x in RANK_WITHOUT_WILD:
                l=l+[Hand(HandType.PAIR,x,[self.wildCard,self.wildCard],2)]
            wildCount=1
        if(wildCount==1):
            i=0
            while(i<=len(self.nonWildCards)-1):
                if(RANK_NUM[self.nonWildCards[i][1]]>=RANK_NUM['B']):
                    break
                l=l+[Hand(HandType.PAIR,self.nonWildCards[i][1],[self.nonWildCards[i],self.wildCard],1)]
                if(i<=len(self.nonWildCards)-2 and self.nonWildCards[i]==self.nonWildCards[i+1]):
                    i=i+2 #skip the same suits
                    continue
                i=i+1
        i=0
        for i in range(len(self.nonWildCards)):
            for j in range(i+1,len(self.nonWildCards)):
                if self.nonWildCards[i][1] == self.nonWildCards[j][1]:
                    l=l+[HandType.PAIR,self.nonWildCards[i][1],[self.nonWildCards[i],self.nonWildCards[j]],0]
                else:
                    break
        l=[x for x in dict.fromkeys(l)]
        return l
    def getTriples(self)->list:
        l=[]
        wildCount=self.wildCount
        if(wildCount==2):
            i=0
            while(i<=len(self.nonWildCards)-1):
                if(RANK_NUM[self.nonWildCards[i][1]]>=RANK_NUM['B']):
                    break
                l=l+[Hand(HandType.TRIPLE,self.nonWildCards[i][1],[self.nonWildCards[i],self.wildCard,self.wildCard],2)]
                if(i<=len(self.nonWildCards)-2 and self.nonWildCards[i]==self.nonWildCards[i+1]):
                    i=i+2
                    continue
                i=i+1
            wildCount=1
        if(wildCount==1):
            i=0
            for i in range(len(self.nonWildCards)):
                for j in range(i+1,len(self.nonWildCards)):
                    if(RANK_NUM[self.nonWildCards[i][1]]>=RANK_NUM['B']): break
                    if self.nonWildCards[i][1] == self.nonWildCards[j][1]:
                        l=l+[Hand(HandType.TRIPLE,self.nonWildCards[i][1],[self.nonWildCards[i],self.nonWildCards[j],self.wildCard],0)]
                    else:
                        break
            while i < len(self.nonWildCards) - 1:
                if(RANK_NUM[self.nonWildCards[i][1]]>=RANK_NUM['B']): break
                if self.nonWildCards[i][1] == self.nonWildCards[i+1][1]:
                    l=l+[Hand(HandType.TRIPLE,self.nonWildCards[i][1],[self.nonWildCards[i],self.nonWildCards[i+1],self.wildCard],1)]
                i=i+1
        i=0
        while(i<=len(self.nonWildCards)-3):
            if self.nonWildCards[i][1] == self.nonWildCards[i+1][1] == self.nonWildCards[i+2][1]:
                l=l+[Hand(HandType.TRIPLE,self.nonWildCards[i][1],[self.nonWildCards[i+1],self.nonWildCards[i+2],self.wildCard],0)]
            i=i+1
        self.pairs=l
        return l
    def getTripleOfPairs(self)->list:
        l=[]
        #nonWildCards=self.sortHand(self.nonWildCards,byRealPoint=True)
        wildCount=self.wildCount
        pointCards:list[list[str]] = [[] for _ in range(14)]
        for x in self.nonWildCards:
            if(x[1]=='B' or x[1]=='R'):
               continue
            if(x[1]=='A'):
                pointCards[0]=pointCards[0]+[x]
            pointCards[RANK_NUM[x[1]]]=pointCards[RANK_NUM[x[1]]]+[x]
        pointCount=[len(x) for x in pointCards]
        if(wildCount==2):
            for i in range(12):
                if(pointCount[i]>=1 and pointCount[i+1]>=2 and pointCount[i+2]>=1): #A*BBC*
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i],1))]
                    b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2))]
                    c=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+2],1))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],2] for x in product(a,b,c)]
                if(pointCount[i]>=1 and pointCount[i+1]>=1 and pointCount[i+2]>=2): #A*B*CC
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i],1)  )]
                    b=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+1],1))]
                    c=[list(x)                 for x in dict.fromkeys(combinations(pointCards[i+2],2))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],2] for x in product(a,b,c)]
                if(pointCount[i]>=2 and pointCount[i+1]>=1 and pointCount[i+2]>=1): #AAB*C*
                    a=[list(x)                 for x in dict.fromkeys(combinations(pointCards[i],  2))]
                    b=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+1],1))]
                    c=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+2],1))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],2] for x in product(a,b,c)]
                
                if(pointCount[i+1]>=2 and pointCount[i+2]>=2):#**BBCC
                    b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2))]
                    c=[list(x) for x in dict.fromkeys(combinations(pointCards[i+2],2))]
                    l=l+[ [HandType.TRIPLE_OF_PAIR, NUM_RANK[i], x[0]+x[1]+[self.wildCard,self.wildCard] ,2] for x in product(b,c)]
                if(pointCount[i]>=2 and pointCount[i+1]>=2):#AABB**
                    a=[list(x) for x in dict.fromkeys(combinations(pointCards[i],2)) ]
                    b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2)) ]
                    l=l+[ [HandType.TRIPLE_OF_PAIR, NUM_RANK[i], x[0]+x[1]+[self.wildCard,self.wildCard] ,2] for x in product(a,b)]
                if(pointCount[i]>=2 and pointCount[i+2]>=2):#AA**CC
                    a=[list(x) for x in dict.fromkeys(combinations(pointCards[i],2)) ]
                    c=[list(x) for x in dict.fromkeys(combinations(pointCards[i+2],2)) ]
                    l=l+[ [HandType.TRIPLE_OF_PAIR, NUM_RANK[i], x[0]+x[1]+[self.wildCard,self.wildCard] ,2] for x in product(a,c)]
            wildCount=wildCount-1
        if(wildCount==1):
            for i in range(12):
                if(pointCount[i]>=1 and pointCount[i+1]>=2 and pointCount[i+2]>=2): #A*BBCC
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i],1))]
                    b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2))]
                    c=[list(x) for x in dict.fromkeys(combinations(pointCards[i+2],2))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],1] for x in product(a,b,c)]
                if(pointCount[i]>=1 and pointCount[i+1]>=2 and pointCount[i+2]>=2): #AAB*CC
                    a=[list(x) for x in dict.fromkeys(combinations(pointCards[i],2)  )]
                    b=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+1],1))]
                    c=[list(x)                 for x in dict.fromkeys(combinations(pointCards[i+2],2))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],1] for x in product(a,b,c)]
                if(pointCount[i]>=2 and pointCount[i+1]>=2 and pointCount[i+2]>=1): #AABBC*
                    a=[list(x)                 for x in dict.fromkeys(combinations(pointCards[i],  2))]
                    b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2))]
                    c=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(pointCards[i+2],1))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],1] for x in product(a,b,c)]
        for i in range(12):
            if(pointCount[i]>=2 and pointCount[i+1]>=2 and pointCount[i+2]>=2): #A*BBCC
                a=[list(x) for x in dict.fromkeys(combinations(pointCards[i],2))]
                b=[list(x) for x in dict.fromkeys(combinations(pointCards[i+1],2))]
                c=[list(x) for x in dict.fromkeys(combinations(pointCards[i+2],2))]
                l=l+[[HandType.TRIPLE_OF_PAIR,pointCards[i][0][1],x[0]+x[1]+x[2],0] for x in product(a,b,c)]
        return l
    def getPlates(self)->list:
        l=[]
        wildCount=self.wildCount
        if(wildCount==2):
            for i in range(13):
                if(self.pointedCount[i]>=1 and self.pointedCount[i+1]>=3): #A**BBB
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],1))]
                    b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],3))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+[self.wildCard,self.wildCard]+x[1],2] for x in product(a,b)]
                if(self.pointedCount[i]>=3 and self.pointedCount[i+1]>=3): #AAAB**
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],3))]
                    b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],1))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+x[1]+[self.wildCard,self.wildCard],2] for x in product(a,b)]
                if(self.pointedCount[i]>=2 and self.pointedCount[i+1]>=2): #AA**BB
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],2))]
                    b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],2))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+[self.wildCard,self.wildCard]+x[1],2] for x in product(a,b)]
            wildCount=1
        if(wildCount==1):
            for i in range(13):
                if(self.pointedCount[i]>=2 and self.pointedCount[i+1]>=3): #AA*BBB
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],1))]
                    b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],3))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+[self.wildCard]+x[1],1] for x in product(a,b)]
                if(self.pointedCount[i]>=3 and self.pointedCount[i+1]>=2): #AAABB*
                    a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],3))]
                    b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],1))]
                    l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+x[1]+[self.wildCard],1] for x in product(a,b)]
        for i in range(13):
            if(self.pointedCount[i]>=3 and self.pointedCount[i+1]>=3): 
                a=[list(x)+[self.wildCard] for x in dict.fromkeys(combinations(self.pointedCards[i],1))]
                b=[list(x) for x in dict.fromkeys(combinations(self.pointedCards[i+1],3))]
                l=l+[[HandType.TRIPLE_OF_PAIR,self.pointCards[i][0][1],x[0]+x[1],0] for x in product(a,b)]
        return l
    def getFullHouse(self)->list:
        l=[]
        if(self.pairs==None): self.pairs=self.getPairs()
        if(self.triples==None): self.triples=self.getTriples()
        for i in range(self.wildCount+1):
            triples=[x for x in self.triples if x[3]==i]
            #for j in range(self.wildCount-i+1):
            pairs=[x for x in self.pairs if x[3]<=self.wildCount-i ]
            return [[HandType.FULLHOUSE,y[1],y[2].append(x[2],x[3]+y[3])] for x in pairs for y in triples if(x[1]!=y[1])]
        return l
    def getStraightsAndFlushes(self)->list:
        l=[]
        conditions2=[
            [True, True, False, False, False],
            [True, False, True, False, False],
            [True, False, False, True, False],
            [True, False, False, False, True],
            [False, True, True, False, False],
            [False, True, False, True, False],
            [False, True, False, False, True],
            [False, False, True, True, False],
            [False, False, True, False, True],
            [False, False, False, True, True],
        ]
        conditions1=[
            [True, False, False, False, False],
            [False, True, False, False, False],
            [False, False, True, False, False],
            [False, False, False, True, False],
            [False, False, False, False, True],
        ]
        conditions=[
            [False, False, False, False, False]
        ]
        if(self.wildCount==1):  conditions.extend(conditions1)
        if(self.wildCount==2):  conditions.extend(conditions2)
        for i in range(10):
            for mask in conditions:
                legal=True
                for j in range(5): 
                    if(self.pointedCount[i+j]==0 and mask[j]==False):
                        legal=False
                        break
                if(legal==False): continue
                straights:list[str]=[["0"]]
                for k in range(5):
                    if(mask[k]==True):
                        straights=[x[0]+[x[1]] for x in product(straights,[self.wildCard])] 
                    else:
                        straights=[x[0]+[x[1]] for x in product(straights,self.pointedCards[i+k] )]
                for x in straights:
                    x=x[1:]
                    pattern=None
                    flush=True
                    for y in x:
                        if(y==self.wildCard):
                            continue
                        if(pattern!=None and pattern!=y[0]):
                            flush=False
                            break
                        pattern=y[0]
                    l.append([HandType.FLUSH if flush else HandType.STRAIGHT,NUM_RANK[i],x,sum(mask)])
        return l
    def getBomb4(self)->list:
        l=[]
        for i in range(1,14):
            for j in range(self.wildCount+1):
                if(self.pointedCount[i]+j>=4):
                    for x in dict.fromkeys(combinations(self.pointedCards[i],j)):
                        l.append([HandType.BOMB_4,NUM_RANK[i],list(x)+[self.wildCard]*j,j])
        return l
    def getBomb5(self)->list:
        l=[]
        for i in range(1,14):
            for j in range(self.wildCount+1):
                if(self.pointedCount[i]+j>=5):
                    for x in dict.fromkeys(combinations(self.pointedCards[i],j)):
                        l.append([HandType.BOMB_5,NUM_RANK[i],list(x)+[self.wildCard]*j,j])
        return l
    def getBomb6(self)->list:
        l=[]
        for i in range(1,14):
            for j in range(self.wildCount+1):
                if(self.pointedCount[i]+j>=6):
                    for x in dict.fromkeys(combinations(self.pointedCards[i],j)):
                        l.append([HandType.BOMB_6,NUM_RANK[i],list(x)+[self.wildCard]*j,j])
        return l
    def getBomb7(self)->list:
        l=[]
        for i in range(1,14):
            for j in range(self.wildCount+1):
                if(self.pointedCount[i]+j>=7):
                    for x in dict.fromkeys(combinations(self.pointedCards[i],j)):
                        l.append([HandType.BOMB_7,NUM_RANK[i],list(x)+[self.wildCard]*j,j])
        return l
    def getBomb8(self)->list:
        l=[]
        for i in range(1,14):
            for j in range(self.wildCount+1):
                if(self.pointedCount[i]+j>=8):
                    for x in dict.fromkeys(combinations(self.pointedCards[i],j)):
                        l.append([HandType.BOMB_8,NUM_RANK[i],list(x)+[self.wildCard]*j,j])
        return l
    def getBombKing(self)->list:
        if(len(self.handCards)>=4 and self.handCards[-1]==self.handCards[-2]=='HR' and self.handCards[-3]==self.handCards[-4]=='SB'):
            return [HandType.BOMB_KING,'B',['SB','SB','HR','HR'],0]
        return []
    def getAll(self)->list:
        l=[]
        l.extend(self.getSingles())
        l.extend(self.getPairs())
        l.extend(self.getTriples())
        l.extend(self.getTripleOfPairs())
        l.extend(self.getPlates())
        l.extend(self.getFullHouse())
        l.extend(self.getStraightsAndFlushes())
        l.extend(self.getBomb4())
        l.extend(self.getBomb5())
        l.extend(self.getBomb6())
        l.extend(self.getBomb7())
        l.extend(self.getBomb8())
        return l
a=HandGenerator(['SA', 'S2','HR','HR'],'3')
def _getMoves(self,handCards:list[str],previousHand:list,level='2'):
    moves=[['PASS','PASS',['PASS'],0]]
    flushes=[]
    rivalType=previousHand[0]#上家的牌型
    rivalRank=previousHand[1] #上家牌的点数
    hg=HandGenerator(handCards,level)
    if(rivalType==HandType.PASS):
            moves=hg.getAll()
            return moves
    if(rivalType==HandType.STRAIGHT): #特殊处理，先计算出同花顺，得到所有炸弹类牌和普通顺子后在函数末尾返回
        straightsAndFlushes=hg.getStraightsAndFlushes()
        for x in straightsAndFlushes:
            if(x[0]==HandType.FLUSH):
                flushes.append(x)
            elif(RANK_NUM[x[1]]>RANK_NUM[rivalRank]):
                moves.append(x)
    if(rivalType==HandType.BOMB_KING):
        return [['PASS','PASS',['PASS'],0]]
    moves.extend(hg.getBombKing())#更差的牌组可以下放了

    if(rivalType==HandType.BOMB_8):
        moves.extend([x for x in hg.getBomb8() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
        return moves
    moves.extend(hg.getBomb8())

    if(rivalType==HandType.BOMB_7):
        moves.extend([x for x in hg.getBomb7() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
        return moves
    moves.extend(hg.getBomb7())

    if(rivalType==HandType.BOMB_6):
        moves.extend([x for x in hg.getBomb6() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
        return moves
    moves.extend(hg.getBomb6())

    if(rivalType==HandType.FLUSH):  
        moves.extend([x for x in flushes if RANK_NUM[x[1]]>RANK_NUM[rivalRank]])
    moves.extend(flushes)

    if(rivalType==HandType.BOMB_5):  
        moves.extend([x for x in hg.getBomb5() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
        return moves
    moves.extend(hg.getBomb5())

    if(rivalType==HandType.BOMB_4):         
        moves.extend([x for x in hg.getBomb4() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
        return moves
    moves.extend(hg.getBomb4())

    if(rivalType==HandType.SINGLE):         moves.extend([ x for x in hg.getSingles()       if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
    if(rivalType==HandType.PAIR):           moves.extend([ x for x in hg.getPairs()         if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
    if(rivalType==HandType.TRIPLE_OF_PAIR): moves.extend([ x for x in hg.getTripleOfPairs() if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
    if(rivalType==HandType.TRIPLE):         moves.extend([ x for x in hg.getTriples()       if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
    if(rivalType==HandType.PLATE):          moves.extend([ x for x in hg.getPlates()        if RANK_NUM[x[1]]>RANK_NUM[rivalRank]] )
    if(rivalType==HandType.FULLHOUSE):      moves.extend([ x for x in hg.getFullHouse()     if RANK_NUM[x[1]]>RANK_NUM[rivalRank]]   )
    return moves
def getHands(self,handCards:list[str],previousHand:list,level='2'):
    l=_getMoves(handCards,previousHand,level)
    return [self.translateActionToBlackBoxForm(x) for x in l]
for x in (a.getPairs()):
    print(x)
