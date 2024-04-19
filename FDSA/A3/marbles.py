class MarblesBoard:
	"""create a class to help execute a marbles sorting game"""

	def __init__(self, seq):
		"""Create a new marbles board instance with N slots and marbles

		The class should be initialized with a particular sequence of Marbles, 
		listed in the positiosn from 0 to N-1"""

		self._seq = list(seq) #make sure it's a list instead of a tuple

	def switch(self):
		#Switch the marbles in positions 0 and 1
		self._seq[0], self._seq[1] = self._seq[1], self._seq[0] #Simultaneous Assignment
		return

	def rotate(self):
		"""Move the marble in position 0 to postion N-1, and move all other
		marbles one space to the left (one index lower)"""
		self._seq = self._seq[1:]+self._seq[:1] #takes out the first number and put it at the end
		return

	def is_solved(self):
		#returns true if the marbles are in the correct order.
		prev = self._seq[0] #initialize prev to the first item. There will be a redundant step where you compare the first item with itself
		for cur in self._seq: #loop through the list comparing each item to the previous item
			if cur < prev: #return False if any item is smaller than the previous item
				return False
			prev = cur #update the previous item for iteration
		return True #after the list is exhausted, return True.

	def show(self): # So I can access the board as a list directly from solver.
		return self._seq

	""" You may want to write __str__ and __repr__ methods that display the current
	state of the board """
	def __str__(self): #might not really need this for the purpose but it might be good to be able to print(board)
		return str(self._seq).replace(",","")[1:-1] #makes convert list to a string, take out the commas, and take out the brackets

	def __repr__(self): #return str(self._seq).replace(",","")[1:-1] and we can delete the __str__ method 
		return self.__str__()

class Solver:
	"""write a class that plays the Marbles Game, taking MarblesBoard in its contstructor"""
	def __init__(self, board):
		self._board = board #to use for updating the board
		self._showBoard = tuple(board.show()) #to use to access the board as a tuple

	def solve(self):
		"""write a solve() method that repeatedly calls the switch() and rotate() 
		methods until the game is solved. You should not call switch when one of the 
		two marbles being switched is 0. This assumes we only have 1 of each marble labeled 0 to N-1.
		I think the strategy is to compare the 2 marbles in the front of the board.
		If the either of the marbles is a 0, do a rotate. 
		If the first marble is smaller than the second marble, do a rotate
		If the first marble is bigger than the second marble, do a switch
		The rotation is essentially iterating through the marbles set and comparing each subsequent pair"""
		count = 0 #to keep track of total steps
		print(self._board)
		
		while self._board.is_solved() == False: # before each loop check if the board is solved or not
			if self._showBoard[0] == 0 or self._showBoard[1] == 0: #if either marble is 0, do a rotate
				self._board.rotate()
			elif self._showBoard[0] < self._showBoard[1]: #if the first marble is smalelr than the second, do a rotate
				self._board.rotate()
			elif self._showBoard[0] >= self._showBoard[1]: #if the first marble is bigger than the second, do a switch
				self._board.switch()
			count += 1 #increment counter to keep track of how many steps were taken
			self._showBoard = tuple(board.show()) #update the showBoard tuple to match the new board
			print(self._board) #print the current board.

		return print("total steps: " + str(count)) #reveal how many steps were taken

import sys #get command line input as sys.argv
boardInput = list(map(int,sys.argv[1].split(","))) #convert command line input into a list of integers
board = MarblesBoard(boardInput) #make the board as a MarblesBoard class
player = Solver(board) #put board into the Solver class
player.solve() #solve the board

""" The way I look at the while loop is that, in the worst case scenario, we will have to go through
every adjacent pair in the list to compare them and put them in the correct order relative to each other.
When this is done and the list is rotated through the first pass is complete. 
We will have to do N consecutive passes through the list (in the worst case scenario) to make sure the list
is fully sorted. Therefore, I believe my script is O(n^2)."""