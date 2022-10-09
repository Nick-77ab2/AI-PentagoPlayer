#!/usr/bin/python

#---------------------------------------------------------------------------
# Pentago
# This program is designed to play Pentago, using lookahead and board
# heuristics.  It will allow the user to play a game against the machine, or
# allow the machine to play against itself for purposes of learning to
#  improve its play.  All 'learning'code has been removed from this program.
#
# Pentago is a 2-player game played on a 6x6 grid subdivided into four
# 3x3 subgrids.  The game begins with an empty grid.  On each turn, a player
# places a token in an empty slot on the grid, then rotates one of the
# subgrids either clockwise or counter-clockwise.  Each player attempts to
# be the first to get 5 of their own tokens in a row, either horizontally,
# vertically, or diagonally.
#
# The board is represented by a matrix with extra rows and columns forming a
# boundary to the playing grid.  Squares in the playing grid can be occupied
# by either 'X', 'O', or 'Empty' spaces.  The extra elements are filled with
# 'Out of Bounds' squares, which makes some of the computations simpler.
#
# JL Popyack, ported to Python, May 2019, updated Nov 2021
#   This is a program shell that leaves implementation of miniMax, win,
#   and heuristics (in the Player class) to the student.
#---------------------------------------------------------------------------

import random
import copy
import sys, getopt
import time
import numpy as np

#--------------------------------------------------------------------------------
# Game Setup utilities:
#  Get names of players, player types (human/computer), player to go first, 
#  player tokens (white/black).
#  Allows preconfigured player info to be input from a file
#  Allows game to begin with particular initial state, with Player 1 to 
#  play first.
#--------------------------------------------------------------------------------

def showInstructions():
#---------------------------------------------------------------------------
# Initialize "legend" board with position numbers
#---------------------------------------------------------------------------
	print(
	"""
Two players alternate turns, placing marbles on a 6x6 grid, each
trying to be the first to get 5 of their own colored marbles,
black or white) in a row, either horizontally, vertically, or
diagonally.  After placing a marble on the grid, the player rotates
one of 4 subgrids clockwise (Right) or counter-clockwise (Left).

Moves have the form "b/n gD", where b and n describe the subgrid and
position where the marble will be placed, g specifies the subgrid to
rotate, and D is either L or R, for rotating the subgrid left or right.
Numbering follows the scheme shown below (between 1 and 9), where
subgrids 1 and 2 are on the top, and 3 and 4 are on the bottom:
""")

	pb = PentagoBoard()

	for i in range(pb.BOARD_SIZE):
		for j in range(pb.BOARD_SIZE):
			pb.board[i][j] = (pb.GRID_SIZE*i + j%pb.GRID_SIZE)%pb.GRID_ELEMENTS + 1
	print(pb)

	print( "\nRotating subgrid " + str(1) + " Right:" )
	newBoard = pb.rotateRight(1)
	print(newBoard)

	print( "\nRotating subgrid " + str(3) + " Left:" )
	newBoard = pb.rotateLeft(3)
	print(newBoard)

#----------------------------------------------------------------------------
#  Prompts the user to choose between two options.  
#  Will also allow single-letter lower-case response (unless both are the same)
#----------------------------------------------------------------------------
def twoChoices(question,option1,option2):
	opt1 = option1.lower()
	opt1 = opt1[0]
	opt2 = option2.lower()
	opt2 = opt2[0]
	
	extra = ""
	if opt1 == opt2:
		opt1 = option1
		opt2 = option2
	else:
		extra = "' (" + opt1 + "/" + opt2 + ")"
	
	prompt = question + " (" + option1 + "/" + option2 + "): "
	
	done = False
	while not done:
		response = input(prompt)	
		done = response in [option1, option2, opt1, opt2]
		if not done:
			print("Please answer '" + option1 + "' or '" + option2 + extra)
	
	if (response == option1) or (response == opt1):
		return option1
	else:
		return option2
		

#----------------------------------------------------------------------------
#  Sets up game parameters:
#  Names of players, player types (human/computer), player to go first, 
#  player tokens (white/black).
#
#  Allows preconfigured player info to be input from a file:
#    python3 Pentago_base.py -c testconfig.txt
#
#  Allows game to begin with particular initial state, with Player 1 to 
#  play first.
#    python3 Pentago_base.py -b "w.b.bw.w.b.wb.w..wb....w...bw.bbb.ww"
#----------------------------------------------------------------------------
def gameSetup(timestamp):
	pb = PentagoBoard()
	setupDone = False

	player = [ None for i in range(2) ]
	
	opts, args = getopt.getopt(sys.argv[1:],"b:c:",["board=","config="])
	for opt, arg in opts:
		if opt in ("-b", "--board"):
			initialState = arg
			pb = PentagoBoard(arg)
		elif opt in ("-c", "--config"):
			print("Reading setup from " + arg + ":")
			f = open(arg, "r")
			info = f.read().splitlines()
			f.close() 

			playerName,playerType,playerToken,  \
			  opponentName,opponentType,opponentToken = info

			player[0] = Player(playerName,playerType,playerToken)
			player[1] = Player(opponentName,opponentType,opponentToken)			  
			setupDone = True
		else:
			print("Unknown option, " + opt + " " + arg )
			
	if not setupDone:
		ch = input("Do you want to see instructions (y/n)? ")
		if ch == "y" or ch == "Y":
			showInstructions()
		
		#-----------------------------------------------------------------------
		# Get player information, and save it in file named config_timestamp.txt, 
		# where "timestamp" is a unique timestamp generated at start of game.
		#-----------------------------------------------------------------------
	
		print("Player 1 plays first.")
		playerToken = None
		opponentToken = None
		f = open("config_"+ str(timestamp) + ".txt","w")
		for i in range(2):
			playerName  = input("\nName of Player " + str(i+1) + ": ")
			playerType = twoChoices("human or computer Player?","human","computer")

			if i==0:
				question = "Will " + playerName + " play Black or White?"
				response = twoChoices(question,"Black","White")
				playerToken = response[0].lower()
				opponentToken = "w" if playerToken == "b" else "b"
				
				player[0] = Player(playerName,playerType,playerToken)
				f.write(playerName + "\n" + playerType + "\n" + playerToken + "\n")
				
		player[1] = Player(playerName,playerType,opponentToken)
		f.write(playerName + "\n" + playerType + "\n" + opponentToken + "\n")
		f.close()
		
	return pb, player
		

#-----------------------------------------------------------------------
# names for common abbreviations
#-----------------------------------------------------------------------
descr = {
  "b": "Black",
  "w": "White",
  "h": "human",
  "c": "computer"
}

#USED FOR CHECKING IF THE BOARD WAS ACTUALLY ROTATED IN THE WIN
didRotr=True
#--------------------------------------------------------------------------------

class PentagoBoard:
#--------------------------------------------------------------------------------
# Basic elements of game:
# Board setup constants, rotation of sectors right (clockwise) or 
# left (counter-clockwise),
# apply a move
#--------------------------------------------------------------------------------


	def __init__ (self,board=""):
	#---------------------------------------------------------------------------
	# board can be a string with 36 characters (w, b, or .) corresponding to the
	# rows of a Pentago Board, e.g., "w.b.bw.w.b.wb.w..wb....w...bw.bbb.ww"
	# Otherwise, the board is empty.
	#---------------------------------------------------------------------------
		self.BOARD_SIZE = 6
		self.GRID_SIZE = 3
		self.GRID_ELEMENTS = self.GRID_SIZE * self.GRID_SIZE

		if board=="":
			self.board = [['.' for col in range(self.BOARD_SIZE)] \
			                   for row in range(self.BOARD_SIZE)]
			self.emptyCells = self.BOARD_SIZE**2
			                   
		else:
			self.board = [[board[row*self.BOARD_SIZE + col] \
			  for col in range(self.BOARD_SIZE)] \
			  for row in range(self.BOARD_SIZE)] 
			self.emptyCells = board.count(".")


	def __str__ (self):
		outstr = "+-------+-------+\n"
		for offset in range(0,self.BOARD_SIZE,self.GRID_SIZE):
			for i in range(0+offset,self.GRID_SIZE+offset):
				outstr += "| "
				for j in range(0,self.GRID_SIZE):
					outstr += str(self.board[i][j]) + " "
				outstr += "| "
				for j in range(self.GRID_SIZE,self.BOARD_SIZE):
					outstr += str(self.board[i][j]) + " "
				outstr += "|\n"
			outstr += "+-------+-------+\n"
		
		return outstr


	def toString(self):
		return "".join(item for row in self.board for item in row) 


	def getMoves(self):
	#---------------------------------------------------------------------------
	# Determines all legal moves for player with current board,
	# and returns them in moveList.
	#---------------------------------------------------------------------------
		moveList = [ ]
		for i in range(self.BOARD_SIZE):
			for j in range(self.BOARD_SIZE):
				if self.board[i][j] == ".":
				#---------------------------------------------------------------
				#  For each empty cell on the grid, determine its block (1..4)
				#  and position (1..9)  (1..GRID_SIZE^2)
				#---------------------------------------------------------------
					gameBlock = (i // self.GRID_SIZE)*2 + (j // self.GRID_SIZE) + 1
					position  = (i%self.GRID_SIZE)*self.GRID_SIZE + (j%self.GRID_SIZE) + 1
					pos = str(gameBlock) + "/" + str(position) + " "
				#---------------------------------------------------------------
				#  For each block, can place a token in the given cell and
				#  rotate the block either left or right.
				#---------------------------------------------------------------
					numBlocks = (self.BOARD_SIZE // self.GRID_SIZE)**2  # =4 
					for k in range(numBlocks):  
						block = str(k+1)
						moveList.append(pos+block+"L")
						moveList.append(pos+block+"R")

		return moveList

	def rotateLeft(self,gameBlock):
	#---------------------------------------------------------------------------
	# Rotate gameBlock counter-clockwise.  gameBlock is in [1..4].
	#---------------------------------------------------------------------------
		rotLeft = copy.deepcopy(self)

		rowOffset = ((gameBlock-1)//2)*self.GRID_SIZE
		colOffset = ((gameBlock-1)%2)*self.GRID_SIZE
		for i in range(0+rowOffset,self.GRID_SIZE+rowOffset):
			for j in range(0+colOffset,self.GRID_SIZE+colOffset):
				rotLeft.board[2-j+rowOffset+colOffset][i-rowOffset+colOffset] = self.board[i][j]

		return rotLeft


	def rotateRight(self,gameBlock):
	#---------------------------------------------------------------------------
	# Rotate gameBlock clockwise.  gameBlock is in [1..4].
	#---------------------------------------------------------------------------
		rotRight = copy.deepcopy(self)

		rowOffset = ((gameBlock-1)//2)*self.GRID_SIZE
		colOffset = ((gameBlock-1)%2)*self.GRID_SIZE
		for i in range(0+rowOffset,self.GRID_SIZE+rowOffset):
			for j in range(0+colOffset,self.GRID_SIZE+colOffset):
				rotRight.board[j+rowOffset-colOffset][2-i+rowOffset+colOffset] = self.board[i][j]

		return rotRight


	def applyMove(self, move, token, player=None):
	#---------------------------------------------------------------------------
	# Perform the given move, and update board.
	#---------------------------------------------------------------------------
		global didRotr
		gameBlock = int(move[0])  # 1,2,3,4
		position = int(move[2])   # 1,2,3,4,5,6,7,8,9
		rotBlock = int(move[4])   # 1,2,3,4
		direction = move[5]       # L,R

		i = (position-1)//self.GRID_SIZE + self.GRID_SIZE*((gameBlock-1)//2) ;
		j = ((position-1)%self.GRID_SIZE) + self.GRID_SIZE*((gameBlock-1)%2) ;

		newBoard = copy.deepcopy(self)
		newBoard.board[i][j] = token
		checkWin=True
		if player.token==token:
			checkWin=player.win(newBoard)
		else:
			checkWin=player.loss(newBoard)
		if( direction=='r' or direction=='R') and not(checkWin):
			didRotr=True
			newBoard = newBoard.rotateRight(rotBlock)
		elif (direction=='l' or direction=='L') and not(checkWin):
			didRotr=True
			newBoard = newBoard.rotateLeft(rotBlock)
		elif checkWin:
			didRotr=False
		return newBoard



#--------------------------------------------------------------------------------

class Player:
#--------------------------------------------------------------------------------
# Contains elements for players of human and computer types:
# Student needs to provide code for three methods: win, userid_h, and miniMax
#--------------------------------------------------------------------------------

	def __init__ (self,name,playerType,token):
		self.INFINITY = 10000

		self.name = name
		
		if playerType.lower() in ["human","computer"]:
			self.playerType = playerType.lower()    
		elif playerType == "h":
			self.playerType = "human"
		elif playerType == "c":
			self.playerType = "computer"
		else:
			print(playerType + " is not a valid player type.  Assuming " + name + 
			 " is human type.")
			 
		if token.lower() in ["b","w"]:
			self.token = token.lower()
			 
	def __str__ (self):
		return "Player " + self.name + ": type=" + self.playerType +  \
		       ", plays " + descr[self.token] + " tokens"


	def gethumanMove(self, board):
	#---------------------------------------------------------------------------
	# If the opponent is a human, the user is prompted to input a legal move.
	# Determine the set of all legal moves, then check input move against it.
	#---------------------------------------------------------------------------

	#---------------------------------------------------------------------------
	# In Pentago, available moves are the same for either player:
	#---------------------------------------------------------------------------
		moveList = board.getMoves()
		move = None

		ValidMove = False
		while(not ValidMove):
			hMove = input('Input your move (block/position block-to-rotate direction): ')

			for move in moveList:
				if move == hMove:
					ValidMove = True
					break

			if(not ValidMove):
				print('Invalid move.  ')

		return hMove

#I have a findWinner() function that returns who wins, including ties
#and then a win() function that just checks if findWinner() returns if the winner is self.token
#and the same for loss() which checks if winner is something other than self.token, but not a tie or null 
#You can probably change your current win() to be findWinner()
	def findWinner(self,board):
	#---------------------------------------------------------------------------
	# Determines if player has won, by finding '5 in a row'.
	# Student code needed here.
	#---------------------------------------------------------------------------
		theBoard=board.board
		opponentToken=''
		playerWin=0
		opponentWin=0
		if self.token=='w':
			opponentToken='b'
		else:
			opponentToken='w'

		#C is faster than python, therefore I'm only running numpy operations
		newBoard=np.array(theBoard)
		diag1=newBoard.diagonal(0)
		diag2=newBoard.diagonal(1)
		diag3=newBoard.diagonal(-1)
		diag4=np.fliplr(newBoard).diagonal(0)
		diag5=np.fliplr(newBoard).diagonal(1)
		diag6=np.fliplr(newBoard).diagonal(-1)
		for i in range(len(newBoard)):
			if (newBoard[i][0:5] == self.token).sum() == 5 or (newBoard[i][1:6] == self.token).sum() == 5:
				playerWin+=1
			elif (newBoard[i][0:5] == opponentToken).sum() == 5 or (newBoard[i][1:6] == opponentToken).sum() == 5:
				opponentWin+=1
			if (newBoard[:,i][0:5] == self.token).sum() == 5 or (newBoard[:,i][1:6] == self.token).sum() == 5:
				playerWin+=1
			elif (newBoard[:,i][0:5] == opponentToken).sum() == 5 or (newBoard[:,i][1:6] == opponentToken).sum() == 5:
				opponentWin+=1
		
		if (diag1[0:5] == self.token).sum() == 5 or (diag1[1:6] == self.token).sum() == 5:
			playerWin+=1
		elif (diag1[0:5] == opponentToken).sum() == 5 or (diag1[1:6] == opponentToken).sum() == 5:
			opponentWin+=1
		if (diag4[0:5] == self.token).sum() == 5 or (diag4[1:6] == self.token).sum() == 5:
			playerWin+=1
		elif (diag4[0:5] == opponentToken).sum() == 5 or (diag4[1:6] == opponentToken).sum() == 5:
			opponentWin+=1
		checker=[diag2,diag3,diag5,diag6]
		for i in checker:
			if (i==self.token).sum() == 5:
				playerWin+=1
			elif (i== opponentToken).sum() == 5:
				opponentWin+=1

		if playerWin>0 and opponentWin==0:
			return self.token
		elif playerWin==0 and opponentWin>0:
			return opponentToken
		elif playerWin>0 and opponentWin>0:
			return "tie"
		else:
			return None

	def win(self,board):
		result=self.findWinner(board)
		if result==self.token:
			return True
		return False

	def loss(self,board):
		result=self.findWinner(board)
		if result!=self.token and result!="tie" and result!=None:
			return True
		return False

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
#------------------------------------------------------------------------------------------------------------------------
#THE BELOW COMMENT IS MY PREVIOUS CODE COMMENTED OUT, YES I KNOW IT'S A STRING WITH NO PARENT, IT DOES NOTHING
#I LEFT IT HERE FOR READING CONVENIENCE OF THE COMMENTS PREVIOUSLY PLACED HERE
#------------------------------------------------------------------------------------------------------------------------
	"""
	def miniMax(self, board, opponent, min, depth, maxDepth):
	#---------------------------------------------------------------------------
	# Use MiniMax algorithm to determine best move for player to make for given
	# board.  Return the chosen move and the value of applying the heuristic to
	# the board.
	# To examine each of player's moves and evaluate them with no lookahead,
	# maxDepth should be set to 1.  To examine each of the opponent's moves,
	#  set maxDepth=2, etc.
	# Increase depth by 1 on each recursive call to miniMax.
	# min is the minimum value seen thus far by
	#
	# If a win is detected, the value returned should be INFINITY-depth.
	# This rates 'one move wins' higher than 'two move wins,' etc.  This ensures
	# that Player moves toward a win, rather than simply toward the assurance of
	# a win.
	#
	# Student code needed here.
	# Alpha-Beta pruning is recommended for Extra Credit.
	# Argument list for this function may be altered as needed.
	#
	# successive calls to MiniMax should swap the self and opponent arguments.
	#---------------------------------------------------------------------------

	#---------------------------------------------------------------------------
	# This code just picks a random move, and needs to be replaced.
	#---------------------------------------------------------------------------
		moveList = board.getMoves()  # find all legal moves
		token1=''
		token2=''
		count=0
		depth+=1
		#Set the tokens at the given depth.
		if depth%2==1:
			token1=self.token
			token2=opponent
		else:
			token2=self.token
			token1=opponent

		max = -(self.INFINITY+1)
		for m in moveList:
			print(m)
			maxBoard=board.applyMove(m,token1,self)
			min=self.nwp28_h(maxBoard)

			if self.win(maxBoard):
				return m, self.INFINITY-depth

			min = (self.INFINITY+1)

			if maxDepth==2:
				for n in maxBoard.getMoves():
					minBoard= maxBoard.applyMove(n,token2,self)
					tempVal=self.nwp28_h(minBoard)
					if tempVal < min:
						min = tempVal
					#pruning
					if min<max:
						break

			if maxDepth>2:
				for n in maxBoard.getMoves():
					minBoard= maxBoard.applyMove(n,token2,self)
					if self.loss(minBoard): #WRITE LOSS HERE
						return n, -(self.INFINITY-depth)
					if depth==maxDepth:
						return n, self.nwp28_h(minBoard)
					tempVal=self.miniMax(minBoard, opponent, min, depth, maxDepth)[1]
					if tempVal<min:
						min=tempVal

					#pruning, which is supposed to help a lot, but doesn't seem to?
					if min<max:
						break

			if maxDepth>1:
				if min>max:
					max=min
					move=m
			else:
				if val>max:
					max=val
					move=m
		return move, max
	"""
	def testNegamax(self, board, opponent, depth, maxDepth, a, b, move, color):
		if color==1:
			token1=self.token
		else:
			token1=opponent
		moveSet=board.getMoves()
		if depth == maxDepth or self.win(board) or self.loss(board):
			return move, color*self.nwp28_h(board)
		theMax=-(self.INFINITY+1)
		for m in moveSet:
			newMove=board.applyMove(m,token1,self)
			tempVal=-(self.testNegamax(newMove, opponent, depth + 1, maxDepth, -b, -a, m, -color)[1])
			if tempVal>theMax:
				theMax=tempVal
				move=m
			a = max(a, theMax)
			if a>=b:
				break
		return move, theMax

	def getHumanMove(self, board):
	#---------------------------------------------------------------------------
	# If the opponent is a human, the user is prompted to input a legal move.
	# Determine the set of all legal moves, then check input move against it.
	#---------------------------------------------------------------------------
		moveList = board.getMoves()
		move = None

		ValidMove = False
		while(not ValidMove):
			hMove = input("Input your move, " + self.name + \
			              " (block/position block-to-rotate direction): ")

			if hMove == "exit":
				return "exit" 
				
			for move in moveList:
				if move == hMove:
					ValidMove = True
					break

			if(not ValidMove):
				print("Invalid move.  ")

		return hMove


	def getComputerMove(self, board):
	#---------------------------------------------------------------------------
	# If the opponent is a computer, use artificial intelligence to select
	# the best move.
	# For this demo, a move is chosen at random from the list of legal moves.
	#---------------------------------------------------------------------------
		opponent = "w" if self.token=="b" else "b"
		#negamax(board, opponent, depth, maxDepth, alpha, Beta, move, player)
		move, value = self.testNegamax(board, opponent,0, 2, -self.INFINITY, self.INFINITY, None ,1)
		return move


	def playerMove(self, board):
	#---------------------------------------------------------------------------
	# Depending on the player type, return either a human move or computer move.
	#---------------------------------------------------------------------------
		if self.playerType=="human":
			return self.getHumanMove(board)
		else:
			return self.getComputerMove(board)



def explainMove(move, player):
#---------------------------------------------------------------------------
# Explain actions performed by move
#---------------------------------------------------------------------------

	gameBlock = int(move[0])  # 1,2,3,4
	position = int(move[2])   # 1,2,3,4,5,6,7,8,9
	rotBlock = int(move[4])   # 1,2,3,4
	direction = move[5]       # L,R

	G = PentagoBoard().GRID_SIZE
	i = (position-1)//G + G*((gameBlock-1)//2) ;
	j = ((position-1)%G) + G*((gameBlock-1)%2) ;
	if didRotr==True:
		print("Placing " + player.token + " in cell [" + str(i) + "][" + str(j) +  \
		  	"], and rotating Block " + str(rotBlock) +  \
		  	(" Left" if direction=="L" else " Right"))
	else:
		 print("Placing " + player.token + " in cell [" + str(i) + "][" + str(j) +  \
		  	"]")



#--------------------------------------------------------------------------------
#  MAIN PROGRAM
#--------------------------------------------------------------------------------

if __name__ == "__main__":
#--------------------------------------------------------------------------------
#  To run program: 
#    python3 Pentago_base.py 
#  This will lead the user through a dialog to name the players, who plays which
#  color, who goes first, whether each player is human, computer.  
#  A configuration file containing this information is created, with a unique 
#  name containing a timestamp.
#  
#  To skip the interactive dialog and use the preconfigured player info 
#  (file has been renamed to testconfig.txt):
#    python3 Pentago_base.py -c testconfig.txt
#
#  To begin the game at a particular initial state expressed as a 36-character 
#  string linsting the board elements in row-major order (Player 1 to play first):
#    python3 Pentago_base.py -b "w.b.bw.w.b.wb.w..wb....w...bw.bbb.ww"
#  This is useful for mid-game testing.
#
#  A transcript of the game is produced with name beginning "transcript_" and
#  ending with a timestamp value.  The file contains player info, followed by
#  lines containing each state as a 36-character string, followed by the move made.
#--------------------------------------------------------------------------------

	timestamp = time.time()
	print( "\n-------------------\nWelcome to Pentago!\n-------------------" )
	
	pb, player = gameSetup(timestamp)
	print("\n" + str(player[0]) + "\n" + str(player[1]) + "\n")

	#-----------------------------------------------------------------------
	# Play game, alternating turns until a win encountered, board is full
	# with no winner, or human user types "exit".
	#-----------------------------------------------------------------------
	f = open("transcript_"+ str(timestamp) + ".txt","w")
	f.write("\n" + str(player[0]) + "\n" + str(player[1]) + "\n")
	gameOver = False
	currentPlayer = 0
	print(pb)
	numEmpty = pb.emptyCells
	startTime=time.time()
	while( not gameOver ):
		move = player[currentPlayer].playerMove(pb)
		if move == "exit":
			break
		if didRotr==True:	
			print(player[currentPlayer].name + "'s move: " + move)
		else:
			theMove=str(move)
			size=len(theMove)
			newMove=theMove[:size - 6]
			print(player[currentPlayer].name + "'s move: " + newMove)
		f.write(pb.toString() + "\t" + move + "\n")
		
		newBoard = copy.deepcopy(pb)
		newBoard = newBoard.applyMove(move,player[currentPlayer].token,player[currentPlayer])
		
		explainMove(move,player[currentPlayer]) 

		print(newBoard)
		numEmpty = numEmpty - 1
		win0=False
		win1=False
		tie=False

		if player[0].findWinner(newBoard)==player[0].token:
			win0=True
		elif player[0].findWinner(newBoard)=="tie":
			win0=True
		else:
			win0=False
		if player[1].findWinner(newBoard)==player[1].token:
			win1=True
		elif player[1].findWinner(newBoard)=="tie":
			win1=True
		else:
			win1=False
		gameOver = win0 or win1 or numEmpty==0

		currentPlayer = 1 - currentPlayer
		pb = copy.deepcopy(newBoard)
	print("Runtime: %s seconds "%(time.time()-startTime))
	#-----------------------------------------------------------------------
	# Game is over, determine winner.
	#-----------------------------------------------------------------------
	if not gameOver:  # Human player requested "exit"
		print("Exiting game.")
	elif (win0 and win1):
		print("Game ends in a tie (multiple winners).")
	elif win0:
		print(player[0].name + " (" + descr[ player[0].token ] + ") wins")
	elif win1:
		print(player[1].name + " (" + descr[ player[1].token ] + ") wins")
	elif numEmpty==0:
		print("Game ends in a tie (no winner).")

	f.write(pb.toString() + "\t\n")
	f.close()

