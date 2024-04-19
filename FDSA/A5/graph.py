######################## Classes ############################

# Create object for linked graph
class Node():
	""" Node object to represent each of the nodes """
	def __init__(self, name, value = None):
		self.value = value
		self.name = name
		self.connections = []

	def add_con(self, other):
		if other not in self.connections:
			self.connections.append(other)
		# based on the abj.txt file, it looks like the graph edges are 2 directional
		if self not in other.connections:
			other.connections.append(self)

	def get_con(self):
		return self.connections

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()

class Queue():
	""" Queue object, first in first out"""
	def __init__(self):
		self.items = []

	def enqueue(self, item):
		self.items.insert(0,item)

	def dequeue(self):
		return self.items.pop()

	def isEmpty(self):
		return self.items == []

######################## Functions ############################

def shortestpath(node):
# Breadth first search from node
	Q = Queue()
	Q.enqueue(node)
	visited_nodes = set() # Keep track of visited nodes
	distances = {} # dict to store output
	distances[node.name] = 0
	while not Q.isEmpty():
		v = Q.dequeue()
		for child in v.get_con():
			if child not in visited_nodes and child.name not in distances.keys():
			# if this is a new node, and distance not already stored,
			# use the distance of the parent + 1.
				distances[child.name] = distances[v.name] + 1
				Q.enqueue(child)
		visited_nodes.add(v) # record node as visited
	return distances


# Method that accepts 2 nodes as arguments, n1 and n2, and returns the number of
# nodes that are equidistant from n1 and n2.
def equidistant(n1, n2):
	dict1 = shortestpath(n1)
	dict2 = shortestpath(n2)
	count = 0

	for key in dict1.keys():
		if dict1[key] == dict2[key]:
			count += 1
	return count


######################## Main ############################

# Accept adjacency matrix as input and construct node-based representation of a graph
adj_matrix = open("adj.txt", "rt")
rows = adj_matrix.readlines()
adj_matrix.close()
# Instead of assigning a variable to each node, I will put the nodes in a list
nodes = []
# First creat all the nodes required
for i in range(len(rows)):
	nodes.append(Node("v"+str(i)))
# Add the connections for each node
for i in range(len(rows)):
	items = rows[i].split()
	for j in range(len(items)):
		if items[j] == "1":
			nodes[i].add_con(nodes[j])

# Import the input.txt file to read inputs
input_file = open("input.txt", "rt")
inputs = input_file.readlines()
input_file.close()
output_file = open("output.txt", "wt")
for i in inputs:
	#nodes are stored in a list as nodes[0] = the node named 0
	n1 = nodes[int(i.split()[0])]
	n2 = nodes[int(i.split()[1])]
	answer = equidistant(n1,n2)
	output_file.write(str(answer)+"\n")
output_file.close()

