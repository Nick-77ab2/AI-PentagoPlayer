from time import thread_time_ns
import Pentago
import numpy as np

class Player(Pentago.Player):
	
	def nwp28_h(self,board):
		#First moves: place middle: +10 place outside middle: +20 place corner +5
		#Calculate sets of adjacents not relating to middle, for player +30
		#Calculate number of sets of 3 for player. +50
		#If there are two sets of adjacents, check if they're on diagonal boards. +100
			#If there are two adjacents on diagonal boards, check if there's a piece on a board2 next to them in a corner. +1000
		theBoard=board.board
		board2=[]
		theBoard=np.array(theBoard)
		blocks=np.hsplit(theBoard,2)
		for i in blocks:
			slice = np.vsplit(i,2)
			for j in slice:
				board2.append(j.flatten())
		board2 = np.array(board2)

		score=0
		diagonals=[[],[],[],[]]
		adjacents=0
		for block in range(len(board2)):
			for piece in range(len(board2[block])):
				if board2[block][piece]==self.token:
					if piece==1 or piece==3 or piece==5 or piece==7:
						score+=20
						diagonals[block].append(piece)
					elif piece==4:
						score+=10
					else:
						score+=5
			
			def calculateAdjacentScore():
				nonlocal score,adjacents
				#increase score for each adjacent pair.
				if board2[block][1]==self.token:
					if board2[block][3]==self.token:
						score+=30
						adjacents+=1
					if board2[block][5]==self.token:
						score+=30
						adjacents+=1
				if board2[block][3]==self.token:
					if board2[block][7]==self.token:
						score+=30
						adjacents+=1
				if board2[block][5]==self.token:
					if board2[block][7]==self.token:
						score+=30
						adjacents+=1
			calculateAdjacentScore()
			
			def calculateThreeSet():
				nonlocal score
				#Check Diagonal 3 sets
				if block==0 or block==3:
					if board2[block][0]==self.token and board2[block][4]==self.token and board2[block][8]==self.token:
						score+=50
				if block==1 or block==2:
					if board2[block][2]==self.token and board2[block][4]==self.token and board2[block][6]==self.token:
						score+=50
				#Check regular sets of 3: Horizontal and Vertical
				if board2[block][0]==self.token and board2[block][1]==self.token and  board2[block][2]==self.token:
					score+=50
				if board2[block][0]==self.token and board2[block][3]==self.token and  board2[block][6]==self.token:
					score+=50
				if board2[block][1]==self.token and board2[block][4]==self.token and  board2[block][7]==self.token:
					score+=50
				if board2[block][2]==self.token and board2[block][5]==self.token and  board2[block][8]==self.token:
					score+=50
				if board2[block][3]==self.token and board2[block][4]==self.token and  board2[block][5]==self.token:
					score+=50
				if board2[block][6]==self.token and board2[block][7]==self.token and  board2[block][8]==self.token:
					score+=50
			calculateThreeSet()
		def checkSetAdjacents():
			nonlocal score,adjacents
			#If there are 2 or more adjacents
			if adjacents>=2:
				#Then determine where they are using a true false return from poking the location in the 2d diagonals array.
				if diagonals[0] and diagonals[3]:
					score+=100
					if board2[1][0]==self.token or board2[1][2]==self.token or board2[1][6]==self.token or board2[1][8]==self.token:
						score+=1000
					if board2[2][0]==self.token or board2[2][2]==self.token or board2[2][6]==self.token or board2[2][8]==self.token:
						score+=1000
				if diagonals[1] and diagonals[2]:
					score+=100
					if board2[0][0]==self.token or board2[0][2]==self.token or board2[0][6]==self.token or board2[0][8]==self.token:
						score+=1000
					if board2[3][0]==self.token or board2[3][2]==self.token or board2[3][6]==self.token or board2[3][8]==self.token:
						score+=1000
		checkSetAdjacents()
		return score


def testNegamax(self,board, opponent, depth, a, b, move, color):
	if color==1:
		token1=self.token
		token2=opponent
	else:
		token2=self.token
		token1=opponent
	moveSet=board.getMoves()
	if depth == 0 or self.win(board) or self.loss(board):
		return move, color*self.nwp28_h(board)
	val=-(self.INFINITY-1)
	for m in moveSet:
		newMove=board.applyMove(m,token1,self)
		tempVal=-testNegamax(newMove, opponent, depth - 1, -b, -a, m, -color)
		val = max(val, tempVal[1])
		if val==tempVal[1]:
			move=tempVal[0]
		a = max(a, val)
		if a>b:
			break
	return move, val
