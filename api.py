from enum import Enum
from functools import cmp_to_key
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
RANK_NUM={'R': 17, 'B': 16, 'L': 15, 'A': 13, 'K': 12, 'Q': 11, 'J': 10, 'T': 9, 
           '9': 8, '8': 7, '7': 6, '6': 5, '5': 4, '4': 3, '3': 2, '2': 1,'1':0}

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

def sortHand(a,level="2",RealPoint=False):
    """
    接受和返回的有序牌组。级牌（含红心）均为实际点数，没有特殊表示。levelMask=True时，将按照实际点数排序。
    """
    if(RealPoint==False):
        a=[x[0]+'L' if x[1]==level else x for x in a]
        a=sorted(a,key=cmp_to_key(compareSingle))
        a=[x[0]+level if x[1]=="L" else x for x in a]
    else:
        a=[x[0]+'1' if x[1]=='A' else x for x in a]
        a=sorted(a,key=cmp_to_key(compareSingle))
        #a=[x[0]+"A" if x[1]=="1" else x for x in a]
    
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

#legal: player_hand_card and rival_move:can be NULL ->legal_action
def getHandType(a:list[str],level="2")->str:#H5 etc
    """
    升序排列的牌组，级牌不特殊表示
    SB HR
    """
    a=sortHand(a)
    cardCount=len(a)
    wildCard="H"+level
    wildCount=0
    for x in a:
        if(x==wildCard):
            wildCard=wildCard+1
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
        realPointHands=sortHand(a,level,True)
        #duplicate in former 4 cards or joker
        if(RANK_NUM[points[4]]>=RANK_NUM['B'] or points[0]==points[1] or points[1]==points[2] or points[2]==points[3]): return HandType.INVALID
        if(wildCount==0):
            if(RANK_NUM[realPointHands[4][1]] - RANK_NUM[realPointHands[0][1]]!=4 or RANK_NUM[points[4]]-RANK_NUM[points[0]]!=4): return HandType.INVALID
            if(a[0][0]==a[1][0]==a[2][0]==a[3][0]==a[4][0]): flush=True
        if(wildCount==1):
            realPointHands=sortHand(a[:-1],level,True)#A???\*
            if(realPointHands[0]=='1'): #special treat
                if(realPointHands[1]=='1'): return HandType.INVALID
                gap=RANK_NUM[realPointHands[2][1]]-RANK_NUM[realPointHands[1][1]]-1+RANK_NUM[realPointHands[3][1]]-RANK_NUM[realPointHands[2][1]]-1
                if(gap>1):return HandType.INVALID
                if(RANK_NUM['3']<RANK_NUM[realPointHands[1][1]]<RANK_NUM['10']): return HandType.INVALID 
            if( RANK_NUM[realPointHands[3][1]]-RANK_NUM[realPointHands[0][1]]>4): return HandType.INVALID
            if(a[0][0]==a[1][0]==a[2][0]==a[3][0]): flush=True
        if(wildCard==2):
            realPointHands=sortHand(a[:-2],level,True)
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
        realPointHands=sortHand(a[:wildCount],level,True)
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