from collections import namedtuple
import csv
import re
import json
import math
import collections

class DataRow:
	def __init__(self,attribs):
		self.attribs = attribs
		self.tuple = namedtuple('Row',attribs)
	def parse(self,row):
		values = []
		for val in zip(self.attribs,row.split(',')):
			values.append(val[1])
		return self.tuple(*values)
		
class Tree:
	def __init__(self,attribs,examples,isLeaf):
		self.attribs = attribs
		self.examples = examples
		self.isLeaf = isLeaf

def load():
	with open('testData.arff') as f:
		wholetxt = f.read()
		datasplit = wholetxt.split('@DATA')
		attribvals = re.findall(r'\{(.+?)\}',datasplit[0])
		treevals = []
		for values in attribvals:
			finalvals = values.split(',')
			treevals.append(finalvals)
		attribs = re.findall(r"'(\w+)'",datasplit[0])

		csvdata = datasplit[1].splitlines()
		csvdata.pop(0)
		datalist =[]
		for row in csvdata:
			tuple = DataRow(attribs)
			typed_row = tuple.parse(row)
			datalist.append(typed_row)
		diction = dict(zip(attribs,treevals))
		tree = Tree(diction,datalist,0)	
		return tree

def highestCount(tree):
	count = 0
	for ex in tree.examples:
		if(ex.Wait == '"Yes"'):
			count += 1
		else:
			count -= 1
	if(count>0):
		return "Wait: Yes"
	else:
		return "Wait: No"
def findBestAttr(passedtree):
	tree = passedtree
	highestgain = 0
	bestAttr =0
	numbattr = len(tree.attribs)-1

	for attrib in range(numbattr):
		gainval = 1- gain(tree, tree.attribs.keys()[attrib])
		if gainval >= highestgain:
			bestAttr = tree.attribs.keys()[attrib]
			highestgain = gainval
	return bestAttr

def gain(passedtree,testattrib):
		tree = passedtree
		attrib = testattrib
		totalgain = float(0)
		for val in tree.attribs[attrib]:
			newdata = []
			positive = 0
			negative = 0
			qval = 0
			gain = 0
			for ex in tree.examples:
				if(getattr(ex,attrib)== val):
					newdata.append(ex)
					if(getattr(ex,"Wait") == '"Yes"'):
						positive= positive+1
					else:
						negative= negative+1
			if(negative+positive > 0):
				qval = float(positive)/(negative+positive)
				ent = entropy(qval)

			else:
				ent = 0
			prob = float(len(newdata))/len(tree.examples)
			totalgain = totalgain + float((ent*prob))
		return totalgain

def entropy(qval):

	if(qval == 0):
		return 0
	if(qval == 1):
		return 0
	log1 = math.log(qval,2)
	log2 = math.log(1-qval,2)
	ent = -(qval*log1 + (1-qval)*log2)
	return ent

def chisquared(passedtree,testattrib, tempAttribs):
		tree = passedtree
		attrib = testattrib
		attribdata = tempAttribs
		totaldelta = float(0)
		totalpos = 0
		totalneg = 0
		delta =0
		compare = 0
		print tree.examples
		print attrib
		df = len(attribdata[attrib])-1
		if(df ==1):
			compare = 2.706
		if(df ==2):
			compare = 4.605
		if(df==3):
			compare = 6.251
		for testex in tree.examples:
			if(testex.Wait == '"Yes"'):
				totalpos = totalpos+1
			else:
				totalneg = totalneg+1
		for val in attribdata[attrib]:
			newdata = []
			positive = 0
			negative = 0
			for ex in tree.examples:
				if(getattr(ex,attrib)== val):
					newdata.append(ex)
					if(getattr(ex,"Wait") == '"Yes"'):
						positive= positive+1
					else:
						negative= negative+1
			pos_hat = totalpos * ((positive+negative) / float(totalpos+totalneg))
			neg_hat = totalneg * ((positive+negative) / float(totalpos+totalneg))
			delta += (math.pow(positive-pos_hat,2)/pos_hat) + (math.pow(negative-neg_hat,2)/neg_hat)
			print 'delta=', delta
		print delta
		print compare
		return delta >= compare

def induction(passedtree):
	totalchecked = 0
	totalwait = 0
	totalnowait = 0
	tree = passedtree
	
	classcheck = [x[-1] for x in tree.examples]
	if(len(classcheck) -1 <=0):
		passedtree.isLeaf = 1
		return highestCount(tree)
	elif classcheck.count(classcheck[0]) == len(classcheck):
		passedtree.isLeaf = 1
		return classcheck[0]
	else:
		passedtree.isLeaf = 0
		subtrees = []
		bestAttr = findBestAttr(tree)
		tempAttribs = tree.attribs.copy()
		del(tree.attribs[bestAttr])
		returntree = {bestAttr:{}}
		for val in tempAttribs[bestAttr]:
			newdata = []
			for ex in tree.examples:
				if(getattr(ex,bestAttr)== val):
					newdata.append(ex)
			
			temptree = Tree(tree.attribs,newdata,0)
			subtrees.append(temptree)
			returntree[bestAttr][val] = induction(temptree)
		if all([sub.isLeaf ==1 for sub in subtrees]):
			print
			if not chisquared(tree, bestAttr, tempAttribs):
				print 'alsoran'
				return {bestAttr:highestCount(tree)}
		return returntree
	
	
tree = load()

induced = induction(tree)

print json.dumps(induced, indent = 4)