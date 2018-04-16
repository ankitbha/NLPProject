import sys
from collections import defaultdict
import numpy

import re

from nltk.tokenize import TweetTokenizer

# def normalize_word(word):
#     temp = word
#     while True:
#         w = re.sub(r"([a-zA-Z])\1\1", r"\1\1", temp)
#         if (w == temp):
#             break
#         else:
#             temp = w
# 	return w

def normalize_word(word): #removing repitive letters like "It tastes 'soooo' awesome"
	temp = word
	r1 = r"([a-zA-Z])\1\1"
	r2 = r"\1\1"
	w = re.sub(r1,r2,temp)
	while (w!=temp):
		w = re.sub(r1,r2,temp)
		temp = w	
	return w


def load_unicode_mapping(path): #dictionary with emoticon and its meaning. 
	emoji_dict = defaultdict()
	with open(path, 'r') as file:
		lines = file.readlines()
		for line in lines:
			tokens = line.strip() 
			tokens = tokens.split('\t') 
			emoji_dict[tokens[0]] = tokens[1]
	return emoji_dict		

def InitializeWords(word_file_path):
	word_dictionary = defaultdict()

	with open(path, 'r') as file:
		lines = file.readlines()
		for line in lines:
			tokens = line.strip()
			tokens = tokens.split('\t')
			word_dictionary[tokens[0].lower()] = tokens[1]

	alphabet_list = "bcdefghjklmnopqrstuvwxyz" 

	for alphabet in alphabet_list:
		if alphabet in word_dictionary:
			del word_dictionary[alphabet]

	return word_dictionary

def load_split_word(split_word_file_path):
	hashtagged_word_split_dict=defaultdict()

	with open(split_word_file_path,'r') as file:
		lines = file.splitlines()
		for line in lines:
			tokens = line.lower()
			tokens = tokens.strip()
			tokens = tokens.split('\t')
			if(length(tokens)!=1):
				hashtagged_word_split_dict[tokens[0]] = tokens[1]
	
	return hashtagged_word_split_dict						

def load_abbreviation(path = './abbreviations.txt'):
	abbreviation_dict = defaultdict()
	with open(path) as file:
		lines = file.readlines()
		for line in lines:
			tokens = line.lower()
			tokens = tokens.strip()
			tokens = tokens.split('\t')
			abbreviation_dict[tokens[0]] = tokens[1] 
	return abbreviation_dict

#didnot include dumpfile
def split_hashtags(term, wordlist, split_word_list):
	if(len(term.strip())==1):
		n = ['']
		return n

	if(split_word_list!=None and term.lower() in split_word_list):
		n = split_word_list.get(term.lower())
		return n.split(' ')

	if(term.startswith('#')):
		term = term[1:]

	if(wordlist!=None and term.lower() in wordlist):
		n = [term.lower()]
		return n

	words=[]
	term = re.sub(r'([0-9]+)', r' \1', term)
	term = re.sub(r'(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|0th)', r'\1 ', term)
	words = term.strip().split(' ')	

	words = [str(s) for s in words]

	return words

def filter_text(text, word_list, split_word_list, emoji_dict, abbreviation_dict, normalize_text=False,split_hastag=False,ignore_profiles=False,replace_emoji=True):
	filtered_text=[]

	filter_list = ['/', '-', '=', '+', '…', '\\', '(', ')', '&', ':']

	for t in text:
		word_tokens = None

		#discarding symbols
		# if(str(t).lower() in filter_list):
		# 	continue

		if(ignore_profiles and str(t).startswith('@')):
			continue

		if(str(t).startswith('http')):
			continue

		if(str(t).lower()=="#sarcasm"):
			continue

		if(replace_emoji): #replacing emoji with its unicode description
			if(t in emoji_dict):
				t=emoji_dict.get(t).split('_')
				filtered_text.extend(t)
				continue

		if(split_hastag and str(t).startswith("#")):
			splits = split_hashtags(t,word_list,split_word_list)
			if(splits !=None):
				filtered_text.extend([s for s in splits if (not filtered_text.__contains__(s))])
				continue

		if(normalize_text):
			t = normalize_word(t)
		
		if (t in abbreviation_dict):
			tokens = abbreviation_dict.get(t).split(' ')
			filtered_text.extend(tokens)
			continue

		filtered_text.append(t)

	return filtered_text

def parsedata(lines, word_list, split_word_list, emoji_dict, abbreviation_dict, normalize_text=False, split_hashtag=False, ignore_profiles=False, lowercase=False, replace_emoji=True, n_grams=None, at_character=False):
	
	data = []
	
	for i, line in enumerate(lines):
		if (i % 100 == 0):
			print(str(i) + '...', end='', flush=True)
		

		# convert the line to lowercase
		if (lowercase):
			line = line.lower()
			# split into token
		token = line.split('\t')

        # ID
		id = token[0]

        # label
		label = int(token[1].strip())
		# tweet text
		target_text = TweetTokenizer().tokenize(token[2].strip())
		# if (at_character):
		# 	target_text = [c for c in token[2].strip()]

		# if (n_grams != None):
		# 	n_grams_list = list(create_ngram_set(target_text, ngram_value=n_grams))
		# 	target_text.extend(['_'.join(n) for n in n_grams_list])

		# filter text
		target_text = filter_text(target_text, word_list, split_word_list, emoji_dict, abbreviation_dict,normalize_text,split_hashtag,ignore_profiles, replace_emoji=replace_emoji)

        # awc dimensions
		dimensions = []
		if (len(token) > 3 and token[3].strip() != 'NA'):
			dimensions = [dimension.split('@@')[1] for dimension in token[3].strip().split('|')]

		# context tweet
		context = []
		if (len(token) > 4):
			if (token[4] != 'NA'):
				context = TweetTokenizer().tokenize(token[4].strip())
				context = filter_text(context, word_list, split_word_list, emoji_dict, abbreviation_dict,normalize_text,split_hashtag,ignore_profiles, replace_emoji=replace_emoji)

		# author
		author = 'NA'
		if (len(token) > 5):
			author = token[5]

		if (len(target_text) != 0):
		# print((label, target_text, dimensions, context, author))
			data.append((id, label, target_text, dimensions, context, author))

	return data

def build_vocab(data, without_dimension=True, ignore_context=False, min_freq=0):
	vocabulary = defaultdict(int)
	vocabulary_frequency = defaultdict(int)
	
	total_no_words = 1

	if(without_dimension==False):
		for i in range(1,101):
			vocabulary_frequency[str(i)] = 0

	for sentence_number, token in enumerate(data):
		for word in token[2]:
			if word not in vocabulary_frequency:
				vocabulary_frequency[word] = 0
			vocabulary_frequency[word] = vocabulary_frequency.get(word) + 1

		if(without_dimension == False):
			for word in token[3]:
				vocabulary_frequency[word] = vocabulary_frequency.get(word) + 1

		if(ignore_context == False):
			for word in token[4]:
				if word not in vocabulary:
					vocabulary_frequency[word] = 0
				vocabulary_frequency[word] = vocabulary_frequency.get(word) + 1
	
	for a, b in vocabulary_frequency.items():
		if(b >=min_freq):
			vocabulary[a] = total_no_words
			total_no_words = total_no_words + 1

	return vocabulary		

def write_vocab(path,vocabulary):
	with open(path,'w') as f:
		for key, value in vocabulary.items():
			f.write(str(key) +"\t" +str(value)+ "\n")


def loaddata(filename, word_file_path, split_word_path, emoji_file_path, normalize_text=False, split_hashtag=False,ignore_profiles=False,lowercase=True, replace_emoji=True, n_grams=None, at_character=False):
	word_list = None
	emoji_dict = None

	split_word_list = load_split_word(split_word_path)

	if (split_hashtag):
		word_list = InitializeWords(word_file_path)

	if (replace_emoji):
		emoji_dict = load_unicode_mapping(emoji_file_path)

	abbreviation_dict = load_abbreviation()

	lines = open(filename, 'r').readlines()

	data = parsedata(lines, word_list, split_word_list, emoji_dict, abbreviation_dict, normalize_text=normalize_text,split_hashtag=split_hashtag,ignore_profiles=ignore_profiles,lowercase=lowercase,replace_emoji=replace_emoji,n_grams=n_grams, at_character=at_character)
	
	return data



def vectorize_word_dimension(data, vocab, drop_dimension_index=None):
	X=[]
	Y=[]
	known_words=[]
	unknown_words=[]

	for id,label,tokenlist,dimensions,context,author in data:
		vec=[]
		context_vec=[]
		for token in tokenlist:
			if(token in vocab):
				vec.append(vocab[words])
			else:
				vec.append(0)

		X.append(vec)
		Y.append(label)

	return numpy.asarray(X), numpy.asarray(Y) 	


def pad_sequence_1d(sequences,flag_pad='pre'):
	
	X=[vectors for vectors in sequences]	
	
	maxlen = max([len(v) for v in X])
	# X=numpy.zeros(maxlen)
	Y=[]

	for i,v in enumerate(X):
		temp_len = len(v)
		temp=[]
		if(temp_len < maxlen):
			t = maxlen - temp_len
			if(flag_pad=='pre'):
				for i in range(0,t):
					temp.append(0)
				temp.extend(v)
			elif(flag_pad == 'post'):
				temp = v
				for i in range(0,t):
					temp.extend([0])	
		else:
			temp = v		
		Y.append(temp)
	return Y
		



