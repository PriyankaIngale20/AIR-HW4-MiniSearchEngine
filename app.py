import argparse
import sys
import time
import shutil
import psutil
from ply import lex
import os
from HTMLLexer import HTMLLexer
from flask import Flask, request, jsonify, render_template, flash
# from HashTable import HashTable
# from nltk.stem import PorterStemmer
import logging

app = Flask(__name__)
app.secret_key = "asdfghyj_12334456"

image_path = os.path.join('static', 'LilFindEngine.png')
logging.basicConfig(level=logging.DEBUG)


@app.route('/')
def root():
    print("this is for test")
    app.logger.debug(f"this is for test")
    flash(
        "Prepend your query with 'word' or 'phrase' for word based or phrase based search respectively, e.g. 'word cat' or 'phrase memory card'")
    return render_template("index.html", user_image=image_path, search_result_text="")


@app.route('/search', methods=['POST'])
def search():
    # print("post called")
    query_words = []
    search_results = []
    query = ""
    result_text = ""
    if request.method == 'POST':
        query = request.form['query']
        query_words = query.split()

    if not query_words:
        flash("Error: query field is required")
        # return jsonify({"error": "'query' field is required."}), 400
    else:
        q_type = query_words[0]
        print(q_type)

        if (q_type == 'word') or (q_type == 'phrase'):
            query_words = query_words[1:]
            directory_path = "./output"
            # Assuming that read_data_from_files will return the search results instead of printing them
            query_string, search_results = process_query_words(q_type, query_words, directory_path)
            print(f" result is = {search_results =} ")
            if search_results:
                result_text = f"Your result for query \"{query}\" is"
            else:
                result_text = f" No result found for query \"{query}\""
                print(f" No result found ")
            #return render_template("index.html", user_image=image_path, search_result_text="")
        else:
            flash("Error: Incorrect prepend")
    # Returning the search results as JSON
    return render_template("index.html", content=search_results, user_image=image_path, search_result_text=result_text)


def process_query_words(q_type, query_words, directory_path):
    # Initialize HTML lexer and search engine
    m = HTMLLexer()
    m.lexx()
    m.build()
    search_engine = retrieve()
    # Tokenize and process query string
    tokens = []
    query_string = ""
    for wordKey in query_words:
        m.lexer.input(wordKey)
        tok = m.lexer.token()
        if tok:  # Handle valid tokens
            tokens.append(tok.value)
            query_string += tok.value + " "
        # Handle unknown tokens
        else:
            tokens.append(wordKey)
    return query_string, search_engine.read_data_from_files(q_type, tokens, directory_path)


class retrieve(object):
    # Used to merge results of two or more query terms

    def __init__(self):
        # self.keys = key
        self.file_size_dict = 0
        self.file_size_post = 0
        self.file_size_map = 0
        self.file_size_loc = 0
        self.dict_length = 0
        self.post_length = 0
        self.map_length = 0
        self.loc_length = 0
        self.dict_recordSize = 51
        self.post_recordSize = 25
        self.map_recordSize = 17
        self.loc_recordSize = 6

    def get_file_len(self, f1, f2, f3, f4):
        self.file_size_dict = os.path.getsize(f1)
        self.file_size_post = os.path.getsize(f2)
        self.file_size_map = os.path.getsize(f3)
        self.file_size_loc = os.path.getsize(f4)
        dict_length = int(self.file_size_dict / self.dict_recordSize)  # 51 is record length of dictionary file
        post_length = int(self.file_size_post / self.post_recordSize)  # 25 is record length of postings file
        map_length = int(self.file_size_map / self.map_recordSize)  # 17 is record length of map file
        loc_length = int(self.file_size_loc / self.loc_recordSize)  # 7 is record length of location file
        return dict_length, post_length, map_length, loc_length

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
                flash("Empty slot found. Key does not exist in collection")
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

    def wordResult(self, postList, nextPost):
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

    def phraseResult(self, f4, postList, nextPost):
        finalPosts = []
        nextPosts_dict2 = {item[0]: [item[1], item[2], item[3]] for item in nextPost}
        postList_dict2 = {item[0]: [item[1], item[2], item[3]] for item in postList}
        index1 = []
        index2 = []
        for key in set(nextPosts_dict2.keys()).union(postList_dict2.keys()):
            if key in nextPosts_dict2 and key in postList_dict2:  # for same document ID
                for i in range(int(postList_dict2[key][1])):
                    index = self.readFileLine(int(postList_dict2[key][2]) + i, self.loc_recordSize, f4)
                    index1.append(int(index[0]))
                for i in range(int(nextPosts_dict2[key][1])):
                    index = self.readFileLine(int(nextPosts_dict2[key][2]) + i, self.loc_recordSize, f4)
                    index2.append(int(index[0]))
                for value1 in index1:
                    if value1 + 1 in index2:
                        finalPosts.append(
                            [key, '{:.3f}'.format(float(nextPosts_dict2[key][0]) + float(postList_dict2[key][0]))])
            #print(f"{finalPosts[:10] = }")
        return finalPosts

    def verify_directory(self, directory_path):
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print("Directory does not exist or is not a directory.")
            return False
        return True

    def get_file_paths(self, directory_path):
        files_to_read = ["dict.txt", "post.txt", "map.txt", "loc.txt"]
        file_paths = [os.path.join(directory_path, filename) for filename in files_to_read]
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"{os.path.basename(file_path)} does not exist in the specified directory.")
                sys.exit(1)
        return file_paths

    def read_dictionary(self, f1, word):
        dict_line_no = self.dict_hash(word, self.dict_length, f1)  # Calculate hash value
        # print(f"Hash value of token {word} is {int(dict_line_no)}\n")
        if dict_line_no > self.dict_length:
            print("Token does not exist in collection! Enter new Token\n")
            return None
        # offset = dict_line_no * self.dict_recordSize
        return self.readFileLine(dict_line_no, self.dict_recordSize, f1)

    def process_postings(self, f2, f3, f4, docCount, docStart):
        postings_list = []
        for i in range(docCount):
            posting = self.readFileLine((docStart + i), self.post_recordSize, f2)
            postings_list.append(posting)
        return postings_list

    def retrive_postings(self, q_type, query_words, f1, f2, f3, f4):
        retrieved = []
        next_posts = []
        postings_list = []

        for word in query_words:
            dict_entry = self.read_dictionary(f1, word)
            if dict_entry and (dict_entry[0] == word):
                print(f"dic entry: {dict_entry}")
                docCount, docStart = int(dict_entry[1]), int(dict_entry[2])
                postings_list = self.process_postings(f2, f3, f4, docCount, docStart)
                postings_list = sorted(postings_list, key=lambda x: x[1],
                                       reverse=True)  # Sort for high to low tf*idf weights
                if next_posts and len(query_words) > 1:
                    # Word Search
                    if q_type== 'word':
                        postings_list = self.wordResult(next_posts, postings_list)
                        postings_list = sorted(postings_list, key=lambda x: x[1], reverse=True)
                        # print(f"After considering 2nd word {postings_list = } \n")
                    elif q_type== 'phrase':
                        # Phrase Search
                        postings_list = self.phraseResult(f4, next_posts, postings_list)
                        postings_list = sorted(postings_list, key=lambda x: x[1], reverse=True)
                        # print(f"After considering 2nd word {postings_list_phrase = } \n")
                    else:
                        return retrieved
                else:
                    postings_list = postings_list[:10]

                next_posts = postings_list

        if postings_list:
            for posting in postings_list:
                w, wt, *_ = posting[:2]
                # print(f"{w= }")
                x = self.readFileLine(int(w), self.map_recordSize, f3)
                # print(f"one post from postings_list is {x}")
                if x[0] not in retrieved:
                    retrieved.append(x[0])

        return retrieved

    def read_data_from_files(self, q_type, query_words, directory_path):
        # Verify that the directory exists
        flag = self.verify_directory(directory_path)
        file_path = self.get_file_paths(directory_path)
        print(f"{file_path = }")
        if flag and file_path:
            with open(file_path[0], "r") as f1, open(file_path[1], "r") as f2, open(file_path[2], "r") as f3, open(
                    file_path[3], "r") as f4:
                self.dict_length, self.post_length, self.map_length, self.loc_length = self.get_file_len(file_path[0],
                                                                                                         file_path[1],
                                                                                                         file_path[2],
                                                                                                         file_path[3])
                retrieved = self.retrive_postings(q_type, query_words, f1, f2, f3, f4)
                return self.formatData(retrieved, query_words)

    def formatData(self, retrieved, query_words):
        if len(retrieved) > 11:
            retrieved = retrieved[:10]
            return retrieved
        else:
            return retrieved

    # read line from linenumber
    def readFileLine(self, dict_line_no, recordsize, fn):
        fn.seek(0)
        offset = dict_line_no * recordsize
        fn.seek(offset)
        x = fn.read(recordsize).strip()
        fn.seek(0)
        return x.split()


if __name__ == "__main__":
    app.run(debug=True)
    print("Started")
    # rt = retrieve()
    # rt.main()  # Start execution
