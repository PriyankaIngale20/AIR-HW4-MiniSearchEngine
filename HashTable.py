class HashTable(object):
    def __init__(self, size):
        self.size = size
        self.table = [None] * size
        self.keys = ''
        self.values = ''

    def build(self, size):
        self.size = size

    def _hash(self, key):
        count = 0
        hash_val = -1
        #print(f"1. hash_val for {key} is {hash_val}")
        for char in key:
            hash_val = (hash_val * 31 + ord(char))
        hash_val = hash_val % self.size
        #print(f"2. hash_val for {key} is {hash_val}")
        while self.table[hash_val] is not None and self.table[hash_val][0] != key:   # Hash Value
            #print(f"3. collision for {key} times {count}")
            count+=1
            hash_val = (hash_val + 1) % self.size
            #print(f"4. Final hash value: {hash_val}")
        return hash_val

    def _data(self, index):
        return self.table[index]

    def insert(self, key, value):
        index = self._hash(key)
        if self.table[index] is None:
            self.table[index] = []
            self.table[index].append(key)
            self.table[index].append(value)
        else:
            oldKey = self.check_key(key)
            if oldKey == key:   # No collision
                pair = self.table[index]
                self.table[index] = []
                self.table[index].append(key)
                self.table[index].append(value)


    def append_to_value(self, key, value):
        index = self._hash(key)
        if self.keys[index] is not None:
            i = self.keys[index].index(key)
            self.values[index][i].append(value)
        return None

    def get(self, key):
        index = self._hash(key)
        # print("get value", self.table[index])
        if self.table[index] is None:
            return None
        else:
            pair = self.table[index]
            return pair[1]

    def append(self, key, value):
        index = self._hash(key)
        if self.table[index] is not None:
            for pair in self.table[index]:
                if pair[0] == key:
                    self.table[index].append([key, value])
                    return None
        return None

    def check_key(self, key):
        index = self._hash(key)
        pair = self.table[index]
        return pair[0]


    def ht_size(self):
        return self.size


    # def __iter__(self):
    #     for key, value in self.keys.items():
    #         yield key, self.values[key]

    def __iter__(self):
        self.index = 0
        self.current_bucket = 0
        return self

    def __next__(self):
        while self.current_bucket < self.size:
            if self.table[self.current_bucket] is not None:
                if self.index < len(self.table[self.current_bucket]):
                    pair = self.table[self.current_bucket][self.index]
                    self.index += 1
                    return pair
                else:
                    self.current_bucket += 1
                    self.index = 0
            else:
                self.current_bucket += 1
        raise StopIteration
