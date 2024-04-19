def is_hot(N): #Recursive function that reads the state of the game (N) and returns whether the state is hot or cold
	if N < 2:
		return False #If the N<2, that means the state is cold. This is the base case.
	else:
		return not(is_hot(N-1) and is_hot(N/2)) #the state is only cold if both N-1 and N/2 is hot. In other words, hot is true if not((N-1)and(N/2))
fp = open("input.txt") #open the input file as read only
op = open("output.txt","w") #open the ouput file as write only
lines = fp.readlines() #stores each line of the input as a list
for i in range(len(lines)):
	if is_hot(int(lines[i])) == True:
		op.write("hot\n")
	else:
		op.write("cold\n")
op.close()