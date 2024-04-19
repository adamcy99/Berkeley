#Part 1, write a scrip to compute how many unique prime facts an integer has.
#For example, 12 = 2x2x3, so has 2 unique prime factors, 2 and 3.
#Use your scrip to comput the number of unique prime factors of 1234567890

def prime_factors(number):
	n = [] # number of prime factors
	half = int(number)//2
	for i in range(2,half+1): #first find all the factors other than 1
		if number%i == 0:
			if i == 2:		#if the factor is 2, we know it's prime
				n.append(i)
			else:
				prime = True
				for j in range(2,i):    #now decide whether this factor is prime or not
					if i%j == 0:
						prime = False   	#not a prime
				if prime == True:
					n.append(i)		#goes through and doesn't break, means it is a prime, add to set
	return n

def prime_factors2(number):
	n = []
	i = 1
	while(i <= number):
		k = 0
		if(number%i == 0):
			j = 1
			while(j <= i):
				if(i%j == 0):
					k += 1
				j += 1
			if(k == 2):
				n.append(i)
		i += 1
	return n

#Part 2. Write a script that prompts the user for their phone number, x.
#Compute x minus the sum of the digits of x. Call this result y.
#hint: to find the sum of the digits of x, check to see what x//10 and x%10 would give you
#Compute the sum of the digits of y, and store the result back in y.
#Repeat until y has just one digit, then display it.

def phone_number():
	x = input("What is your phone number? ")
	xprime = int(x)
	sumx = 0
	for i in range(10):
		sumx += xprime%10
		xprime //= 10
	y = int(x) - sumx
	while y >= 10:
		yprime = int(y)
		sumy = 0
		for j in range(len(str(y))):
			sumy += yprime%10
			yprime //= 10
		y = sumy
	return y