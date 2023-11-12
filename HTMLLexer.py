import HashTable
from ply import lex
import re
from HashTable import HashTable
import math
from nltk.stem import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
import os

class HTMLLexer(object):


    stop_words = [
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
        "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
        "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
        "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
        'the', "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
        "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
        "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
        "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "don",
        "should", "now", "www"
    ]


    tokens = (
        'STYLETAG',
        'SCRIPTTAG',
        'TAG',
        'TEXT_TAG',
        'FLOAT',
        'TIME',
        'COMMA_NUMBER',
        'HYPENATED',
        'ABBREVIATED',
        'EMAIL',
        'WORD',
        'WHITESPACE',
        'PUNCTUATION',
    )

    def __init__(self):
        self.ps = PorterStemmer()
        self.ps2 = SnowballStemmer("english")

    # rule for html style tags
    def t_STYLETAG(self, t):
        r'<style>[\s\S]*?<\/style>'
        pass

    # rule for html script tags
    def t_SCRIPTTAG(self, t):
        r'<script[^>]*>[\s\S]*?<\/script>'
        pass

    # rule for html tags
    def t_TAG(self, t):
        r'\s*<[^>]*>\s*'
        pass

    # When a HTML tag is in the middle of a word, such as a <b> tag
    def t_TEXT_TAG(self, t):
        r'(\w+<[^>]*>\w+)+'
        t.value = re.sub("<[^>]*>", "", t.value)
        t.value = str(t.value).lower()
        return t

    # for hypenated words
    def t_HYPENATED(self, t):
        r"(\w+-\w+)(-\w+)*"
        t.value = re.sub("-*", "", t.value)
        t.value = str(t.value).lower()
        return t

    # rule for floats, we ignore everything in the decimal place
    def t_FLOAT(self, t):
        r"[-+]?\d*\.\d+"
        t.value = str(float(t.value))
        return t

    # numbers which have commas in them, we just remove the comma
    def t_COMMA_NUMBER(self, t):
        r"(\d*,\d+)+"
        t.value = re.sub(",", ",", t.value)
        t.value = str(t.value)
        return t

    # numbers that have a colon in them
    def t_TIME(self, t):
        r"\w+:\w+"
        t.value = re.sub(":", ":", t.value)
        t.value = str(t.value)
        return t

    # This rule catches abbreviations as well as websites urls
    def t_ABBREVIATED(self, t):
        r"(\w+\.\w+)(\.\w+)*"
        t.value = str(t.value).lower()
        return t

    # This rule is to detect emails
    def t_EMAIL(self, t):
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
        t.value = str(t.value).lower()
        return t

    # # Rule to match consonant followed by e
    # def t_CONSONANT_E(self, t):
    #     r'\b[A-Za-z]*[^a][bcdfghjklmnpqrstvwxyz]{1,2}le\b'
    #     t.value = str(t.value).lower()
    #     return t

    def t_WORD(self, t):
        r'\w+'
        word = t.value.lower()
        if (self.stopwords.get(word) is None):
            if len(word) > 1:       # removing tokens < 1 character
                t.value = self.ps2.stem(word)
                t.value = str(t.value)
                #t.value = word
                return t
        pass

    def t_PUNCTUATION(self, t):
        r'[!"#$%&\'\(\)\*\+,-./:;<=>?@\[\]^_`{|}~\\/-]'
        pass

    def t_WHITESPACE(self, t):
        r'\s+'
        pass

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.stopwords = {}
        self.addTostopwords(self.stopwords)
        self.lexer = lex.lex(module=self, **kwargs)
        self.frequency = {}
        self.wordposition = {}
        self.total_tok = 0
        # initialize has table 3 times size of dictionary
        self.globalHash_table = HashTable(115597)   # 32327 is a prime number

    def lexx(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)


    # Add stopwords into Hashtable
    def addTostopwords (self, stopwords):
        for word in HTMLLexer.stop_words:
            self.stopwords[word] = True

    # after one file counts the frequency of words in the file, it calls this function to update the running total of token frequencies
    def updateFrequency(self, freq, docID, sum_log):
        for key in freq:
            if key in self.frequency:
                # increment document count if key already exist
                self.frequency[key][0] += 1
                self.frequency[key].append([docID, float('{:.3f}'.format(freq[key]/sum_log))])
            else:
                self.total_tok += 1
                # initialize document count to one for new key
                self.frequency[key] = [1]
                self.frequency[key].append([docID, float('{:.3f}'.format(freq[key]/sum_log))])


    def updateFrequency_2(self, freq, docID, sum_log):
        value = []
        for key in freq:
            if self.globalHash_table.get(key) is None:
                # initialize document count to one for new key
                value.append(1)
                value.append([docID, float('{:.3f}'.format(freq[key]/sum_log))])
                p = self.globalHash_table.insert(key, value)
                value = []
            else:
                # increment document count if key already exist
                if self.globalHash_table.check_key(key) == key:
                    #print("Not Collision!")
                    value = self.globalHash_table.get(key)
                    value[0] += 1
                    value.append([docID, float('{:.3f}'.format(freq[key]/sum_log))])
                    self.globalHash_table.insert(key, value)
                    value = []
                else :
                    print("Collision!")


    # opens inputFile, tokenizes it, then writes the tokens to outputFile. updates the frequency count of tokens
    def tokenizeFile(self, inputFile, docID):

        tokens = []

        # read the complete file in buffer and tokenize
        with open(inputFile, 'rb') as f:
            buffer = f.read().decode(errors='ignore')
            self.lexer.input(buffer)
            while True:
                tok = self.lexer.token()
                if not tok:
                    break
                else :
                    if len(tok.value)<39:
                        tokens.append(tok.value)

        # Count the frequency of tokens for this file - document hash table
        freq = {}
        for x in tokens:
            if (x in freq):
                freq[x] += 1
            else:
                freq[x] = 1


        # Calculate rtf for socument HT
        val = 0.0
        sum_log = 0.0
        for k, v in freq.items():
            val = 1+math.log10(v)
            val = float('{:.3f}'.format(val))
            sum_log += val
            freq[k] = val

        # update the global count of token frequencies
        self.updateFrequency(freq, docID, sum_log)
        self.updateFrequency_2(freq, docID, sum_log)

    # create the files with tokens in an order with hash table
    def finish2(self, N):
        with open("output/dict.txt", "w") as f1, open("output/post.txt", "w") as f2:
            count = 0
            start = 0
            line = 0
            whitespace = str(" ")
            data = []
            print("Total tokens", self.total_tok)
            #print("Hash Value for token 7634134 is ", self.globalHash_table._hash(str(7634134)), self.globalHash_table.get(str(7634134)))
            for i in range(self.globalHash_table.ht_size()):
                if self.globalHash_table._data(i) is not None:
                    line+=1
                    count += 1
                    data = self.globalHash_table._data(i)
                    word = data[0]
                    postings = data[1][1:]
                    if len(postings) > 0:
                        f1.write("%-38s %-4s %-6s\n" % (data[0], data[1][0], start))
                        start = start + data[1][0]
                        idf = 1+math.log10(N/data[1][0])
                        idf = float('{:.3f}'.format(idf))
                        for i in postings:
                            f2.write("%-5s %-6s\n" %(i[0], float('{:.3f}'.format(i[1]*idf))))
                else:
                    line+=1
                    if line != self.globalHash_table.ht_size():
                        f1.write("%-50s\n" % whitespace)
                    else:
                        f1.write("%-51s" % whitespace)
        print("Total token count: ", count)