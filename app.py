import argparse
import sys
import time
import shutil
import psutil
from ply import lex
import os
from HTMLLexer import HTMLLexer
from flask import Flask, request, jsonify, render_template
#from HashTable import HashTable
#from nltk.stem import PorterStemmer
import logging

app = Flask(__name__)

image_path = os.path.join('static', 'LilFindEngine.png')
logging.basicConfig(level=logging.DEBUG)

word_based_search_btn_enabled = True
phrase_based_search_btn_enabled = False
radio_btn_checked = []

@app.route('/')
def root():
    print("this is for test")
    app.logger.debug(f"this is for test")
    return render_template("index.html", user_image = image_path)   


@app.route('/search', methods=['POST'])
def search():
    print("post called")
    query_words = []
    search_type = ''
    if request.method == 'POST':
        query_words = request.form['query']
        search_type = request.form['search_type']
        query_words = query_words.split()
        print(f"{query_words = }")
        print(f"{search_type = }")
        app.logger.debug(f"some_variable data: {query_words}")
    else:
        print("Else called")

    directory_path = "./output"

    if not query_words:
        return jsonify({"error": "Both 'query' and 'directory' fields are required."}), 400

    search_engine = retrieve()

    m = HTMLLexer()
    m.lexx()
    m.build()
    tokens = []
    query_string = ""
    if len(query_words)>1:
        for wordKey in query_words:
            print(f"in for loop {wordKey = }")
            m.lexer.input(wordKey)
            tok = m.lexer.token()
            if tok:
                tokens.append(tok.value)
                query_string = query_string + tok.value + " "
            else:
                tokens.append(wordKey)  # You may decide how to handle unknown tokens
    else:
        query_string = query_words[0]
        #print("in Else - Single word query")
        #print(f"{query_words[0] = }")
        m.lexer.input(query_words[0])
        #print("working")
        tok = m.lexer.token()
        #print("working")
        if tok:
            tokens.append(tok.value)
        else:
            tokens.append(query_words)  # You may decide how to handle unknown tokens

    # Assuming that read_data_from_files will return the search results instead of printing them
    search_results = search_engine.read_data_from_files(tokens, directory_path)
    print(f" result is = {search_results =} ")
    if search_results:
        result_text = f"Your result for query \"{query_string}\" is"

    # radio_btn_checked = {'word_based': 'word_based' == search_type, 'phrase_based': 'phrase_based' == search_type}
    
    # Returning the search results as JSON
    return render_template("index.html", content = search_results, user_image = image_path, search_result_text = result_text) 


class retrieve(object):
    # Used to merge results of two or more query terms

    def __init__(self):
        # self.keys = key
        self.file_size_dict = 0
        self.file_size_post = 0
        self.file_size_map = 0
        self.dict_length = 0
        self.post_length = 0
        self.map_length = 0
        self.dict_recordSize = 51
        self.post_recordSize = 13
        self.map_recordSize = 11

    def get_file_len(self, f1, f2, f3):
        self.file_size_dict = os.path.getsize(f1)
        self.file_size_post = os.path.getsize(f2)
        self.file_size_map = os.path.getsize(f3)
        dict_length = int(self.file_size_dict / self.dict_recordSize)  # 51 is record length of dictionary file
        post_length = int(self.file_size_post / self.post_recordSize)  # 25 is record length of dictionary file
        map_length = int(self.file_size_map / self.map_recordSize)  # 17 is record length of dictionary file
        return dict_length, post_length, map_length

    def dict_hash(self, key, size, f1):
        # Compute the initial hash value
        hash_val = -1
        for char in key:
            hash_val = (hash_val * 31 + ord(char)) % size
        # Initialize variables for collision handling
        original_hash = hash_val
        count = 0
        # Try to find the key
        while True:
            offset = hash_val * self.dict_recordSize
            f1.seek(offset)
            line = f1.read(self.dict_recordSize).strip()
            if line == "":
                print("Empty slot found. Key does not exist in collection. Hash Value:", hash_val)
                break
            elif line.startswith(key + " "):
                print("Key found. Hash Value:", hash_val)
                break
            else:
                print(f"Collision for {key}. Trying next slot. Count: {count}")
                hash_val = (hash_val + 1) % size
                count += 1
                if hash_val == original_hash:
                    print("Hash table is full or key does not exist. Cannot find key.")
                    break
        f1.seek(0)
        return hash_val

    def combineResult(self, postList, nextPost):
        finalPosts = []
        # Create dictionaries from the lists for easy lookup
        nextPosts_dict = {item[0]: item[1] for item in nextPost}
        postList_dict = {item[0]: item[1] for item in postList}
        for key in set(nextPosts_dict.keys()).union(postList_dict.keys()):
            if key in nextPosts_dict and key in postList_dict:
                finalPosts.append([key, '{:.3f}'.format(float(nextPosts_dict[key]) + float(postList_dict[key]))])
            elif key in nextPosts_dict:
                finalPosts.append([key, '{:.3f}'.format(float(nextPosts_dict[key]))])
            else:
                finalPosts.append([key, '{:.3f}'.format(float(postList_dict[key]))])
        return finalPosts

    def verify_directory(self, directory_path):
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print("Directory does not exist or is not a directory.")
            return False
        return True

    def get_file_paths(self, directory_path):
        files_to_read = ["dict.txt", "post.txt", "map.txt"]
        file_paths = [os.path.join(directory_path, filename) for filename in files_to_read]
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"{os.path.basename(file_path)} does not exist in the specified directory.")
                sys.exit(1)
        return file_paths

    def read_dictionary(self, f1, word):
        dict_line_no = self.dict_hash(word, self.dict_length, f1)  # Calculate hash value
        #print(f"Hash value of token {word} is {int(dict_line_no)}\n")
        if dict_line_no > self.dict_length:
            print("Token does not exist in collection! Enter new Token\n")
            return None
        #offset = dict_line_no * self.dict_recordSize
        return self.readFileLine(dict_line_no, self.dict_recordSize, f1)


    def process_postings(self, f2, f3, docCount, docStart):
        postings_list = []
        for i in range(docCount):
            posting = self.readFileLine((docStart + i), self.post_recordSize, f2)
            postings_list.append(posting)
        return postings_list


    def retrive_postings(self, query_words, f1, f2, f3):
        retrieved = []
        next_posts = []
        for word in query_words:
            dict_entry = self.read_dictionary(f1, word)
            if dict_entry and (dict_entry[0] == word):
                docCount, docStart = int(dict_entry[1]), int(dict_entry[2])
                postings_list = self.process_postings(f2, f3, docCount, docStart)
                postings_list = sorted(postings_list, key=lambda x: x[1], reverse=True)  # Sort for high to low tf*idf weights
                if next_posts:
                    postings_list = self.combineResult(next_posts, postings_list)
                if len(postings_list) > 11:
                    postings_list = postings_list[:10]  # Print the top 10 elements
                print("Top postings entries are: \n", postings_list, "\n")
                for w, wt in postings_list:
                    x = self.readFileLine(int(w), self.map_recordSize, f3)
                    print(f"one post from postings_list is {x[0]}")
                    retrieved.append(x[0])
                next_posts = postings_list
                postings_list = []
        return retrieved


    def read_data_from_files(self, query_words, directory_path):
        # Verify that the directory exists
        flag = self.verify_directory(directory_path)
        file_path = self.get_file_paths(directory_path)
        print(f"{file_path = }")
        if flag and file_path:
            with open(file_path[0], "r") as f1, open(file_path[1], "r") as f2, open(file_path[2], "r") as f3:
                self.dict_length, self.post_length, self.map_length = self.get_file_len(file_path[0], file_path[1],
                                                                                        file_path[2])
                retrieved = self.retrive_postings(query_words, f1, f2, f3)
                return self.formatData(retrieved, query_words)



    def formatData(self, retrieved, query_words):
        if len(retrieved) > 11:
            retrieved = retrieved[:10]
            return retrieved
            #print(f"Top 10 Documents that has word {query_words} are: ")
            print(retrieved, "\n")
        else:
            return retrieved
            #print(f"Documents that has word {query_words} are: ")
            print(retrieved, "\n")

    # read line from linenumber
    def readFileLine(self, dict_line_no, recordsize, fn):
        fn.seek(0)
        offset = dict_line_no * recordsize
        fn.seek(offset)
        x = fn.read(recordsize).strip()
        fn.seek(0)
        return x.split()

    def main(self):
        # Parse command line arguments
        # for elapsed time
        elapsed_time = []
        start = time.time()
        # for cpu time
        p = psutil.Process()
        cpu_time = []
        cpu_time.append(0.00)
        # Serve pages
        port = 8987
        delay_open_url(f'http://localhost:{port}/game.html', .1)

        parser = argparse.ArgumentParser(description="Read data from a specified directory")
        parser.add_argument("-q", nargs="+", help="Query words")
        parser.add_argument("-d", help="Directory path")
        args = parser.parse_args()
        if args.q is None or args.d is None:  # Check if both -q and -d options are provided
            parser.error("Both -q and -d options are required.")
        query_words = args.q  # Get the query words and directory path
        directory_path = args.d
        # Create an instance of the HTMLLexer class and use it
        m = HTMLLexer()
        m.lexx()
        m.build()
        tokens = []
        # parse the  all tokens from lexer
        for wordKey in query_words:
            m.lexer.input(wordKey)
            tok = m.lexer.token()
            if tok:
                tokens.append(tok.value)
                print(f"Entered token is: {tok.value}")
            else:
                print(f"Unknown or incorrect token entered! Try new Token")

        self.read_data_from_files(tokens, directory_path)  # Read files from the specified directory
        finish = time.time()
        print(f"Total time taken to process query is {'{:.6f}'.format(finish - start)} seconds")


if __name__ == "__main__":
    app.run(debug=True)
    print("Started")
    #rt = retrieve()
    #rt.main()  # Start execution
