import random
"""
A loop function to seperate the letters into individual items in a list or join list into string
"""
def function1(entry):
    if(isinstance(entry, str)):
        step_1_list = []
        for l in entry:
            step_1_list.append(l)
        return step_1_list
    elif(isinstance(entry, list)):
        the_start = ""
        for s in entry:
            the_start = the_start + f"{s}"
        return the_start

"""
In this function I can convert the items into their ASCII codes in a new list through the built 
python ord() function and reverse it with the chr() function.
"""
def function2(entry):
    if(isinstance(entry, list)):
        step_2_list = []
        if(isinstance(entry[0], str)):
            for s in entry:
                step_2_list.append(ord(s))
            return step_2_list
        elif(isinstance(entry[0], int)):
            for s in entry:
                step_2_list.append(chr(s))
            return step_2_list

"""
In this function I check if the list has int entries or string entries as int will indicate it is
the ASCII list and str indicates the list entries are binary as the built in bin() function for python
converts the int into a str with 0b at the start.  There is no built in function for converting back so
I needed to implement a conversion back, in this function
"""
def function3(entry):
    if(isinstance(entry, list)):
        step_3_list = []
        if(isinstance(entry[0], int)):
            for s in entry:
                step_3_list.append(bin(s))
            return step_3_list
        elif(isinstance(entry[0], str)):
            """Removes the 0b added to the binary string then reads the string from the back digit
            and adds it to a total converted number to add to the list"""
            for s in entry:
                no_0b = s.replace("0b", "")
                converted = 0
                i = len(no_0b)-1
                while(i >= 0):
                    converted += (int(no_0b[i]) * pow(2, len(no_0b)-(i+1)))
                    i -= 1
                step_3_list.append(converted)
        elif(isinstance(entry[0], list)):
            for s in entry:
                i = len(s)-1
                converted = 0
                while(i >= 0):
                    converted += (s[i] * pow(2, len(s)-(i+1)))
                    i -= 1
                step_3_list.append(converted)
            return step_3_list


"""A loop to print the list into a formated line of entries to check the work."""
def print_list_assignment(check_list):
    if(isinstance(check_list[0], str)):
        if(check_list[0].find("0b") == -1):
            to_show = "["
            for c in check_list:
               to_show = to_show + f"'{c}', "
            to_show = to_show + "]"
            print(to_show.replace(", ]", "]"))
        else:
            to_show = "["
            for c in check_list:
                to_show = to_show + f"{c.replace("0b", "")}, "
            to_show = to_show + "]"
            print(to_show.replace(", ]", "]"))
    elif(isinstance(check_list[0], int)):
        to_show = "["
        for c in check_list:
            to_show = to_show + f"{c}, "
        to_show = to_show + "]"
        print(to_show.replace(", ]", "]"))

prime_list = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181,
             191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277,
             281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383,
             389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487,
             491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
             607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709,
             719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827,
             829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947,
             953, 967, 971, 977, 983, 991, 997]


"""Key generation function, creates a list with the public key pair first and private
key pair second.  Chooses the public key randomly from the list of prime numbers between 100-1000"""
def key_gen(p, q):
    result = []
    prod_n = p * q
    euler_t = (p - 1) * (q - 1)
    pub_k = prime_list[random.randint(0, len(prime_list)-1)]
    public_k = [pub_k, prod_n]
    result.append(public_k)

    pr_k = 0
    inverse_check = 0
    while (inverse_check != 1):
        if (pub_k * pr_k) % euler_t == 1:
            inverse_check = 1
            break
        else:
            pr_k += 1
    private_k = [pr_k, prod_n]
    result.append(private_k)
    return result

"""function to encrypt and decript with the RSA method"""
def rsa(value, key):
    if value < key[1]:
        return (value**key[0]) % key[1]



"""Code to test the functions meet assignment criteria"""
start = "Thomas Neidhardt"
print(start)
"""This is the code just to print the values as they are converted"""
step_i = function1(start)
step_ii = function2(step_i)
print_list_assignment(step_ii)

"""I print the values used here for the primes and keys to be able to check the math of the code"""
p1 =  prime_list[random.randint(0, len(prime_list))-1]
p2 =  prime_list[random.randint(0, len(prime_list))-1]
print("The p = " + str(p1) + " and q = " + str(p2))
test_keys = key_gen(p1, p2)
print("The public key pair is public key = " + str(test_keys[0][0]) + ", n = "+str(test_keys[0][1]))
print("The private key pair is private key = " + str(test_keys[1][0]) + ", n = " + str(test_keys[1][1]))

"""I also print the encrypted int values output by the RSA before converting it to the
string characters here"""
name_enc = []
for i in step_ii:
    name_enc.append(rsa(i, test_keys[0]))
encr_char = function1(name_enc)
encr_char = "encrypted int values of characters ["
for i in name_enc:
    encr_char = encr_char + str(i) + ", "
encr_char = encr_char + "]"
encr_char = encr_char.replace(", ]", "]")
print(encr_char)
enc_str = function1(function2(name_enc))
print("encrypted string "+enc_str)


"""This code prints the decrypted int values and then converts it back into a string"""
name_dec = []
for i in name_enc:
    name_dec.append(rsa(i, test_keys[1]))
decr_char = "decrypted values are ["
for i in name_dec:
    decr_char = decr_char + str(i) + ", "
decr_char = decr_char + "]"
decr_char = decr_char.replace(", ]", "]")
print(decr_char)
dec_str = "Decrypted string: " + function1(function2(name_dec))
print(dec_str)

"""Code to print examples needed for assignment with a sentence"""
sentence = "What can be done?"
sentence_list = function2(function1(sentence))
enc_sentence = []
for i in sentence_list:
    enc_sentence.append(rsa(i, test_keys[0]))
enc_sentence_str = function1(function2(enc_sentence))
print("Encrypted sentence string: " + enc_sentence_str)
dec_sentence = []
for i in enc_sentence:
    dec_sentence.append(rsa(i, test_keys[1]))
dec_sentence_str = function1(function2(dec_sentence))
print("Decrypted sentence string: "+ dec_sentence_str)