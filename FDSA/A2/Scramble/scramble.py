def interleave(A, B):  #Interleave Function to get a1b1a2b2a3b4...
	ab = "" #instatiate output string of a interleave b
	if len(A) == len(B): #check condition where A and B are strings of the same length
		for i in range(len(A)): #for loop to interleave A and B from 0 to len(A)-1
			ab += A[i]+B[i] #add A[i]B[i] to the end of the output string
		return ab
	else: #if A and B are not the same length, return an error message
		return "A and B are not the same length"
def checkpower2(a): #takes string "a" to see if it's length is a power of 2, if not, add "." until it is
	b = len(a) #use b as a varaible to hold the length of the string
	while b > 1: #we only check power if len(a) > 1
		if b%2 != 0:
			return False #this means b is an odd number and therefore cannot be power of 2
		b /= 2 #keep dividing by 2 until you get an odd number or 1, if you get 1 you leave the while loop
	return True #if you can break out of the while loop, it means len(a) is a power of 2
def scramble(a): #the recursive fucntion scramble will output the scramble of string "a"
	if len(a) == 1: #the scramble of a single character is just that character
		return a
	else: 
		if checkpower2(a) == False: #make sure the string has length of power 2
			a += "." #add a "." at the end if not power 2
			return scramble(a) #run the new string through scramble
		else: # the string has len power 2
			return interleave(scramble(a[:len(a)//2]), scramble(a[len(a)//2:])) #interleave first half of message with second half of message
#The following code is for grading purposes. Read input.txt file and write output.txt file
fp = open("input.txt") #open up input.txt file with read only
op = open("output.txt","w") #open up output.txt file with write only
lines = fp.readlines() #Return all lines as a list of strings
for i in range(len(lines)): #iterate the list of strings to perform the scramble on each line separately
	curline = lines[i] #pull the current line we want to encode
	newcurline = lines[i].replace("\n","") #get rid of the \n so it is not included in the scrambling
	op.write(scramble(newcurline)+"\n") #scramble the desired line and the insert a \n at the end
op.close()