# My code does not check whether the inputed postfix expression is correct.
# I am assuming that the postfix expression inputted to the do_math function
# is accurate so I don't have to check it. Also I rounded the answer to 2 
# decimal points based on the example output file.

import operator as op

class stack(object):
	def __init__(self):
		self._data = []
	def push(self,e):
		self._data.append(e)
	def pop(self):
		if len(self._data) == 0:
			raise Exception("Stack is Empty")
		return self._data.pop(-1)

# Set basic mathematical operators and assigning variables to them
add = op.add
sub = op.sub
mul = op.mul
div = op.truediv

def do_math(expression):
	values = stack()
	for i in expression.split(): # Convert the string separated by " " into a list
		if check_number(i):
			# If the character is a number, add it to the stack
			values.push(float(i)) # Conver the number to float type
		else:
			# If the character is not a number pop 2 values from the stack
			b = values.pop()
			a = values.pop()
			if i == "+":
				c = add(a,b)
			elif i == "-":
				c = sub(a,b)
			elif i == "*":
				c = mul(a,b)
			elif i == "/":
				c = div(a,b)
			# Push c back into the stack
			values.push(c)
	return values.pop()


def check_number(x):
	# Function that checks whether the string item is a number or not
	try:
		float(x)
		return True
	except ValueError:
		return False

# Read the lines from the input file
inputfile = open("input.txt", "rt")
inputlines = inputfile.readlines()
inputfile.close()
outputfile = open("output.txt", "wt")
for line in inputlines:
	ans = round(do_math(line),2) # Round output to 2 decimal points
	outputfile.write(str(ans)+"\n")
outputfile.close()